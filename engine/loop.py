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
        for pos in p.positions:
            if pos.figi == self.figi:
                return pos.qty, pos.avg_price, pos.current_price
        return 0.0, 0.0, 0.0

    async def do_buy(self, qty, price):
        try:
            res = await od.post_order(self.c, self.account_id, self.figi, qty, "ORDER_DIRECTION_BUY")
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
            log.info("[robot-%s] BUY %s x %s = %s", self.rid, self.ticker, qty, round(qty * price, 2))
            return True
        except Exception as e:
            log.error("[robot-%s] BUY FAILED: %s", self.rid, str(e)[:200])
            return False

    async def do_sell(self, qty, price, reason="signal"):
        try:
            if self.stop_order_id:
                await od.cancel_stop_order(self.c, self.account_id, self.stop_order_id)
                self.stop_order_id = None
            res = await od.post_order(self.c, self.account_id, self.figi, qty, "ORDER_DIRECTION_SELL")
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
            log.info("[robot-%s] SELL %s x %s = %s (%s)", self.rid, self.ticker, qty, round(qty * price, 2), reason)
            self.peak_px = 0.0
            self.armed = False
            return True
        except Exception as e:
            log.error("[robot-%s] SELL FAILED: %s", self.rid, str(e)[:200])
            return False

    async def tick(self):
        self._tick_count += 1
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
            size = self.strategy.position_size(cur)
            if size > 0:
                done = await self.do_buy(size, cur)
                if done:
                    sp = cur * (1 - self.stop_loss)
                    try:
                        res = await od.post_stop_order(self.c, self.account_id, self.figi, size, round(sp, 2))
                        self.stop_order_id = res.order_id
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
            _q, _a, _c = await self.get_position()
            if _q > 0 and _a > 0:
                await _rec.ensure_stop(self, _q, _a)
        except Exception as _e:
            log.warning("[robot-%s] startup reconcile: %s", self.rid, str(_e)[:120])
        while True:
            try:
                await self.tick()
            except Exception as e:
                log.error("[robot-%s] tick error: %s", self.rid, str(e)[:200])
            await asyncio.sleep(self.check_interval)