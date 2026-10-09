# -*- coding: utf-8 -*-
"""desktop.py - windows toast notifications (silent)."""
from __future__ import annotations
import logging
from typing import Any, Optional
log = logging.getLogger("notify.desktop")
_TOASTER = None
try:
    from windows_toasts import Toast, WindowsToaster
    _TOASTER = WindowsToaster("RobotV2")
except Exception as e:
    log.warning("windows-toasts unavailable: %s", e)
    _TOASTER = None

def notify(title: str, body: str) -> bool:
    if _TOASTER is None:
        return False
    try:
        t = Toast()
        t.text_fields = [str(title), str(body)]
        try:
            from windows_toasts import ToastAudio
            t.audio = ToastAudio(silent=True)
        except Exception:
            pass
        _TOASTER.show_toast(t)
        return True
    except Exception as e:
        log.warning("toast fail: %s", e)
        return False

def notify_trade(t: Any) -> bool:
    if not isinstance(t, dict):
        return False
    tk = str(t.get("ticker") or t.get("figi") or "?")
    side = str(t.get("kind") or t.get("side") or "").upper()
    qty = t.get("qty") or "?"
    price = t.get("price") or "?"
    status = str(t.get("status") or "")
    rid = t.get("robot_id", "?")
    return notify("[R{}] {} {}".format(rid, side, tk), "{} x {} [{}]".format(qty, price, status))

def notify_error(robot_id, msg):
    return notify("[R{}] ERROR".format(robot_id), str(msg)[:120])