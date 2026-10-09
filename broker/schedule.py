# -*- coding: utf-8 -*-
from __future__ import annotations
import json
import logging
import pathlib
from datetime import datetime, time, timezone, timedelta
log = logging.getLogger("broker.schedule")
MSK = timezone(timedelta(hours=3))
ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "schedule.json"
OPEN = time(9, 10)
CLOSE = time(18, 59)
_days = {}
_loaded = False
def load_cache():
    global _days, _loaded
    try:
        raw = json.loads(CACHE.read_text(encoding="utf-8"))
        _days = {k: bool(v) for k, v in raw.items()}
        _loaded = True
        log.info("schedule loaded: " + str(len(_days)) + " days")
    except Exception:
        _loaded = False
def is_trading_now(now=None):
    dt = now or datetime.now(MSK)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=MSK)
    dt = dt.astimezone(MSK)
    if dt.weekday() >= 5:
        return False, "weekend"
    d = dt.strftime("%Y-%m-%d")
    if _loaded and d in _days and not _days[d]:
        return False, "holiday"
    t = dt.time()
    if OPEN <= t < CLOSE:
        return True, "trading"
    return False, "closed "+t.strftime("%H:%M")
def next_open(now=None):
    dt = now or datetime.now(MSK)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=MSK)
    dt = dt.astimezone(MSK)
    for _ in range(15):
        if dt.weekday() < 5 and dt.time() < CLOSE:
            if dt.time() < OPEN:
                return dt.replace(hour=9, minute=10, second=0, microsecond=0)
            return dt
        dt = (dt + timedelta(days=1)).replace(hour=9, minute=10, second=0, microsecond=0)
    return dt
load_cache()