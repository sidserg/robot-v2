# -*- coding: utf-8 -*-
from __future__ import annotations
from strategies.base import Strategy
from broker.models import Signal
from strategies import indicators as ind

class BollingerStrategy(Strategy):
    name = "bollinger"
    def signal(self, candles, position_qty, avg_price):
        period = int(self.params.get("bb_period", 20))
        mult = float(self.params.get("bb_mult", 2.0))
        closes = [c.close for c in candles]
        if len(closes) < period + 2:
            return Signal(action="HOLD", reason="not enough candles")
        low, mid, high = ind.bollinger(closes, period, mult)
        if low is None:
            return Signal(action="HOLD", reason="bb None")
        px = closes[-1]
        if position_qty <= 0 and px <= low:
            return Signal(action="BUY", reason="bb low")
        if position_qty > 0 and px >= high:
            return Signal(action="SELL", reason="bb high")
        return Signal(action="HOLD", reason="inside bb")