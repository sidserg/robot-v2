# -*- coding: utf-8 -*-
"""test_grid.py - Grid strategy tests."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from broker.models import Candle
from strategies.grid import GridStrategy

def _candles(prices):
    return [Candle(time=str(i), open=p, high=p, low=p, close=p) for i, p in enumerate(prices)]

def test_not_enough():
    s = GridStrategy({})
    sig = s.signal(_candles([100.0] * 5), 0, 0)
    assert sig.action == "HOLD"

def test_first_tick_hold():
    s = GridStrategy({"grid_levels": 10})
    cs = _candles([100.0 + (i % 5) * 0.1 for i in range(30)])
    sig = s.signal(cs, 0, 0)
    assert sig.action == "HOLD"
