# -*- coding: utf-8 -*-
"""reconcile.py - сверка позиции и стопа с T-Invest."""
from __future__ import annotations
import logging
from broker import orders as od
from broker import portfolio as pf

log = logging.getLogger("engine.reconcile")

async def ensure_stop(loop, size, avg):
    """Если у робота есть позиция, но нет активного стопа - поставить."""
    if size <= 0 or avg <= 0:
        return
    if loop.stop_order_id:
        try:
            active = await od.get_stop_orders(loop.c, loop.account_id)
            ids = [x.get("stopOrderId", "") for x in active]
            if loop.stop_order_id in ids:
                return
            log.warning("[robot-%s] stop %s not active, re-placing", loop.rid, loop.stop_order_id)
            loop.stop_order_id = None
        except Exception as e:
            log.warning("[robot-%s] stop check failed: %s", loop.rid, str(e)[:120])
    sp = avg * (1 - loop.stop_loss)
    try:
        r = await od.post_stop_order(loop.c, loop.account_id, loop.figi, size, round(sp, 2))
        loop.stop_order_id = r.order_id
        log.info("[robot-%s] stop re-placed @ %s qty=%s", loop.rid, round(sp, 2), size)
    except Exception as e:
        log.error("[robot-%s] stop place failed: %s", loop.rid, str(e)[:120])