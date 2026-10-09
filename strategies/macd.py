# -*- coding: utf-8 -*-
from __future__ import annotations
from strategies.base import Strategy
from broker.models import Signal
from strategies import indicators as ind

class MACDStrategy(Strategy):
    name = "macd"
    def signal(self, candles, position_qty, avg_price):
        fast = int(self.params.get("macd_fast", 12))
        slow = int(self.params.get("macd_slow", 26))
        sig_p = int(self.params.get("macd_signal", 9))
        closes = [c.close for c in candles]
        if len(closes) < slow + sig_p + 2:
            return Signal(action="HOLD", reason="not enough candles")
        m1, s1, h1 = ind.macd(closes, fast, slow, sig_p)
        m0, s0, h0 = ind.macd(closes[:-1], fast, slow, sig_p)
        if None in (m0, s0, m1, s1):
            return Signal(action="HOLD", reason="macd None")
        if position_qty <= 0 and h0 <= 0 and h1 > 0:
            return Signal(action="BUY", reason="macd cross up")
        if position_qty > 0 and h0 >= 0 and h1 < 0:
            return Signal(action="SELL", reason="macd cross down")
        return Signal(action="HOLD", reason="macd "+str(round(h1,2)))