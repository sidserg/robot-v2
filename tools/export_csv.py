# -*- coding: utf-8 -*-
from __future__ import annotations
import csv,sqlite3,pathlib,sys
R=pathlib.Path(__file__).resolve().parent.parent
DB=R/"data"/"robot.db"
OUT=R/"data"/"exports"

def main():
    OUT.mkdir(exist_ok=True,parents=True)
    c=sqlite3.connect(str(DB))
    c.row_factory=sqlite3.Row
    rows=c.execute("SELECT id,robot_id,ts,kind,ticker,figi,qty,price,total,commission,status,mode,strategy FROM trades ORDER BY id").fetchall()
    c.close()
    if not rows:
        print("no trades")
        return
    p=OUT/"trades_all.csv"
    with open(p,"w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f)
        w.writerow(["id","robot_id","ts","kind","ticker","figi","qty","price","total","commission","status","mode","strategy"])
        for r in rows:
            w.writerow([r[k] for k in r.keys()])
    print("exported:",p,len(rows),"rows")
    by_rid={}
    for r in rows:
        by_rid.setdefault(r["robot_id"],[]).append(r)
    for rid,items in by_rid.items():
        tk=items[-1]["ticker"] or str(rid)
        p2=OUT/("trades_"+str(rid)+"_"+str(tk)+".csv")
        with open(p2,"w",newline="",encoding="utf-8-sig") as f:
            w=csv.writer(f)
            w.writerow(["id","ts","kind","ticker","qty","price","total","commission","status"])
            for r in items:
                w.writerow([r["id"],r["ts"],r["kind"],r["ticker"],r["qty"],r["price"],r["total"],r["commission"],r["status"]])
        print("  per-robot:",p2,len(items),"rows")

if __name__=="__main__":
    main()