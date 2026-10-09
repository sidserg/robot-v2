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

async def reconcile_trades(loop, window_min=60):
    """Сверяем operations T-Invest за окно с trades в БД. Возвращает число missing."""
    from datetime import datetime, timezone, timedelta
    from db import repo
    try:
        to_dt = datetime.now(timezone.utc)
        fr_dt = to_dt - timedelta(minutes=int(window_min))
        ops = await pf.get_operations(loop.c, loop.account_id, fr_dt.strftime("%Y-%m-%dT%H:%M:%SZ"), to_dt.strftime("%Y-%m-%dT%H:%M:%SZ"))
    except Exception as e:
        log.warning("[robot-%s] reconcile ops failed: %s", loop.rid, str(e)[:120])
        return 0
    my = repo.get_trades(limit=200, robot_id=loop.rid)
    missing = []
    for o in ops:
        if o.get("figi") != loop.figi:
            continue
        st = (o.get("state", "") or "").upper()
        if st != "OPERATION_STATE_EXECUTED":
            continue
        # сверяем по (figi, дата) - в T-Invest id операции != order_id
        odate = (o.get("date", "") or "")[:16]
        found = False
        for t in my:
            tdate = (t.get("ts", "") or "").replace(" ", "T")[:16]
            if tdate == odate:
                found = True
                break
        if not found:
            missing.append(o)
    if missing:
        log.warning("[robot-%s] T-Invest sees %s ops not in DB", loop.rid, len(missing))
    return len(missing)