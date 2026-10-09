# -*- coding: utf-8 -*-
"""models.py — Pydantic-модели T-Invest API."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field

class Money(BaseModel):
    units: int = 0
    nano: int = 0

    def to_float(self) -> float:
        return float(self.units) + float(self.nano) / 1e9

    @classmethod
    def from_any(cls, v) -> "Money":
        if v is None:
            return cls()
        if isinstance(v, dict):
            return cls(units=int(v.get("units", 0) or 0), nano=int(v.get("nano", 0) or 0))
        return cls()

class Candle(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: int = 0
    is_complete: bool = True

class Position(BaseModel):
    figi: str
    ticker: str = ""
    qty: float = 0.0
    avg_price: float = 0.0
    current_price: float = 0.0
    value: float = 0.0
    expected_yield: float = 0.0
    instrument_type: str = ""

class Portfolio(BaseModel):
    account_id: str
    positions: list[Position] = Field(default_factory=list)
    cash_rub: float = 0.0
    total_value: float = 0.0

class OrderResult(BaseModel):
    order_id: str = ""
    status: str = ""
    executed_qty: float = 0.0
    executed_price: float = 0.0
    commission: float = 0.0
    raw: dict = Field(default_factory=dict)

class Signal(BaseModel):
    action: str  # BUY | SELL | HOLD
    reason: str = ""
    qty: float = 0.0