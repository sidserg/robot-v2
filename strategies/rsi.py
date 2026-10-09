# -*- coding: utf-8 -*-
from __future__ import annotations
from strategies.base import Strategy
from broker.models import Signal
from strategies import indicators as ind

class RSIStrategy(Strategy):
    name = "rsi"
    def signal(self, candles, position_qty, avg_price):
        period = int(self.params.get("rsi_period", 14))
        low = float(self.params.get("rsi_low", 30.0))
        high = float(self.params.get("rsi_high", 70.0))
        closes = [c.close for c in candles]
        if len(closes) < period + 2:
            return Signal(action="HOLD", reason="not enough candles")
        r = ind.rsi(closes, period)
        if r is None:
            return Signal(action="HOLD", reason="rsi None")
        if position_qty <= 0 and r <= low:
            return Signal(action="BUY", reason="rsi "+str(round(r,1)))
        if position_qty > 0 and r >= high:
            return Signal(action="SELL", reason="rsi "+str(round(r,1)))
        return Signal(action="HOLD", reason="rsi "+str(round(r,1)))