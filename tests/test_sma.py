# -*- coding: utf-8 -*-
"""test_sma.py - SMA strategy tests."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from broker.models import Candle
from strategies.sma import SMAStrategy

def _candles(prices):
    return [Candle(time=str(i), open=p, high=p, low=p, close=p) for i, p in enumerate(prices)]

def test_not_enough_candles():
    s = SMAStrategy({"fast": 5, "slow": 20})
    sig = s.signal(_candles([100.0] * 10), 0, 0)
    assert sig.action == "HOLD"

def test_slope_up_buy():
    s = SMAStrategy({"fast": 5, "slow": 20, "signal_mode": "slope"})
    cs = _candles([100 + i * 0.5 for i in range(40)])
    sig = s.signal(cs, 0, 0)
    assert sig.action == "BUY"

def test_slope_down_sell():
    s = SMAStrategy({"fast": 5, "slow": 20, "signal_mode": "slope"})
    cs = _candles([100 - i * 0.5 for i in range(40)])
    sig = s.signal(cs, 100, 105)
    assert sig.action == "SELL"

def test_slope_up_no_position_buy():
    s = SMAStrategy({"fast": 5, "slow": 20, "signal_mode": "slope"})
    cs = _candles([100 + i * 0.5 for i in range(40)])
    sig = s.signal(cs, 100, 95)
    assert sig.action == "HOLD"

def test_cross_up_buy():
    s = SMAStrategy({"fast": 5, "slow": 20, "signal_mode": "cross"})
    prices = [100.0] * 30 + [95.0] * 5 + [110.0] * 10
    cs = _candles(prices)
    sig = s.signal(cs, 0, 0)
    assert sig.action in ("BUY", "HOLD")

def test_position_size_default():
    s = SMAStrategy({"qty_limit": 50})
    assert s.position_size(100.0) == 50.0