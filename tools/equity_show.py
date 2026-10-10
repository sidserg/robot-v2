# -*- coding: utf-8 -*-
from __future__ import annotations
import sys, pathlib
R=pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R))
from db import repo

def main():
    import json
    cfg=json.loads((R/"config.json").read_text(encoding="utf-8"))
    days=int(sys.argv[1]) if len(sys.argv)>1 else 7
    print("robot ticker points min max last")
    for r in cfg.get("robots",[]):
        rid=r.get("id")
        tk=r.get("ticker","?")
        rows=repo.get_equity(rid, days=days)
        if not rows:
            print(str(rid)+"s "+tk+" 0 0 0 0")
            continue
        vals=[float(x.get("total") or 0) for x in rows]
        print(str(rid)+"s "+tk+" "+str(len(rows))+" "+str(round(min(vals)))+" "+str(round(max(vals)))+" "+str(round(vals[-1])))

if __name__=="__main__":
    main()
