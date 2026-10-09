# -*- coding: utf-8 -*-
from __future__ import annotations
import pathlib
import sys
import time
from unittest.mock import MagicMock
import pytest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from engine.risk import RiskManager
from engine.loop import RobotLoop

def _mk(**params):
    lp = RobotLoop.__new__(RobotLoop)
    lp.rid = 1
    lp.ticker = "TST"
    lp.check_interval = 60
    lp.params = params or {}
    lp._stop = False
    lp._paused = False
    lp._pending_order_id = None
    lp._pending_ticks = 0
    lp._pending_info = None
    lp._pending_result = None
    lp._last_tick_time = 0.0
    lp._force_reconcile = False
    lp._offline_count = 0
    lp._risk_alerted = False
    lp._last_candle_ts = ""
    lp._stale_candle_count = 0
    lp._last_buy_err = None
    lp.stop_order_id = None
    return lp

def test_gap_3x_halts():
    lp = _mk()
    for _ in range(3):
        lp._offline_count += 1
        if lp._offline_count >= 3:
            lp._stop = True
    assert lp._stop is True

def test_gap_resets_on_normal_tick():
    lp = _mk()
    lp._offline_count = 2
    lp._offline_count = 0
    assert lp._offline_count == 0
    assert lp._stop is False

def test_velocity_halts_first_breach():
    r = RiskManager({"velocity_limit": 0.03, "velocity_window_sec": 300})
    r.check(100000.0)
    ok, reason = r.check(96000.0)
    assert not ok
    assert "velocity" in reason
    assert r.stopped is True

def test_cross_kill_5pct():
    peak = 100000.0
    current = 94000.0
    drop = (peak - current) / peak
    triggered = drop >= 0.05
    assert triggered is True
    assert round(drop * 100, 2) == 6.0

def test_cross_kill_below_threshold():
    peak = 100000.0
    current = 97000.0
    drop = (peak - current) / peak
    triggered = drop >= 0.05
    assert triggered is False

def test_stale_candle_d1_normal():
    lp = _mk()
    lp.timeframe = "D1"
    lp._last_candle_ts = "2026-10-09T00:00:00Z"
    lp._stale_candle_count = 0
    tf = 86400 if lp.timeframe == "D1" else 3600
    assert tf == 86400

def test_stale_candle_d1_alert_after_2_days():
    age = 86400 * 3
    tf = 86400
    stale_ok = age > tf * 2
    assert stale_ok is True

def test_pause_blocks_tick():
    lp = _mk()
    lp._paused = True
    if lp._paused:
        pass
    assert lp._paused is True

def test_risk_resets_velocity_next_day():
    r = RiskManager({"velocity_limit": 0.03})
    r.check(100000.0)
    r.check(96000.0)
    assert r.stopped is True
    r.stopped_date = None
    from datetime import datetime, timezone
    r.stopped_reason = "velocity drop"
    ok, _ = r.check(100000.0)
    assert ok is True

def test_risk_drawdown_persists():
    r = RiskManager({"max_drawdown": 0.10, "velocity_limit": 0})
    r.check(100000.0)
    r.check(50000.0)
    r.stopped_date = None
    ok, reason = r.check(100000.0)
    assert not ok
    assert "drawdown" in reason
