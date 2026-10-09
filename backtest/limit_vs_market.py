# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import dataclass

COMMISSION = 0.0005

@dataclass
class Res:
    name: str
    pnl_pct: float
    trades: int
    fills: int
    skipped: int
    dd: float

def _run(candles, strategy, qty, stop_loss, tp, offset, use_limit, lookahead=3):
    cash = 100000.0
    start = cash
    pos_qty = 0.0
    avg = 0.0
    peak_eq = cash
    max_dd = 0.0
    trades = 0
    fills = 0
    skipped = 0
    pending = None
    for i in range(len(candles)):
        c = candles[i]
        px = c.close
        if pending:
            side = pending[0]
            lmt = pending[1]
            age = i - pending[2]
            hit = False
            if side == "BUY" and c.low <= lmt:
                hit = True
            if side == "SELL" and c.high >= lmt:
                hit = True
            if hit:
                if side == "BUY" and pos_qty <= 0:
                    cost = lmt * qty
                    fee = cost * COMMISSION
                    if cash >= cost + fee:
                        cash -= cost + fee
                        pos_qty = qty
                        avg = lmt
                        trades += 1
                        fills += 1
                elif side == "SELL" and pos_qty > 0:
                    fee = lmt * pos_qty * COMMISSION
                    cash += lmt * pos_qty - fee
                    pos_qty = 0.0
                    avg = 0.0
                    trades += 1
                    fills += 1
                pending = None
            elif age >= lookahead:
                skipped += 1
                pending = None
        if pos_qty > 0 and avg > 0:
            sl = avg * (1 - stop_loss)
            tp_px = avg * (1 + tp)
            if px <= sl or px >= tp_px:
                fee = px * pos_qty * COMMISSION
                cash += px * pos_qty - fee
                pos_qty = 0.0
                avg = 0.0
                trades += 1
                pending = None
        sub = candles[:i+1]
        sig = strategy.signal(sub, pos_qty, avg)
        if sig.action == "BUY" and pos_qty <= 0 and not pending:
            if use_limit:
                pending = ("BUY", px * (1 - offset), i)
            else:
                cost = px * qty
                fee = cost * COMMISSION
                if cash >= cost + fee:
                    cash -= cost + fee
                    pos_qty = qty
                    avg = px
                    trades += 1
                    fills += 1
        elif sig.action == "SELL" and pos_qty > 0 and not pending:
            if use_limit:
                pending = ("SELL", px * (1 + offset), i)
            else:
                fee = px * pos_qty * COMMISSION
                cash += px * pos_qty - fee
                pos_qty = 0.0
                avg = 0.0
                trades += 1
                fills += 1
        eq = cash + pos_qty * px
        if eq > peak_eq:
            peak_eq = eq
        dd = (peak_eq - eq) / peak_eq if peak_eq > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    final = cash + pos_qty * candles[-1].close
    pnl_pct = (final - start) / start * 100.0
    return pnl_pct, trades, fills, skipped, max_dd * 100.0

def compare(candles, strategy, qty=100, stop_loss=0.05, tp=0.15, offset=0.002, lookahead=3):
    m = _run(candles, strategy, qty, stop_loss, tp, 0.0, False, lookahead)
    l = _run(candles, strategy, qty, stop_loss, tp, offset, True, lookahead)
    return (Res("market", round(m[0],2), m[1], m[2], m[3], round(m[4],2)), Res("limit", round(l[0],2), l[1], l[2], l[3], round(l[4],2)))
