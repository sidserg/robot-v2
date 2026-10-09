# -*- coding: utf-8 -*-
"""sma.py - SMA strategy."""
from __future__ import annotations
from strategies.base import Strategy
from broker.models import Candle, Signal

def _sma(values, period):
    if len(values) < period:
        return None
    return sum(values[-period:]) / period

class SMAStrategy(Strategy):
    name = "sma"
    def signal(self, candles, position_qty, avg_price):
        fast_p = int(self.params.get("fast", 5))
        slow_p = int(self.params.get("slow", 20))
        mode = self.params.get("signal_mode", "cross")
        closes = [c.close for c in candles]
        if len(closes) < slow_p + 2:
            return Signal(action="HOLD", reason="not enough candles")
        fast_now = _sma(closes, fast_p)
        slow_now = _sma(closes, slow_p)
        fast_prev = _sma(closes[:-1], fast_p)
        slow_prev = _sma(closes[:-1], slow_p)
        if fast_now is None or slow_now is None:
            return Signal(action="HOLD", reason="not enough candles")
        if mode == "slope":
            up = slow_now > slow_prev
            down = slow_now < slow_prev
        else:
            up = fast_prev <= slow_prev and fast_now > slow_now
            down = fast_prev >= slow_prev and fast_now < slow_now
        if up and position_qty <= 0:
            return Signal(action="BUY", reason="signal UP")
        if down and position_qty > 0:
            return Signal(action="SELL", reason="signal DOWN")
        return Signal(action="HOLD", reason="no signal")