# -*- coding: utf-8 -*-
"""status.py - live status of all robots."""
from __future__ import annotations
import json, sqlite3, pathlib, sys
from datetime import datetime, timezone
R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R))

def _cfg():
    return json.loads((R/"config.json").read_text(encoding="utf-8"))

def _db():
    return sqlite3.connect(str(R/"data"/"robot.db"))

def _states(c):
    try:
        rows = c.execute("SELECT robot_id, running, last_ts, stop_order_id FROM robot_state").fetchall()
        return {r[0]: {"running": r[1], "last_ts": r[2], "stop": r[3]} for r in rows}
    except Exception:
        return {}

def _trades(c, rid, limit=5):
    try:
        return c.execute("SELECT ts,kind,ticker,qty,price,status FROM trades WHERE robot_id=? ORDER BY id DESC LIMIT ?", (rid, limit)).fetchall()
    except Exception:
        return []

def _log_errors():
    p = R/"logs"/"robot.log"
    if not p.exists():
        return 0, 0
    try:
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        total = len(lines)
        errs = sum(1 for l in lines if "[ERROR]" in l)
        return total, errs
    except Exception:
        return 0, 0
def main():
    cfg = _cfg()
    c = _db()
    st = _states(c)
    print("=" * 70)
    print("ROBOTV2 STATUS  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 70)
    for r in cfg.get("robots", []):
        rid = r.get("id")
        tk = r.get("ticker")
        p = r.get("params", {}) or {}
        s = st.get(rid, {})
        run = "RUN" if s.get("running") else "STOP"
        stop = (s.get("stop") or "")[:8]
        print("  [%s] R%d %-6s %-12s fast=%s slow=%s stop=%s trail=%s" % (run, rid, tk, r.get("strategy"), p.get("fast"), p.get("slow"), p.get("stop_loss"), p.get("trail_pct")))
        print("       last_ts=%s  stop_id=%s" % (s.get("last_ts"), stop))
        trs = _trades(c, rid, 3)
        for t in trs:
            print("         %s %-4s %s x%s @ %s [%s]" % (t[0], t[1], t[2], t[3], t[4], (t[5] or "")[:30]))
    c.close()
    total, errs = _log_errors()
    print("-" * 70)
    print("Log: %d lines, %d errors" % (total, errs))
    db = R/"data"/"robot.db"
    if db.exists():
        print("DB: %d KB" % (db.stat().st_size // 1024))
    print("=" * 70)

if __name__ == "__main__":
    main()