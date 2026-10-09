# -*- coding: utf-8 -*-
"""engine.py - единый бэктест-движок."""
from __future__ import annotations
from dataclasses import dataclass, field


COMMISSION = 0.0005


@dataclass
class Metrics:
    start_capital: float = 100000.0
    final_equity: float = 0.0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    trades_total: int = 0
    buys: int = 0
    sells: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    candles: int = 0
    equity_curve: list = field(default_factory=list)


def run_backtest(strategy, candles, qty_limit=100, stop_loss=0.05,
                 take_profit=0.15, trail_pct=0.0, start_capital=100000.0):
    cash = start_capital
    qty = 0.0
    avg = 0.0
    peak_px = 0.0
    armed = False
    peak_eq = start_capital
    max_dd = 0.0
    sells = []
    buys = 0
    equity_curve = []

    for i in range(len(candles)):
        sub = candles[:i + 1]
        px = candles[i].close

        if qty > 0 and avg > 0:
            sl = avg * (1 - stop_loss)
            tp = avg * (1 + take_profit)
            if trail_pct > 0:
                if px > peak_px:
                    peak_px = px
                if not armed and px >= avg * (1 + stop_loss):
                    armed = True
                if armed:
                    ts = peak_px * (1 - trail_pct)
                    if ts > sl:
                        sl = ts
            if px <= sl:
                fee = px * qty * COMMISSION
                cash += px * qty - fee
                sells.append((px - avg) * qty - fee)
                qty = 0.0; avg = 0.0; peak_px = 0.0; armed = False
            elif px >= tp:
                fee = px * qty * COMMISSION
                cash += px * qty - fee
                sells.append((px - avg) * qty - fee)
                qty = 0.0; avg = 0.0; peak_px = 0.0; armed = False

        sig = strategy.signal(sub, qty, avg)
        if sig.action == "BUY" and qty <= 0:
            size = float(qty_limit)
            cost = size * px
            fee = cost * COMMISSION
            if cash >= cost + fee:
                cash -= (cost + fee)
                qty = size
                avg = px
                peak_px = px
                armed = False
                buys += 1
        elif sig.action == "SELL" and qty > 0:
            fee = px * qty * COMMISSION
            cash += px * qty - fee
            sells.append((px - avg) * qty - fee)
            qty = 0.0; avg = 0.0; peak_px = 0.0; armed = False

        eq = cash + qty * px
        equity_curve.append(round(eq, 2))
        if eq > peak_eq:
            peak_eq = eq
        dd = (peak_eq - eq) / peak_eq if peak_eq > 0 else 0.0
        if dd > max_dd:
            max_dd = dd

    final = cash + qty * candles[-1].close
    pnl = final - start_capital
    pnl_pct = (pnl / start_capital) * 100.0
    wins = len([t for t in sells if t > 0])
    losses = len([t for t in sells if t < 0])

    return Metrics(
        start_capital=start_capital,
        final_equity=round(final, 2),
        pnl=round(pnl, 2),
        pnl_pct=round(pnl_pct, 2),
        max_drawdown_pct=round(max_dd * 100, 2),
        trades_total=len(sells),
        buys=buys,
        sells=len(sells),
        wins=wins,
        losses=losses,
        win_rate=round(wins / max(1, wins + losses) * 100, 1),
        candles=len(candles),
        equity_curve=equity_curve[-100:],
    )