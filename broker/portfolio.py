# -*- coding: utf-8 -*-
"""portfolio.py - methods: portfolio, candles, instrument."""
from __future__ import annotations
from typing import Any
from broker.client import TInvestClient
from broker.models import Money, Candle, Position, Portfolio

def _f(v):
    return Money.from_any(v).to_float()

async def get_accounts(c: TInvestClient) -> list[dict]:
    r = await c.call("UsersService/GetAccounts", {})
    return [a for a in r.get("accounts", []) if a.get("status") == "ACCOUNT_STATUS_OPEN"]

async def get_portfolio(c: TInvestClient, account_id: str) -> Portfolio:
    r = await c.call("OperationsService/GetPortfolio", {"accountId": account_id, "currency": "RUB"})
    positions = []
    for p in r.get("positions", []):
        q = p.get("quantity") or {}
        qty = _f(q)
        cur = _f(p.get("currentPrice"))
        avg = _f(p.get("averagePositionPrice"))
        yld = _f(p.get("expectedYield"))
        positions.append(Position(figi=p.get("figi", ""), ticker=p.get("ticker", ""), qty=qty, avg_price=avg, current_price=cur, value=cur * qty, expected_yield=yld, instrument_type=p.get("instrumentType", "")))
    cash_rub = _f(r.get("totalAmountCurrencies"))
    total = _f(r.get("totalAmountPortfolio"))
    return Portfolio(account_id=account_id, positions=positions, cash_rub=cash_rub, total_value=total)

async def get_candles(c: TInvestClient, figi: str, from_i: str, to_i: str, interval: str = "CANDLE_INTERVAL_HOUR") -> list[Candle]:
    r = await c.call("MarketDataService/GetCandles", {"figi": figi, "from": from_i, "to": to_i, "interval": interval})
    out = []
    for k in r.get("candles", []):
        c_ = _f(k.get("close"))
        if c_ <= 0:
            continue
        out.append(Candle(time=k.get("time", ""), open=_f(k.get("open")), high=_f(k.get("high")) or c_, low=_f(k.get("low")) or c_, close=c_, volume=int(k.get("volume", 0) or 0), is_complete=bool(k.get("isComplete", True))))
    return out

async def get_last_price(c: TInvestClient, figi: str) -> float:
    r = await c.call("MarketDataService/GetLastPrices", {"figi": [figi]})
    prices = r.get("lastPrices", [])
    if not prices:
        return 0.0
    return _f(prices[0].get("price"))

async def get_instrument(c: TInvestClient, figi: str) -> dict:
    r = await c.call("InstrumentsService/GetInstrumentBy", {"idType": "INSTRUMENT_ID_TYPE_FIGI", "id": figi})
    return r.get("instrument", {})