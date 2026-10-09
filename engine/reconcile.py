# -*- coding: utf-8 -*-
from __future__ import annotations
import logging
from broker import orders as od
from broker import portfolio as pf

log = logging.getLogger("engine.reconcile")

def _px_of(stop):
    m = stop.get("stopPrice") or {}
    try:
        return float(m.get("units",0)) + float(m.get("nano",0))/1e9
    except Exception:
        return 0.0

async def ensure_stop(loop, size, avg):
    if size <= 0 or avg <= 0:
        return
    sp = round(avg * (1 - loop.stop_loss), 2)
    try:
        active = await od.get_stop_orders(loop.c, loop.account_id)
    except Exception as e:
        log.warning("[robot-%s] stop check failed: %s", loop.rid, str(e)[:120])
        return
    same_px = []
    all_figi = []
    for x in active:
        if x.get("figi") != loop.figi:
            continue
        _id = x.get("stopOrderId") or ""
        if not _id:
            continue
        all_figi.append(_id)
        _xp = _px_of(x)
        if _xp > 0 and sp > 0 and abs(_xp - sp) / sp < 0.02:
            same_px.append(_id)
    if same_px:
        keep = same_px[0]
        loop.stop_fail_count = 0
        loop.stop_order_id = keep
        try:
            from db import repo as _rp
            _rp.save_state(loop.rid, stop_order_id=keep)
        except Exception:
            pass
        extras = [x for x in all_figi if x != keep]
    elif all_figi:
        loop.stop_order_id = all_figi[0]
        try:
            from db import repo as _rp
            _rp.save_state(loop.rid, stop_order_id=all_figi[0])
        except Exception:
            pass
        extras = all_figi[1:]
    else:
        extras = []
    if all_figi:
        if extras:
            log.warning("[robot-%s] cancel %s extra stops", loop.rid, len(extras))
        for extra in extras:
            try:
                await od.cancel_stop_order(loop.c, loop.account_id, extra)
            except Exception:
                pass
        return
    try:
        r = await od.post_stop_order(loop.c, loop.account_id, loop.figi, size, sp)
        loop.stop_fail_count = 0
        loop.stop_order_id = r.order_id
        log.info("[robot-%s] stop placed @ %s qty=%s", loop.rid, sp, size)
    except Exception as e:
        _fc = int(getattr(loop, "stop_fail_count", 0) or 0) + 1
        loop.stop_fail_count = _fc
        log.error("[robot-%s] stop place failed (%s): %s", loop.rid, _fc, str(e)[:120])
        if _fc >= 3:
            try:
                from notify import desktop as _nd
                _nd.notify_error(loop.rid, "STOP MISSING x" + str(_fc))
            except Exception:
                pass

async def reconcile_trades(loop, window_min=60):
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
