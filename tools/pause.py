# -*- coding: utf-8 -*-
from __future__ import annotations
import json
import pathlib
import sys
R = pathlib.Path(__file__).resolve().parent.parent
P = R / "data" / "paused.json"
def _load():
    try:
        return json.loads(P.read_text(encoding="utf-8"))
    except Exception:
        return {}
def _save(d):
    P.parent.mkdir(parents=True, exist_ok=True)
    P.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
def main():
    args = sys.argv[1:]
    if not args:
        d = _load()
        if not d:
            print("no paused robots")
        else:
            for k, v in sorted(d.items()):
                print(k, "PAUSED" if v else "running")
        return
    rid = str(args[0])
    d = _load()
    if "--resume" in args or "-r" in args:
        d[rid] = False
        print("resumed robot "+rid)
    elif "--pause" in args or "-p" in args:
        d[rid] = True
        print("paused robot "+rid)
    else:
        d[rid] = not bool(d.get(rid, False))
        print(rid, "-> "+("PAUSED" if d[rid] else "running"))
    _save(d)
if __name__ == "__main__":
    main()