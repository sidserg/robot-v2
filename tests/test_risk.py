# -*- coding: utf-8 -*-
"""test_risk.py - risk manager tests."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from engine.risk import RiskManager

def test_no_limits_ok():
    r = RiskManager({})
    ok, _ = r.check(1000.0)
    assert ok

def test_daily_loss_stop():
    r = RiskManager({"daily_loss_limit": 0.05, "velocity_limit": 0})
    r.check(100000.0)
    ok, reason = r.check(94000.0)
    assert not ok
    assert "daily" in reason

def test_daily_loss_within_limit():
    r = RiskManager({"daily_loss_limit": 0.05, "velocity_limit": 0})
    r.check(100000.0)
    ok, _ = r.check(97000.0)
    assert ok

def test_max_drawdown_stop():
    r = RiskManager({"max_drawdown": 0.20, "velocity_limit": 0})
    r.check(100000.0)
    r.check(120000.0)
    ok, reason = r.check(90000.0)
    assert not ok
    assert "drawdown" in reason

def test_stopped_stays_stopped():
    r = RiskManager({"max_drawdown": 0.10, "velocity_limit": 0})
    r.check(100000.0)
    r.check(50000.0)
    ok, _ = r.check(100000.0)
    assert not ok

def test_velocity_breaker():
    r = RiskManager({"velocity_limit": 0.03, "velocity_window_sec": 300})
    r.check(100000.0)
    ok, reason = r.check(96000.0)
    assert not ok
    assert "velocity" in reason


def test_velocity_state_persists():
    from db import repo as _r
    import time
    _now = time.time() + 1800
    _r.save_state(999, velocity_cooldown_until=_now, velocity_half_open=1, risk_scale=0.5)
    s = _r.load_state(999)
    assert s is not None
    assert abs(float(s.get("velocity_cooldown_until") or 0) - _now) < 1
    assert int(s.get("velocity_half_open") or 0) == 1
    assert abs(float(s.get("risk_scale") or 0) - 0.5) < 0.01
    import sqlite3
    c = sqlite3.connect(str(_r.db_path()))
    c.execute("DELETE FROM robot_state WHERE robot_id=999")
    c.commit(); c.close()