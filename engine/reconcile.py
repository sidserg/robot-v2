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
    _rp = getattr(loop, "_round_price", None)
    sp = _rp(avg * (1 - loop.stop_loss)) if _rp else round(avg * (1 - loop.stop_loss), 2)
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
            loop._api_stop_price = sp
        except Exception:
            pass
        try:
            from db import repo as _rp
            _rp.save_state(loop.rid, stop_order_id=keep)
        except Exception:
            pass
        extras = [x for x in all_figi if x != keep]
    elif all_figi:
        loop.stop_order_id = all_figi[0]
        try:
            loop._api_stop_price = sp
        except Exception:
            pass
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
        try:
            loop._api_stop_price = sp
        except Exception:
            pass
        try:
            from db import repo as _rp2
            _rp2.save_state(loop.rid, stop_order_id=r.order_id)
        except Exception:
            pass
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

async def reconcile_trades(loop, window_min=1440):
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
        _ot = (o.get("operationType", "") or "").upper()
        if _ot not in ("OPERATION_TYPE_BUY","OPERATION_TYPE_SELL"):
            continue
        from datetime import datetime as _dt2
        def _pts(x):
            x=(x or "").strip().replace(" ","T").rstrip("Z")
            if len(x)>19: x=x[:19]
            try: return _dt2.fromisoformat(x)
            except Exception: return None
        _okind="BUY" if "BUY" in _ot else "SELL"
        _odt=_pts(o.get("date"))
        found = False
        for t in my:
            if (t.get("kind", "") or "").upper() != _okind: continue
            _tdt=_pts(t.get("ts"))
            if _tdt is None or _odt is None: continue
            _dd=abs((_tdt-_odt).total_seconds())
            if _dd < 180 or abs(_dd-10800) < 180:
                found = True
                break
        if not found:
            missing.append(o)
    if missing:
        _seen = set(getattr(loop, "_seen_missing_ops", set()) or set())
        _new = []
        for o in missing:
            _oid = str(o.get("id") or o.get("date") or "")
            if _oid and _oid not in _seen:
                _new.append(o)
                _seen.add(_oid)
        try:
            loop._seen_missing_ops = _seen
        except Exception:
            pass
        if _new:
            log.warning("[robot-%s] T-Invest sees %s new ops not in DB (total %s)", loop.rid, len(_new), len(missing))
            for o in _new:
                try:
                    _otp=(o.get("operationType") or "").upper()
                    _kind="BUY" if "BUY" in _otp else "SELL"
                    _date=(o.get("date") or "")[:19].replace("T"," ")
                    _q=int(o.get("quantity") or 0)
                    _pv=o.get("price") or {}
                    _px=0.0
                    if isinstance(_pv,dict):
                        _px=float(_pv.get("units",0))+float(_pv.get("nano",0))/1e9
                    elif _pv:
                        _px=float(_pv)
                    if _q<=0 or _px<=0: continue
                    rec={"robot_id":loop.rid,"ts":_date,"kind":_kind,"ticker":loop.ticker,"figi":o.get("figi") or "","qty":float(_q),"price":_px,"total":_q*_px,"commission":0.0,"order_id":str(o.get("id") or ""),"status":"RECONCILED","mode":loop.mode,"strategy":loop.strategy.name}
                    repo.add_trade(rec)
                    log.warning("[robot-%s] RECONCILED %s %s x %s @ %s", loop.rid, _kind, loop.ticker, _q, _px)
                except Exception as _e:
                    log.error("[robot-%s] reconcile add_trade: %s", loop.rid, str(_e)[:120])
        else:
            log.info("[robot-%s] %s ops not in DB (already alerted)", loop.rid, len(missing))
    return len(missing)
