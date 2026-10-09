# -*- coding: utf-8 -*-
from __future__ import annotations
from datetime import datetime, time, timezone, timedelta
import logging
log = logging.getLogger("broker.schedule")
MSK = timezone(timedelta(hours=3))
MORNING_OPEN = time(6, 50)
MAIN_OPEN = time(9, 50)
EVENING_OPEN = time(19, 0)
CLOSE = time(23, 50)
WEEKEND_OPEN = time(9, 50)
WEEKEND_CLOSE = time(19, 0)
def is_trading_now(now=None):
    dt = now or datetime.now(MSK)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=MSK)
    dt = dt.astimezone(MSK)
    t = dt.time()
    wd = dt.weekday()
    if wd >= 5:
        if WEEKEND_OPEN <= t < WEEKEND_CLOSE:
            return True, "weekend session"
        return False, "weekend closed ("+t.strftime("%H:%M")+")"
    if MORNING_OPEN <= t < MAIN_OPEN:
        return True, "morning"
    if MAIN_OPEN <= t < EVENING_OPEN:
        return True, "main"
    if EVENING_OPEN <= t < CLOSE:
        return True, "evening"
    return False, "closed ("+t.strftime("%H:%M")+")"
def next_open(now=None):
    dt = now or datetime.now(MSK)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=MSK)
    dt = dt.astimezone(MSK)
    for _ in range(10):
        wd = dt.weekday()
        t = dt.time()
        if wd >= 5:
            if t < WEEKEND_OPEN:
                return dt.replace(hour=9, minute=50, second=0, microsecond=0)
        else:
            if t < MORNING_OPEN:
                return dt.replace(hour=6, minute=50, second=0, microsecond=0)
            if t < MAIN_OPEN:
                return dt.replace(hour=9, minute=50, second=0, microsecond=0)
            if t < EVENING_OPEN:
                return dt.replace(hour=19, minute=0, second=0, microsecond=0)
        dt = (dt + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return dt