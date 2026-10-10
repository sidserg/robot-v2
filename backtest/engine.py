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


def _atr(candles, i, period):
    if i < period: return 0.0
    trs=[]
    for k in range(i-period+1, i+1):
        h=candles[k].high; l=candles[k].low; pc=candles[k-1].close if k>0 else candles[k].close
        tr=max(h-l, abs(h-pc), abs(l-pc))
        trs.append(tr)
    return sum(trs)/len(trs) if trs else 0.0

def run_backtest(strategy, candles, qty_limit=100, stop_loss=0.05,
                 take_profit=0.15, trail_pct=0.0, start_capital=100000.0,
                 atr_sizing=False, atr_period=14, atr_mult=2.0, risk_pct=0.02,
                 slippage_pct=0.0):
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
            _sl_px = px * (1 - slippage_pct) if slippage_pct > 0 else px
            if px <= sl:
                fee = _sl_px * qty * COMMISSION
                cash += _sl_px * qty - fee
                sells.append((_sl_px - avg) * qty - fee)
                qty = 0.0; avg = 0.0; peak_px = 0.0; armed = False
            elif px >= tp:
                fee = _sl_px * qty * COMMISSION
                cash += _sl_px * qty - fee
                sells.append((_sl_px - avg) * qty - fee)
                qty = 0.0; avg = 0.0; peak_px = 0.0; armed = False

        sig = strategy.signal(sub, qty, avg)
        if sig.action == "BUY" and qty <= 0:
            size = float(qty_limit)
            if atr_sizing:
                _a=_atr(candles,i,atr_period)
                if _a>0 and atr_mult>0:
                    _budget=cash*risk_pct
                    _sz=int(_budget/(_a*atr_mult))
                    if _sz>0:
                        size=min(size,float(_sz))
            _buy_px=px*(1+slippage_pct) if slippage_pct>0 else px
            cost = size * _buy_px
            fee = cost * COMMISSION
            if cash >= cost + fee:
                cash -= (cost + fee)
                qty = size
                avg = _buy_px
                peak_px = _buy_px
                armed = False
                buys += 1
        elif sig.action == "SELL" and qty > 0:
            _sell_px = px * (1 - slippage_pct) if slippage_pct > 0 else px
            fee = _sell_px * qty * COMMISSION
            cash += _sell_px * qty - fee
            sells.append((_sell_px - avg) * qty - fee)
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