# -*- coding: utf-8 -*-
"""loop.py - trade loop for one robot."""
from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from broker import portfolio as pf
from broker import orders as od
from db import repo
from engine.risk import RiskManager
from strategies.sma import SMAStrategy
from strategies.grid import GridStrategy
from notify import desktop as _nt
from engine.watchdog import Watchdog
from engine import reconcile as _rec

log = logging.getLogger("engine.loop")

INTERVAL_MAP = {
    "H1": "CANDLE_INTERVAL_HOUR",
    "D1": "CANDLE_INTERVAL_DAY",
    "M1": "CANDLE_INTERVAL_1_MIN",
    "M5": "CANDLE_INTERVAL_5_MIN",
}


def _make_strategy(name, params):
    if name == "sma":
        return SMAStrategy(params)
    if name == "grid":
        return GridStrategy(params)
    raise ValueError("unknown strategy: " + name)


class RobotLoop:
    def __init__(self, cfg, robot_cfg, client):
        self.cfg = cfg
        self.r = robot_cfg
        self.c = client
        self.rid = int(robot_cfg.get("id", 0))
        self.figi = robot_cfg.get("figi", "")
        self.ticker = robot_cfg.get("ticker", "")
        self.account_id = robot_cfg.get("account_id", "")
        self.mode = robot_cfg.get("mode", "sandbox")
        params = robot_cfg.get("params", {}) or {}
        self.params = params
        self.strategy = _make_strategy(robot_cfg.get("strategy", "sma"), params)
        self.risk = RiskManager(params)
        self.check_interval = int(params.get("check_interval", 60))
        self.days_back = int(params.get("days_back", 330))
        self.timeframe = params.get("timeframe", "D1")
        self.stop_loss = float(params.get("stop_loss", 0.05))
        self.tp = float(params.get("take_profit", 0.15))
        self.trail = float(params.get("trail_pct", 0.0))
        self.stop_order_id = None
        self.peak_px = 0.0
        self.armed = False
        self._tick_count = 0
        self._reconcile_every = int(params.get("reconcile_every", 20))
        self.lot = 1
        self._stop = False
        self._pending_order_id = None
        self._pending_ticks = 0
        self._pending_info = None
        try:
            _st = repo.load_state(self.rid)
            if _st:
                self.stop_order_id = _st.get("stop_order_id") or None
        except Exception:
            pass

    async def get_candles(self):
        to_dt = datetime.now(timezone.utc)
        fr_dt = to_dt - timedelta(days=self.days_back)
        interval = INTERVAL_MAP.get(self.timeframe, "CANDLE_INTERVAL_DAY")
        return await pf.get_candles(
            self.c, self.figi,
            fr_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            to_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            interval,
        )

    async def get_position(self):
        p = await pf.get_portfolio(self.c, self.account_id)
        self._cash = p.cash_rub
        for pos in p.positions:
            if pos.figi == self.figi:
                return pos.qty, pos.avg_price, pos.current_price
        return 0.0, 0.0, 0.0

    def stop(self):
        self._stop = True

    async def _sleep(self, seconds):
        _end = asyncio.get_event_loop().time() + float(seconds)
        while not self._stop:
            _left = _end - asyncio.get_event_loop().time()
            if _left <= 0:
                break
            await asyncio.sleep(min(1.0, _left))

    def _floor_lot(self, qty, lot):
        n = int(qty)
        return float(n - (n - int(n / lot) * lot))

    async def _check_pending(self):
        if not self._pending_order_id:
            return "NONE"
        try:
            r = await od.get_order_state(self.c, self.account_id, self._pending_order_id)
            st = (r.get("executionReportStatus") or "").upper()
            log.info("[robot-%s] pending %s = %s", self.rid, self._pending_order_id, st)
            if "FILL" in st:
                _info = self._pending_info or {}
                self._pending_order_id = None
                self._pending_info = None
                if _info:
                    try:
                        rec = dict(_info)
                        rec["ts"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        rec["status"] = st
                        repo.add_trade(rec)
                        _nt.notify_trade(rec)
                        log.info("[robot-%s] limit FILL %s x %s = %s", self.rid, self.ticker, _info.get("qty"), _info.get("price"))
                    except Exception as _e:
                        log.error("[robot-%s] fill trade save: %s", self.rid, str(_e)[:100])
                return "FILL"
            if "REJECT" in st or "CANCEL" in st:
                self._pending_order_id = None
                return "DEAD"
            return "WAIT"
        except Exception as e:
            log.warning("[robot-%s] pending check failed: %s", self.rid, str(e)[:100])
            self._pending_order_id = None
            return "DEAD"

    async def do_buy(self, qty, price):
        _p = await self._check_pending()
        if _p == "WAIT":
            log.info("[robot-%s] pending %s still open, skip", self.rid, self._pending_order_id)
            return False
        if _p == "FILL":
            log.info("[robot-%s] pending FILLed, will place stop next tick", self.rid)
            return True
        _lot = max(1, int(getattr(self, "lot", 1) or 1))
        qty = self._floor_lot(float(qty), _lot)
        if qty <= 0:
            log.warning("[robot-%s] qty below lot, skip buy", self.rid)
            return False
        try:
            _ot = "ORDER_TYPE_LIMIT" if self.params.get("use_limit", False) else "ORDER_TYPE_MARKET"
            _off = float(self.params.get("limit_offset", 0.002))
            _px = round(price * (1 - _off), 2) if _ot == "ORDER_TYPE_LIMIT" else None
            res = await od.post_order(self.c, self.account_id, self.figi, qty, "ORDER_DIRECTION_BUY", order_type=_ot, price=_px)
            _st = (res.status or "").upper()
            if _ot == "ORDER_TYPE_LIMIT" and "FILL" not in _st:
                self._pending_order_id = res.order_id
                self._pending_info = {"robot_id": self.rid, "kind": "BUY", "ticker": self.ticker, "figi": self.figi, "qty": qty, "price": _px or price, "total": qty * (_px or price), "commission": 0.0, "order_id": res.order_id, "mode": self.mode, "strategy": self.strategy.name}
                log.info("[robot-%s] limit %s placed (status=%s), waiting next tick", self.rid, res.order_id, _st)
                return False
            rec = {
                "robot_id": self.rid,
                "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "kind": "BUY",
                "ticker": self.ticker,
                "figi": self.figi,
                "qty": qty,
                "price": price,
                "total": qty * price,
                "commission": res.commission,
                "order_id": res.order_id,
                "status": res.status,
                "mode": self.mode,
                "strategy": self.strategy.name,
            }
            repo.add_trade(rec)
            _nt.notify_trade(rec)
            try:
                repo.save_state(self.rid, last_ts=rec["ts"])
            except Exception:
                pass
            self._last_buy_err = None
            log.info("[robot-%s] BUY %s x %s = %s", self.rid, self.ticker, qty, round(qty * price, 2))
            return True
        except Exception as e:
            _emsg = str(e)[:200]
            if _emsg == getattr(self, "_last_buy_err", None):
                return False
            self._last_buy_err = _emsg
            log.error("[robot-%s] BUY FAILED: %s", self.rid, _emsg)
            _nt.notify_error(self.rid, "BUY FAILED: " + str(e)[:100])
            return False

    async def do_sell(self, qty, price, reason="signal"):
        try:
            if self.stop_order_id:
                await od.cancel_stop_order(self.c, self.account_id, self.stop_order_id)
                self.stop_order_id = None
            _ot = "ORDER_TYPE_LIMIT" if self.params.get("use_limit", False) else "ORDER_TYPE_MARKET"
            _off = float(self.params.get("limit_offset", 0.002))
            _px = round(price * (1 + _off), 2) if _ot == "ORDER_TYPE_LIMIT" else None
            res = await od.post_order(self.c, self.account_id, self.figi, qty, "ORDER_DIRECTION_SELL", order_type=_ot, price=_px)
            rec = {
                "robot_id": self.rid,
                "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "kind": "SELL",
                "ticker": self.ticker,
                "figi": self.figi,
                "qty": qty,
                "price": price,
                "total": qty * price,
                "commission": res.commission,
                "order_id": res.order_id,
                "status": res.status,
                "mode": self.mode,
                "strategy": self.strategy.name,
            }
            repo.add_trade(rec)
            _nt.notify_trade(rec)
            try:
                repo.save_state(self.rid, last_ts=rec["ts"])
            except Exception:
                pass
            log.info("[robot-%s] SELL %s x %s = %s (%s)", self.rid, self.ticker, qty, round(qty * price, 2), reason)
            self.peak_px = 0.0
            self.armed = False
            try:
                repo.save_state(self.rid, stop_order_id="")
            except Exception:
                pass
            return True
        except Exception as e:
            log.error("[robot-%s] SELL FAILED: %s", self.rid, str(e)[:200])
            _nt.notify_error(self.rid, "SELL FAILED: " + str(e)[:100])
            return False

    async def tick(self):
        self._tick_count += 1
        try:
            repo.save_state(self.rid, running=1, last_ts=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        except Exception:
            pass
        candles = await self.get_candles()
        if len(candles) < 30:
            log.warning("[robot-%s] not enough candles: %s", self.rid, len(candles))
            return
        qty, avg, cur = await self.get_position()
        if cur <= 0:
            cur = candles[-1].close
        # periodic reconcile
        if qty > 0 and avg > 0 and self._reconcile_every > 0 and self._tick_count % self._reconcile_every == 0:
            try:
                await _rec.ensure_stop(self, qty, avg)
                await _rec.reconcile_trades(self, window_min=60)
            except Exception as _e:
                log.warning("[robot-%s] reconcile: %s", self.rid, str(_e)[:120])
        equity = qty * cur
        ok, reason = self.risk.check(equity if equity > 0 else 1.0)
        if not ok:
            log.warning("[robot-%s] risk stop: %s", self.rid, reason)
            return

        if qty > 0 and avg > 0:
            sl = avg * (1 - self.stop_loss)
            tp = avg * (1 + self.tp)
            if self.trail > 0:
                if cur > self.peak_px:
                    self.peak_px = cur
                if not self.armed and cur >= avg * (1 + self.stop_loss):
                    self.armed = True
                if self.armed:
                    ts = self.peak_px * (1 - self.trail)
                    if ts > sl:
                        sl = ts
            if cur <= sl:
                await self.do_sell(qty, cur, "stop")
                return
            if cur >= tp:
                await self.do_sell(qty, cur, "tp")
                return

        sig = self.strategy.signal(candles, qty, avg)
        if sig.action == "BUY" and qty <= 0:
            _max_spread = float(self.params.get("max_spread_percent", 0.5))
            if _max_spread > 0:
                try:
                    _sp = await pf.get_spread_pct(self.c, self.figi)
                    if _sp >= 0 and _sp > _max_spread:
                        log.warning("[robot-%s] spread %.2f%%  skip", self.rid, _sp, _max_spread)
                        return
                except Exception:
                    pass
            size = self.strategy.position_size(cur)
            _cash = getattr(self, "_cash", 0.0)
            _maxpos = float(self.params.get("max_position_rub", 0))
            _budget = min(_cash, _maxpos) if _maxpos > 0 else _cash
            if _budget > 0 and size * cur > _budget:
                _n = int(_budget / cur)
                size = float(_n)
                log.info("[robot-%s] size reduced to %s by budget", self.rid, _n)
            if size > 0:
                done = await self.do_buy(size, cur)
                if done:
                    sp = cur * (1 - self.stop_loss)
                    try:
                        res = await od.post_stop_order(self.c, self.account_id, self.figi, size, round(sp, 2))
                        self.stop_order_id = res.order_id
                        try:
                            repo.save_state(self.rid, stop_order_id=self.stop_order_id)
                        except Exception:
                            pass
                    except Exception as e:
                        log.warning("[robot-%s] stop fail: %s", self.rid, str(e)[:100])
                    self.peak_px = cur
                    self.armed = False
        elif sig.action == "SELL" and qty > 0:
            await self.do_sell(qty, cur, "signal")
        else:
            log.info("[robot-%s] %s HOLD (%s) px=%s qty=%s", self.rid, self.ticker, sig.reason, round(cur, 2), qty)

    async def run(self):
        log.info("[robot-%s] start %s %s interval=%ss", self.rid, self.strategy.name, self.ticker, self.check_interval)
        try:
            _instr = await pf.get_instrument(self.c, self.figi)
            _it = _instr.get("instrumentType", "")
            self.lot = int(_instr.get("lot", 1) or 1)
            if _it not in ("share", "etf", "bond", "currency"):
                log.warning("[robot-%s] unknown instrument type: %s", self.rid, _it)
        except Exception as _e:
            log.warning("[robot-%s] instrument check: %s", self.rid, str(_e)[:120])
        try:
            _q, _a, _c = await self.get_position()
            if _q > 0 and _a > 0:
                await _rec.ensure_stop(self, _q, _a)
        except Exception as _e:
            log.warning("[robot-%s] startup reconcile: %s", self.rid, str(_e)[:120])
        while not self._stop:
            try:
                await self.tick()
            except Exception as e:
                log.error("[robot-%s] tick error: %s", self.rid, str(e)[:200])
                _nt.notify_error(self.rid, "tick: " + str(e)[:100])
            await self._sleep(self.check_interval)