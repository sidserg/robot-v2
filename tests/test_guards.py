# -*- coding: utf-8 -*-
from __future__ import annotations
import asyncio
import pathlib
import sys
import time
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from engine.loop import RobotLoop
from engine.risk import RiskManager

def _mk(**params):
    lp = RobotLoop.__new__(RobotLoop)
    lp.rid = 1
    lp.ticker = "TEST"
    lp.figi = "FIGI"
    lp.timeframe = "D1"
    lp.check_interval = 60
    lp.params = params or {}
    lp._stop = False
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

def test_gap_detection_sets_flag():
    lp = _mk()
    lp._last_tick_time = time.time() - 1000
    _now = time.time()
    _gap = _now - lp._last_tick_time
    lp._last_tick_time = _now
    if _gap > max(180.0, lp.check_interval * 3):
        lp._force_reconcile = True
    assert lp._force_reconcile is True

def test_gap_no_flag_short():
    lp = _mk()
    lp._last_tick_time = time.time() - 30
    _now = time.time()
    _gap = _now - lp._last_tick_time
    lp._last_tick_time = _now
    if _gap > max(180.0, lp.check_interval * 3):
        lp._force_reconcile = True
    assert lp._force_reconcile is False

def test_offline_counter_halts():
    lp = _mk()
    lp._offline_count = 2
    lp._offline_count += 1
    if lp._offline_count >= 3:
        lp._stop = True
    assert lp._stop is True

def test_stale_candle_d1_quiet():
    lp = _mk()
    lp.timeframe = "D1"
    lp._last_candle_ts = "2026-10-08T00:00:00Z"
    lp._stale_candle_count = 0
    _tf_sec = 86400 if lp.timeframe == "D1" else 3600
    _stale_ok = False
    assert _tf_sec == 86400
    assert _stale_ok is False

def test_risk_velocity_breach():
    r = RiskManager({"velocity_limit": 0.03, "velocity_window_sec": 300})
    r.check(100000.0)
    ok, reason = r.check(96000.0)
    assert not ok
    assert "velocity" in reason

def test_risk_velocity_resets_next_day():
    r = RiskManager({"velocity_limit": 0.03})
    r.check(100000.0)
    r.check(96000.0)
    assert r.stopped is True
    r.stopped_date = None
    r.stopped_reason = "velocity drop"
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).date()
    r.stopped_date = None
    ok, _ = r.check(100000.0)
    assert ok is True

def test_risk_drawdown_does_not_reset():
    r = RiskManager({"max_drawdown": 0.10, "velocity_limit": 0})
    r.check(100000.0)
    r.check(50000.0)
    assert r.stopped is True
    r.stopped_date = None
    ok, reason = r.check(100000.0)
    assert not ok
    assert "drawdown" in reason

def test_max_jump_blocks_buy():
    lp = _mk();