# -*- coding: utf-8 -*-
"""loop.py - trade loop for one robot."""
from __future__ import annotations
import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from broker import portfolio as pf
from broker import orders as od
from broker import preflight as _pfl
from db import repo
from engine.risk import RiskManager
from strategies.sma import SMAStrategy
from strategies.grid import GridStrategy
from strategies.rsi import RSIStrategy
from strategies.bollinger import BollingerStrategy
from strategies.macd import MACDStrategy
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
    if name == "rsi":
        return RSIStrategy(params)
    if name == "bollinger":
        return BollingerStrategy(params)
    if name == "macd":
        return MACDStrategy(params)
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
        self._pending_result = None
        self._last_tick_time = 0.0
        self._force_reconcile = False
        self._offline_count = 0
        self._risk_alerted = False
        self._last_candle_ts = ""
        self._stale_candle_count = 0
        try:
            _st = repo.load_state(self.rid)
            if _st:
                self.stop_order_id = _st.get("stop_order_id") or None
                _ltt = _st.get("last_tick_ts")
                if _ltt:
                    try:
                        self._last_tick_time = float(_ltt)
                    except Exception:
                        pass
                self._pending_order_id = _st.get("pending_order_id") or None
                if self._pending_order_id:
                    log.info("[robot-%s] restored pending %s from state", self.rid, self._pending_order_id)
        except Exception:
            pass

    async def get_candles(self):
        to_dt = datetime.now(timezone.utc)
        fr_dt = to_dt - timedelta(days=self.days_back)
        interval = INTERVAL_MAP.get(self.timeframe, "CANDLE_INTERVAL_DAY")
        _cds = await pf.get_candles(
            self.c, self.figi,
            fr_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            to_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            interval,
        )
        _closed = [c for c in _cds if getattr(c, "is_complete", True)]
        return _closed if len(_closed) >= 30 else _cds

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
                try:
                    repo.save_state(self.rid, pending_order_id="")
                except Exception:
                    pass
                if _info:
                    try:
                        rec = dict(_info)
                        rec["ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                        rec["status"] = st
                        repo.add_trade(rec)
                        _nt.notify_trade(rec)
                        log.info("[robot-%s] limit FILL %s x %s = %s", self.rid, self.ticker, _info.get("qty"), _info.get("price"))
                    except Exception as _e:
                        log.error("[robot-%s] fill trade save: %s", self.rid, str(_e)[:100])
                return "FILL"
            if "REJECT" in st or "CANCEL" in st:
                self._pending_order_id = None
                try:
                    repo.save_state(self.rid, pending_order_id="")
                except Exception:
                    pass
                return "DEAD"
            self._pending_ticks = int(getattr(self, "_pending_ticks", 0) or 0) + 1
            if self._pending_ticks >= 3:
                try:
                    await od.cancel_order(self.c, self.account_id, self._pending_order_id)
                    log.warning("[robot-%s] pending %s timeout (3 ticks), cancel -> fallback market", self.rid, self._pending_order_id)
                except Exception:
                    pass
                self._pending_order_id = None
                self._pending_ticks = 0
                return "FALLBACK"
            return "WAIT"
        except Exception as e:
            log.warning("[robot-%s] pending check failed: %s", self.rid, str(e)[:100])
            self._pending_order_id = None
            return "DEAD"

    async def do_buy(self, qty, price):
        _p = self._pending_result or "NONE"
        self._pending_result = None
        if _p == "NONE":
            _p = await self._check_pending()
        if _p == "WAIT":
            log.info("[robot-%s] pending %s still open, skip", self.rid, self._pending_order_id)
            return False
        if _p == "FILL":
            log.info("[robot-%s] pending FILLed, will place stop next tick", self.rid)
            return True
        _force_market = (_p == "FALLBACK")
        if _force_market:
            log.warning("[robot-%s] limit timeout, force market BUY", self.rid)
        _lot = max(1, int(getattr(self, "lot", 1) or 1))
        qty = self._floor_lot(float(qty), _lot)
        if qty <= 0:
            log.warning("[robot-%s] qty below lot, skip buy", self.rid)
            return False
        try:
            _use_lim = bool(self.params.get("use_limit", False)) and not _force_market
            _ot = "ORDER_TYPE_LIMIT" if _use_lim else "ORDER_TYPE_MARKET"
            _off = float(self.params.get("limit_offset", 0.002))
            _px = round(price * (1 - _off), 2) if _use_lim else None
            res = await od.post_order(self.c, self.account_id, self.figi, qty, "ORDER_DIRECTION_BUY", order_type=_ot, price=_px)
            _st = (res.status or "").upper()
            if not res.order_id or len(str(res.order_id)) < 8:
                log.error("[robot-%s] BUY empty order_id, status=%s", self.rid, _st)
                try:
                    _nt.notify_error(self.rid, "BUY empty order_id")
                except Exception:
                    pass
                return False
            if _ot == "ORDER_TYPE_LIMIT" and "FILL" not in _st:
                self._pending_order_id = res.order_id
                self._pending_ticks = 0
                try:
                    repo.save_state(self.rid, pending_order_id=res.order_id)
                except Exception:
                    pass
                self._pending_info = {"robot_id": self.rid, "kind": "BUY", "ticker": self.ticker, "figi": self.figi, "qty": qty, "price": _px or price, "total": qty * (_px or price), "commission": 0.0, "order_id": res.order_id, "mode": self.mode, "strategy": self.strategy.name}
                log.info("[robot-%s] limit %s placed (status=%s), waiting next tick", self.rid, res.order_id, _st)
                return False
            rec = {
                "robot_id": self.rid,
                "ts": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
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
            _max_spread = float(self.params.get("max_spread_percent", 0.5))
            if _max_spread > 0 and reason == "signal":
                try:
                    _sp = await pf.get_spread_pct(self.c, self.figi)
                    if _sp >= 0 and _sp > _max_spread:
                        log.warning("[robot-%s] SELL spread %.2f%% > %.2f%%, skip", self.rid, _sp, _max_spread)
                        return False
                except Exception:
                    pass
            if self.stop_order_id:
                await od.cancel_stop_order(self.c, self.account_id, self.stop_order_id)
                self.stop_order_id = None
            _ot = "ORDER_TYPE_MARKET"
            _px = None
            res = await od.post_order(self.c, self.account_id, self.figi, qty, "ORDER_DIRECTION_SELL", order_type=_ot, price=_px)
            _st = (res.status or "").upper()
            if not res.order_id or len(str(res.order_id)) < 8:
                log.error("[robot-%s] SELL empty order_id, status=%s", self.rid, _st)
                try:
                    _nt.notify_error(self.rid, "SELL empty order_id")
                except Exception:
                    pass
                return False
            if "REJECT" in _st:
                log.error("[robot-%s] SELL REJECTED: %s", self.rid, _st)
                try:
                    repo.add_trade({"robot_id": self.rid, "ts": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), "kind": "SELL", "ticker": self.ticker, "figi": self.figi, "qty": qty, "price": price, "total": qty*price, "commission": 0.0, "order_id": res.order_id, "status": "REJECTED:"+_st, "mode": self.mode, "strategy": self.strategy.name})
                except Exception:
                    pass
                try:
                    _nt.notify_error(self.rid, "SELL rejected")
                except Exception:
                    pass
                return False
            rec = {
                "robot_id": self.rid,
                "ts": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
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
            _exec_px = float(getattr(res, "executed_price", 0) or 0)
            if _exec_px > 0 and price > 0:
                _slip = abs(_exec_px - price) / price * 100.0
                if _slip > 1.0:
                    log.warning("[robot-%s] SELL slippage %.2f%%: want %s got %s (%s)", self.rid, _slip, round(price,2), round(_exec_px,2), reason)
                    try:
                        _nt.notify_error(self.rid, "slip %.2f%% " % _slip + reason)
                    except Exception:
                        pass
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
        _now_ts = time.time()
        _gap = 0.0
        if self._last_tick_time > 0:
            _gap = _now_ts - self._last_tick_time
        self._last_tick_time = _now_ts
        _gap_limit = max(180.0, self.check_interval * 3.0)
        if _gap > _gap_limit:
            self._offline_count += 1
            log.warning("[robot-%s] gap detected: %.0fs offline (count=%s), forcing reconcile", self.rid, _gap, self._offline_count)
            self._force_reconcile = True
            try:
                _mnt = int(_gap // 60)
                _nt.notify("[R" + str(self.rid) + "] " + self.ticker, "связь восстановлена, offline " + str(_mnt) + " мин")
            except Exception:
                pass
            if self._offline_count >= 3:
                log.error("[robot-%s] 3 consecutive gaps, HALT robot", self.rid)
                try:
                    _nt.notify_error(self.rid, "HALT: 3 gaps in a row")
                except Exception:
                    pass
                self._stop = True
                return
        else:
            self._offline_count = 0
        if self._pending_order_id:
            _r = await self._check_pending()
            if _r in ("FILL","FALLBACK","DEAD"):
                self._pending_result = _r
        try:
            repo.save_state(self.rid, running=1, last_ts=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), last_tick_ts=str(_now_ts))
        except Exception:
            pass
        candles = await self.get_candles()
        if len(candles) < 30:
            log.warning("[robot-%s] not enough candles: %s", self.rid, len(candles))
            return
        _lct = candles[-1].time if candles else ""
        _tf_sec = 86400 if self.timeframe == "D1" else 3600
        _stale_ok = False
        try:
            from datetime import datetime as _dt
            _c_dt = _dt.strptime(_lct.replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
            _age = (datetime.now(timezone.utc).replace(tzinfo=None) - _c_dt).total_seconds()
            _stale_ok = _age > _tf_sec * 2
        except Exception:
            _stale_ok = False
        if _lct and _lct == self._last_candle_ts and _stale_ok:
            self._stale_candle_count += 1
            if self._stale_candle_count == 3:
                log.warning("[robot-%s] stale candles: last=%s x%s", self.rid, _lct, self._stale_candle_count)
                try:
                    _nt.notify_error(self.rid, "stale candles x" + str(self._stale_candle_count))
                except Exception:
                    pass
        else:
            self._last_candle_ts = _lct
            self._stale_candle_count = 0
        qty, avg, cur = await self.get_position()
        _last_close = candles[-1].close
        if cur <= 0:
            cur = _last_close
        elif _last_close > 0:
            _dev = abs(cur - _last_close) / _last_close * 100.0
            if _dev > 15.0:
                log.warning("[robot-%s] price %.2f deviates %.2f%% from candle %.2f, using candle", self.rid, cur, _dev, _last_close)
                cur = _last_close
        # periodic reconcile
        if self._force_reconcile and qty <= 0 and self.stop_order_id:
            log.info("[robot-%s] after gap: position closed, clearing stop %s", self.rid, self.stop_order_id)
            self.stop_order_id = None
            try:
                repo.save_state(self.rid, stop_order_id="")
            except Exception:
                pass
        _do_reconcile = (qty > 0 and avg > 0 and self._reconcile_every > 0 and self._tick_count % self._reconcile_every == 0)
        if self._force_reconcile:
            _do_reconcile = True
            self._force_reconcile = False
        if _do_reconcile:
            try:
                await _rec.ensure_stop(self, qty, avg)
                await _rec.reconcile_trades(self, window_min=60)
            except Exception as _e:
                log.warning("[robot-%s] reconcile: %s", self.rid, str(_e)[:120])
        if qty > 0 and avg <= 0:
            log.error("[robot-%s] anomaly: qty=%s but avg=0, skip trade", self.rid, qty)
            try:
                _nt.notify_error(self.rid, "anomaly: qty>0 avg=0")
            except Exception:
                pass
            return
        equity = qty * cur
        ok, reason = self.risk.check(equity if equity > 0 else 1.0)
        if not ok:
            log.warning("[robot-%s] risk stop: %s", self.rid, reason)
            if qty > 0 and avg > 0:
                try:
                    await _rec.ensure_stop(self, qty, avg)
                except Exception as _re:
                    log.warning("[robot-%s] ensure_stop after risk: %s", self.rid, str(_re)[:100])
                if not getattr(self, "_risk_alerted", False):
                    self._risk_alerted = True
                    try:
                        _nt.notify_error(self.rid, "risk stop: " + reason + " (position protected by stop)")
                    except Exception:
                        pass
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

        _max_jump = float(self.params.get("max_jump_percent", 5.0))
        _jump_ok = True
        if _max_jump > 0 and len(candles) >= 2:
            _prev = candles[-2].close
            if _prev > 0:
                _jmp = abs(cur - _prev) / _prev * 100.0
                if _jmp > _max_jump:
                    log.warning("[robot-%s] jump %.2f%% > %.2f%%, skip signal this tick", self.rid, _jmp, _max_jump)
                    _jump_ok = False
        if not _jump_ok:
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
                    _sp_chk = round(sp, 2)
                    if _sp_chk <= 0 or _sp_chk >= cur * 0.99 or _sp_chk < cur * 0.5:
                        log.error("[robot-%s] stop price suspicious: sp=%s cur=%s, skip", self.rid, _sp_chk, cur)
                        try:
                            _nt.notify_error(self.rid, "bad stop price " + str(_sp_chk))
                        except Exception:
                            pass
                    else:
                        try:
                            res = await od.post_stop_order(self.c, self.account_id, self.figi, size, _sp_chk)
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
        if self.mode == "real":
            _use_lim = bool(self.params.get("use_limit", False))
            _ok, _msg = await _pfl.check_real(self.c, self.figi, self.ticker, _use_lim)
            log.info("[robot-%s] preflight: %s", self.rid, _msg)
            if not _ok:
                log.error("[robot-%s] preflight FAILED, stopping robot", self.rid)
                try:
                    _nt.notify_error(self.rid, "preflight: " + _msg)
                except Exception:
                    pass
                self._stop = True
                return
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