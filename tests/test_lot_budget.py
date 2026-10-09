# -*- coding: utf-8 -*-
import asyncio
import time
from engine.loop import RobotLoop


def _mk():
    return RobotLoop.__new__(RobotLoop)


def test_floor_lot_exact():
    assert _mk()._floor_lot(100, 10) == 100.0


def test_floor_lot_round_down():
    assert _mk()._floor_lot(95, 10) == 90.0


def test_floor_lot_below_one_lot():
    assert _mk()._floor_lot(7, 10) == 0.0


def test_floor_lot_lot_one():
    assert _mk()._floor_lot(5, 1) == 5.0


def test_stop_sets_flag():
    lp = _mk()
    lp._stop = False
    lp.stop()
    assert lp._stop is True


def test_sleep_interruptible():
    lp = _mk()
    lp._stop = True
    t0 = time.time()
    asyncio.run(lp._sleep(5.0))
    assert time.time() - t0 < 1.0


def test_sleep_waits_full_when_running():
    lp = _mk()
    lp._stop = False
    t0 = time.time()
    asyncio.run(lp._sleep(1.2))
    assert time.time() - t0 >= 1.0
