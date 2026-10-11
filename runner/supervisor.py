# -*- coding: utf-8 -*-
"""supervisor.py - auto-restart crashed background tasks."""
from __future__ import annotations
import asyncio


async def supervisor(name, factory, stop_ev, log):
    while not stop_ev.is_set():
        try:
            await factory()
            log.info("supervisor: %s exited normally", name)
            return
        except asyncio.CancelledError:
            return
        except Exception as e:
            log.error("supervisor: %s crashed: %s, restart in 5s", name, str(e)[:150])
            try:
                await asyncio.wait_for(stop_ev.wait(), timeout=5)
            except asyncio.TimeoutError:
                pass
