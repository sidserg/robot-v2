# -*- coding: utf-8 -*-
"""test_engine.py - integration test RobotLoop с mock broker."""
import pathlib
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from broker.models import Candle, Position, Portfolio, OrderResult, Signal
from engine.loop import RobotLoop
from engine.risk import RiskManager

@pytest.fixture(autouse=True)
def _force_trading():
    with patch("engine.loop._sch.is_trading_now", return_value=(True, "test")):
        yield


def _cfg():
    return {
        "figi": "TEST",
        "ticker": "TST",
        "account_id": "acc",
        "mode": "sandbox",
        "strategy": "sma",
        "params": {
            "fast": 5, "slow": 20, "signal_mode": "slope",
            "stop_loss": 0.05, "take_profit": 0.15,
            "qty_limit": 10, "check_interval": 60,
            "days_back": 30, "timeframe": "D1",
        },
    }


def _candles_up(n=60):
    return [Candle(time=str(i), open=100 + i, high=101 + i, low=99 + i, close=100 + i) for i in range(n)]


def test_init_strategy():
    loop = RobotLoop({}, _cfg(), None)
    assert loop.rid == 0
    assert loop.strategy.name == "sma"
    assert loop.ticker == "TST"


@pytest.mark.asyncio
async def test_tick_buys_on_signal():
    loop = RobotLoop({}, _cfg(), None)
    loop.get_candles = AsyncMock(return_value=_candles_up(60))
    loop.get_position = AsyncMock(return_value=(0.0, 0.0, 0.0))
    loop.do_buy = AsyncMock(return_value=True)
    with patch("engine.loop.od.post_stop_order", new=AsyncMock(return_value=OrderResult(order_id="s1", status="STOP"))):
        await loop.tick()
    loop.do_buy.assert_awaited_once()


@pytest.mark.asyncio
async def test_tick_sells_on_stop_loss():
    loop = RobotLoop({}, _cfg(), None)
    cs = _candles_up(60)
    cs[-1] = Candle(time="x", open=50, high=50, low=50, close=50)
    loop.get_candles = AsyncMock(return_value=cs)
    loop.get_position = AsyncMock(return_value=(10.0, 100.0, 50.0))
    loop.do_sell = AsyncMock(return_value=True)
    await loop.tick()
    loop.do_sell.assert_awaited_once()
    assert "stop" in loop.do_sell.call_args[0][2]


@pytest.mark.asyncio
async def test_tick_holds_without_signal():
    loop = RobotLoop({}, _cfg(), None)
    cs = [Candle(time=str(i), open=100.0, high=100.0, low=100.0, close=100.0) for i in range(60)]
    loop.get_candles = AsyncMock(return_value=cs)
    loop.get_position = AsyncMock(return_value=(0.0, 0.0, 0.0))
    loop.do_buy = AsyncMock(return_value=True)
    loop.do_sell = AsyncMock(return_value=True)
    await loop.tick()
    loop.do_buy.assert_not_awaited()
    loop.do_sell.assert_not_awaited()


@pytest.mark.asyncio
async def test_risk_stops_before_buy():
    loop = RobotLoop({}, _cfg(), None)
    loop.risk = RiskManager({"max_drawdown": 0.001})
    loop.risk.peak_value = 100000.0
    loop.risk.stopped = True
    loop.get_candles = AsyncMock(return_value=_candles_up(60))
    loop.get_position = AsyncMock(return_value=(0.0, 0.0, 100.0))
    loop.do_buy = AsyncMock(return_value=True)
    await loop.tick()
    loop.do_buy.assert_not_awaited()