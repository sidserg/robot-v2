# -*- coding: utf-8 -*-
"""base.py - стратегия: интерфейс."""
from __future__ import annotations
from typing import Any
from broker.models import Candle, Signal

class Strategy:
    name = "base"

    def __init__(self, params):
        self.params = params or {}

    def signal(self, candles: list[Candle], position_qty: float, avg_price: float) -> Signal:
        raise NotImplementedError

    def position_size(self, price: float) -> float:
        return float(self.params.get("qty_limit", self.params.get("quantity_limit", 10)) or 10)