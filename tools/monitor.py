# -*- coding: utf-8 -*-
from __future__ import annotations
import json, os, pathlib, subprocess, sys, time, urllib.request
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
def _api():
    try:
        r = urllib.request.urlopen("http://127.0.0.1:8770/api/state", timeout=5)
        return json.loads(r.read().decode("utf-8"))
    except Exception:
        return {}
def _alive():
    try:
        import socket
        _s = socket.socket()
        _s.settimeout(2)
        _s.connect(("127.0.0.1", 8770))
        _s.close()
        return True
    except Exception:
        return False
def _render():
    os.system("cls" if os.name == "nt" else "clear")
    d = _api()
    st = d.get("states", [])
    pos = {p.get("robot_id"): p for p in d.get("positions", [])}
    stops = d.get("stops", {})
    paused = d.get("paused", {})
    print("=== RobotV2 MONITOR ===  " + str(d.get("ts","?")) + "  runner: " + ("OK" if _alive() else "NO RUNNER"))
    print()
    print("ID   TICKER   STATUS      QTY       AVG        CUR        YIELD      STOP")
    print("-"*80)
    for s0 in st:
        rid = s0.get("robot_id", 0)
        if rid == 0: continue
        p = pos.get(rid, {})
        tk = str(p.get("ticker","?")).ljust(8)
        qty = float(p.get("qty",0) or 0)
        avg = float(p.get("avg",0) or 0)
        cur = float(p.get("price",0) or 0)
        y = float(p.get("yield",0) or 0)
        stop = stops.get(str(rid), stops.get(rid, "")) or ""
        stop_t = (stop[:8]+"..") if stop else "MISSING"
        ps = "PAUSED" if paused.get(str(rid)) else ("running" if s0.get("running") else "stopped")
        print(str(rid).ljust(4), tk, ps.ljust(11), f"{qty:>7.1f}    {avg:>10.2f} {cur:>10.2f} {y:>10.2f} {stop_t:>10}")
    tr = d.get("trades", [])
    if tr:
        print();print("Recent trades:")
        for t in tr[-5:]:
            print(" " + str(t.get("ts","?")) + " R#" + str(t.get("robot_id")) + " " + str(t.get("kind")) + " " + str(t.get("ticker")) + " x" + str(t.get("qty")) + " @" + str(t.get("price")) + " " + str(t.get("status",""))[:20])
def main():
    iv = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    try:
        while True:
            _render()
            time.sleep(iv)
    except KeyboardInterrupt:
        pass
if __name__ == "__main__":
    main()