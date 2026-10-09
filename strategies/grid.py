# -*- coding: utf-8 -*-
"""grid.py - Grid strategy. signal(candles) -> Signal."""
from __future__ import annotations
from strategies.base import Strategy
from broker.models import Candle, Signal


class GridStrategy(Strategy):
    name = "grid"

    def __init__(self, params):
        super().__init__(params)
        self.levels = int(self.params.get("grid_levels", 10))
        self.corridor_days = int(self.params.get("corridor_days", 90))
        self.lower_stop = float(self.params.get("grid_lower_stop", 0.03))
        self._last_price = None
        self._last_level = None
        self._position_buf = 0.0

    def _corridor(self, candles):
        if len(candles) < 20:
            return None, None
        n = min(len(candles), self.corridor_days)
        sub = candles[-n:]
        prices = sorted(c.close for c in sub)
        lo = prices[max(0, int(len(prices) * 0.05) - 1)]
        hi = prices[min(len(prices) - 1, int(len(prices) * 0.95))]
        return lo, hi

    def _level_idx(self, px, lo, hi):
        if hi <= lo:
            return None
        step = (hi - lo) / max(1, self.levels)
        idx = int((px - lo) / step)
        if idx < 0:
            return None
        if idx >= self.levels:
            return self.levels - 1
        return idx

    def signal(self, candles, position_qty, avg_price):
        lo, hi = self._corridor(candles)
        if lo is None:
            return Signal(action="HOLD", reason="not enough candles")
        px = candles[-1].close

        if avg_price > 0 and position_qty > 0:
            lower_stop = lo * (1 - self.lower_stop)
            if px <= lower_stop:
                return Signal(action="SELL", reason="stop " + str(round(lower_stop, 2)))

        idx = self._level_idx(px, lo, hi)
        if idx is None:
            self._last_level = None
            return Signal(action="HOLD", reason="outside corridor")

        prev = self._last_level
        self._last_level = idx

        if prev is None:
            return Signal(action="HOLD", reason="first tick")

        if idx < prev and position_qty <= 0:
            return Signal(action="BUY", reason="cross down level " + str(idx))
        if idx > prev and position_qty > 0:
            return Signal(action="SELL", reason="cross up level " + str(idx))
        return Signal(action="HOLD", reason="level " + str(idx))