# -*- coding: utf-8 -*-
from __future__ import annotations
import pathlib
import sys
from datetime import datetime
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from broker import schedule as sch

def test_trading_during_weekday_session():
    dt = datetime(2026, 10, 12, 12, 0, tzinfo=sch.MSK)
    ok, why = sch.is_trading_now(dt)
    assert ok is True
    assert why == "trading"

def test_closed_before_open():
    dt = datetime(2026, 10, 12, 8, 0, tzinfo=sch.MSK)
    ok, why = sch.is_trading_now(dt)
    assert ok is False

def test_closed_after_close():
    dt = datetime(2026, 10, 12, 20, 0, tzinfo=sch.MSK)
    ok, why = sch.is_trading_now(dt)
    assert ok is False

def test_weekend_closed():
    dt = datetime(2026, 10, 10, 12, 0, tzinfo=sch.MSK)
    ok, why = sch.is_trading_now(dt)
    assert ok is False
    assert why == "weekend"

def test_next_open_from_weekend():
    dt = datetime(2026, 10, 10, 12, 0, tzinfo=sch.MSK)
    nx = sch.next_open(dt)
    assert nx.weekday() < 5
    assert nx.hour == 9 and nx.minute == 10

def test_next_open_before_session():
    dt = datetime(2026, 10, 12, 7, 0, tzinfo=sch.MSK)
    nx = sch.next_open(dt)
    assert nx.hour == 9 and nx.minute == 10

def test_next_open_inside_session():
    dt = datetime(2026, 10, 12, 12, 0, tzinfo=sch.MSK)
    nx = sch.next_open(dt)
    assert nx == dt
