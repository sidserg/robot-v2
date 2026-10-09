# -*- coding: utf-8 -*-
"""data.py - load candles for backtest."""
from __future__ import annotations
import asyncio
import pathlib
from datetime import datetime, timezone, timedelta
from broker.client import TInvestClient
from broker import portfolio as pf
from broker.models import Candle

def read_token(path="token.txt"):
    p = pathlib.Path(path)
    return p.read_text(encoding="utf-8-sig").strip()

INTERVALS = {"H1": "CANDLE_INTERVAL_HOUR", "D1": "CANDLE_INTERVAL_DAY", "M1": "CANDLE_INTERVAL_1_MIN", "M5": "CANDLE_INTERVAL_5_MIN"}

async def load_candles(figi, days=730, timeframe="D1", mode="sandbox", token=None):
    tok = token or read_token()
    interval = INTERVALS.get(timeframe.upper(), "CANDLE_INTERVAL_DAY")
    to_dt = datetime.now(timezone.utc)
    fr_dt = to_dt - timedelta(days=days)
    async with TInvestClient(tok, mode=mode) as c:
        return await pf.get_candles(c, figi, fr_dt.strftime("%Y-%m-%dT%H:%M:%SZ"), to_dt.strftime("%Y-%m-%dT%H:%M:%SZ"), interval)

def load_candles_sync(figi, days=730, timeframe="D1", mode="sandbox", token=None):
    return asyncio.run(load_candles(figi, days=days, timeframe=timeframe, mode=mode, token=token))