# -*- coding: utf-8 -*-
"""startup_filter.py - warmup + market context."""
from __future__ import annotations

def warmup_ok(robot) -> tuple[bool, str]:
    _max = int(getattr(robot, "_warmup_ticks", 3) or 3)
    _done = int(getattr(robot, "_warmup_done", 0) or 0)
    if _done >= _max:
        return True, "ok"
    _done += 1
    robot._warmup_done = _done
    return False, "warmup " + str(_done) + "/" + str(_max)

def market_drop_pct(candles, lookback=5) -> float:
    if not candles or len(candles) < lookback + 1:
        return 0.0
    try:
        _now = candles[-1].close
        _old = candles[-1 - lookback].close
        if _old <= 0:
            return 0.0
        return (_old - _now) / _old * 100.0
    except Exception:
        return 0.0
