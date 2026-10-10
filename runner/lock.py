# -*- coding: utf-8 -*-
from __future__ import annotations
import os, pathlib, atexit
_LOCK_PATH = pathlib.Path(__file__).resolve().parent.parent / ".runner.lock"
_LOCK_HANDLE = None

def _release():
    global _LOCK_HANDLE
    try:
        if _LOCK_HANDLE:
            _LOCK_HANDLE.close()
        if _LOCK_PATH.exists():
            _LOCK_PATH.unlink()
    except Exception:
        pass

def acquire():
    global _LOCK_HANDLE
    try:
        if _LOCK_PATH.exists():
            _txt = _LOCK_PATH.read_text(encoding="utf-8").strip()
            if _txt.isdigit():
                _old = int(_txt)
                try:
                    import psutil
                    if psutil.pid_exists(_old):
                        _p = psutil.Process(_old)
                        _cmd = " ".join(_p.cmdline() or [])
                        if "multi.py" in _cmd:
                            print("[lock] another runner is alive: pid=" + str(_old))
                            return False
                except Exception:
                    pass
        _fd = os.open(str(_LOCK_PATH), os.O_CREAT | os.O_RDWR | os.O_TRUNC)
        _LOCK_HANDLE = os.fdopen(_fd, "w")
        _LOCK_HANDLE.write(str(os.getpid()))
        _LOCK_HANDLE.flush()
        atexit.register(_release)
        return True
    except Exception as e:
        print("[lock] acquire failed: " + str(e))
        return True