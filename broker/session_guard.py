# -*- coding: utf-8 -*-
"""session_guard - MOEX session awareness."""
from __future__ import annotations
from datetime import datetime, time, timezone, timedelta

MSK = timezone(timedelta(hours=3))
OPEN = time(9, 50, 0)
NORMAL_START = time(10, 5, 0)
NORMAL_END = time(18, 50, 0)
CLOSE = time(19, 0, 0)


def session_phase(now=None):
    dt = now or datetime.now(MSK)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=MSK)
    dt = dt.astimezone(MSK)
    if dt.weekday() >= 5:
        return "weekend"
    t = dt.time()
    if t < OPEN:
        return "pre-open"
    if t < NORMAL_START:
        return "open-auction"
    if t < NORMAL_END:
        return "normal"
    if t < CLOSE:
        return "close-auction"
    return "after-close"


def spread_limit_for_phase(phase, normal_limit=0.5):
    if phase in ("open-auction", "close-auction"):
        return normal_limit * 3.0
    if phase in ("pre-open", "after-close", "weekend"):
        return 0.0
    return normal_limit
