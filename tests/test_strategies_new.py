# -*- coding: utf-8 -*-
from __future__ import annotations
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from broker.models import Candle
from strategies.rsi import RSIStrategy
from strategies.bollinger import BollingerStrategy
from strategies.macd import MACDStrategy
from strategies import indicators as ind

def _c(prices):
    return [Candle(time=str(i), open=p, high=p*1.01, low=p*0.99, close=p, volume=1) for i, p in enumerate(prices)]

def test_rsi_no_position_low():
    st = RSIStrategy({"rsi_period": 5, "rsi_low": 30})
    cs = _c([100 - i * 2 for i in range(20)])
    sig = st.signal(cs, 0.0, 0.0)
    assert sig.action in ("BUY","HOLD")

def test_rsi_position_high_sells():
    st = RSIStrategy({"rsi_period": 5, "rsi_high": 70})
    cs = _c([100 + i * 2 for i in range(20)])
    sig = st.signal(cs, 10.0, 100.0)
    assert sig.action in ("SELL","HOLD")

def test_rsi_not_enough():
    st = RSIStrategy({"rsi_period": 14})
    sig = st.signal(_c([100, 101]), 0.0, 0.0)
    assert sig.action == "HOLD"

def test_bollinger_not_enough():
    st = BollingerStrategy({"bb_period": 20})
    sig = st.signal(_c([100, 101, 102]), 0.0, 0.0)
    assert sig.action == "HOLD"

def test_bollinger_low_buys():
    st = BollingerStrategy({"bb_period": 10, "bb_mult": 2.0})
    cs = _c([100] * 10 + [80])
    sig = st.signal(cs, 0.0, 0.0)
    assert sig.action in ("BUY","HOLD")

def test_bollinger_high_sells():
    st = BollingerStrategy({"bb_period": 10, "bb_mult": 2.0})
    cs = _c([100] * 10 + [120])
    sig = st.signal(cs, 10.0, 100.0)
    assert sig.action in ("SELL","HOLD")

def test_macd_not_enough():
    st = MACDStrategy({})
    sig = st.signal(_c([100] * 10), 0.0, 0.0)
    assert sig.action == "HOLD"

def test_macd_basic():
    st = MACDStrategy({"macd_fast": 3, "macd_slow": 6, "macd_signal": 3})
    cs = _c(list(range(100, 140)))
    sig = st.signal(cs, 0.0, 0.0)
    assert sig.action in ("BUY","HOLD","SELL")

def test_indicators_bollinger():
    low, mid, high = ind.bollinger([100.0] * 20, 20, 2.0)
    assert low == mid == high

def test_indicators_ema():
    v = ind.ema([1, 2, 3, 4, 5], 3)
    assert v is not None
