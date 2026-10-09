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
    r = RiskManager({"daily_loss_limit": 0.05})
    r.check(100000.0)
    ok, reason = r.check(94000.0)
    assert not ok
    assert "daily" in reason

def test_daily_loss_within_limit():
    r = RiskManager({"daily_loss_limit": 0.05})
    r.check(100000.0)
    ok, _ = r.check(97000.0)
    assert ok

def test_max_drawdown_stop():
    r = RiskManager({"max_drawdown": 0.20})
    r.check(100000.0)
    r.check(120000.0)
    ok, reason = r.check(90000.0)
    assert not ok
    assert "drawdown" in reason

def test_stopped_stays_stopped():
    r = RiskManager({"max_drawdown": 0.10})
    r.check(100000.0)
    r.check(50000.0)
    ok, _ = r.check(100000.0)
    assert not ok