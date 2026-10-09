# -*- coding: utf-8 -*-
from __future__ import annotations
import json
import pathlib
import sqlite3
import time
ROOT = pathlib.Path(__file__).resolve().parent.parent
LOG = ROOT / "logs" / "robot.log"
STATE = ROOT / "logs" / ".pilot_state.json"
DB = ROOT / "data" / "robot.db"
CHECK_SEC = 60
SILENT_SEC = 180
STUCK_MIN = 10
DEDUP_SEC = 300

def _load():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _save(d):
    try:
        STATE.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

def _dedup(state, key):
    now = time.time()
    if now - state.get(key, 0) < DEDUP_SEC:
        return False
    state[key] = now
    return True

def _age():
    if not LOG.exists():
        return 10**9
    return time.time() - LOG.stat().st_mtime

def _notify(title, body):
    try:
        from notify.desktop import notify
        notify("Pilot: " + title, body)
    except Exception:
        pass
    print("[pilot] " + title + " - " + body, flush=True)

def _last(n):
    try:
        return LOG.read_text(encoding="utf-8", errors="replace").splitlines()[-n:]
    except Exception:
        return []

_last_px = {}

def _check_silent(state):
    _a = _age()
    if _a > SILENT_SEC:
        if _dedup(state, "sil"):
            _notify("log silent", "no changes for " + str(int(_a)) + "s")

def _check_price(state, lines):
    for x in lines:
        if ("[robot-" not in x) or ("px=" not in x):
            continue
        try:
            i0 = x.index("[robot-") + 7
            i1 = x.index("]", i0)
            rid = x[i0:i1]
            j0 = x.index("px=") + 3
            j1 = j0
            while j1 < len(x) and (x[j1].isdigit() or x[j1] == "."):
                j1 += 1
            px = float(x[j0:j1])
        except Exception:
            continue
        prev = _last_px.get(rid)
        if prev is not None and abs(prev - px) < 1e-9:
            k = "stuck_" + rid
            state[k] = state.get(k, 0) + 1
            if state[k] >= STUCK_MIN and _dedup(state, "n_" + k):
                _notify("price stuck", "robot " + rid + " px=" + str(px))
        else:
            state["stuck_" + rid] = 0
        _last_px[rid] = px

def _check_trade_errors(state):
    try:
        if not DB.exists():
            return
        c = sqlite3.connect(str(DB))
        pct = chr(37)
        q = "SELECT id, robot_id, ticker, status FROM trades WHERE status LIKE ? OR status LIKE ? ORDER BY id DESC LIMIT 50"
        rows = c.execute(q, (pct+"ERROR"+pct, pct+"REJECTED"+pct)).fetchall()
        c.close()
    except Exception:
        return
    seen = state.get("tr_err_seen", 0)
    mx = max([r[0] for r in rows], default=0)
    if mx > seen:
        for r in rows:
            if r[0] > seen:
                _notify("trade error", "R" + str(r[1]) + " " + str(r[2]) + " " + str(r[3]))
        state["tr_err_seen"] = mx

def _maybe_backup(state):
    now = time.time()
    last = state.get("last_backup", 0)
    if now - last < 86400:
        return
    try:
        import subprocess
        r = subprocess.run([__import__(chr(115)+chr(121)+chr(115)).executable, str(ROOT / chr(116)+chr(111)+chr(111)+chr(108)+chr(115) / (chr(98)+chr(97)+chr(99)+chr(107)+chr(117)+chr(112)+chr(95)+chr(100)+chr(98)+chr(46)+chr(112)+chr(121)))], capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            state["last_backup"] = now
            print(chr(91)+chr(112)+chr(105)+chr(108)+chr(111)+chr(116)+chr(93)+chr(32)+chr(98)+chr(97)+chr(99)+chr(107)+chr(117)+chr(112)+chr(32)+chr(111)+chr(107), flush=True)
    except Exception as e:
        print(chr(91)+chr(112)+chr(105)+chr(108)+chr(111)+chr(116)+chr(93)+chr(32)+chr(98)+chr(97)+chr(99)+chr(107)+chr(117)+chr(112)+chr(32)+chr(101)+chr(114)+chr(114)+chr(58), str(e), flush=True)

def main():
    print("[pilot] start " + str(ROOT), flush=True)
    state = _load()
    while True:
        try:
            lines = _last(50)
            _check_silent(state)
            _check_price(state, lines)
            _check_trade_errors(state)
            _maybe_backup(state)
            _save(state)
            print("[pilot] ok age=" + str(int(_age())) + "s", flush=True)
        except Exception as e:
            print("[pilot] err " + str(e), flush=True)
        time.sleep(CHECK_SEC)

if __name__ == "__main__":
    main()
