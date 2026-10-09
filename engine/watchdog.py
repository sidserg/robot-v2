# -*- coding: utf-8 -*-
"""watchdog.py - asyncio watchdog для роботов."""
from __future__ import annotations
import asyncio
import logging
from datetime import datetime

log = logging.getLogger("engine.watchdog")

class Watchdog:
    def __init__(self, loops, check_sec=60, stall_sec=240):
        self.loops = loops
        self.check_sec = check_sec
        self.stall_sec = stall_sec
        self.last_tick = {lp.rid: datetime.now() for lp in loops}

    def mark_tick(self, rid):
        self.last_tick[rid] = datetime.now()

    async def run(self):
        log.info("watchdog started, check=%ss stall=%ss", self.check_sec, self.stall_sec)
        while True:
            await asyncio.sleep(self.check_sec)
            now = datetime.now()
            for lp in self.loops:
                last = self.last_tick.get(lp.rid)
                if last is None:
                    continue
                age = (now - last).total_seconds()
                if age > self.stall_sec:
                    log.warning("[robot-%s] stalled %ss", lp.rid, int(age))