# -*- coding: utf-8 -*-
from __future__ import annotations
import pathlib,sys,json,urllib.request
R = pathlib.Path(__file__).resolve().parent.parent
if str(R) not in sys.path:
    sys.path.insert(0, str(R))
from db import repo
def _cur_prices():
    try:
        r=json.loads(urllib.request.urlopen("http://127.0.0.1:8770/api/state",timeout=5).read().decode("utf-8"))
        return {int(p["robot_id"]): float(p.get("price") or 0) for p in r.get("positions", [])}
    except Exception:
        return {}
def _pnl_for(rid, cur_px):
    trades = repo.get_trades(limit=10000, robot_id=rid)
    if not trades:
        return None
    tk = trades[-1].get("ticker", "?")
    bq=0.0; bcost=0.0; sq=0.0; sp=0.0; comm=0.0; errs=0
    for t in trades:
        k=(t.get("kind") or "").upper()
        st=(t.get("status") or "").upper()
        if "ERROR" in st or "REJECTED" in st:
            errs+=1; continue
        qty=float(t.get("qty") or 0)
        px=float(t.get("price") or 0)
        c=float(t.get("commission") or 0)
        comm+=c
        if k=="BUY":
            bq+=qty; bcost+=qty*px
        elif k=="SELL":
            sq+=qty; sp+=qty*px
    open_q=bq-sq
    avg=bp=bcost/bq if bq>0 else 0.0
    realized=(sp - avg*sq - comm) if bq>0 else (sp - comm)
    unreal=open_q*(cur_px-avg) if (open_q>0 and cur_px>0 and avg>0) else 0.0
    return {"ticker":tk, "trades":len(trades), "open":open_q, "avg":avg, "cur":cur_px, "realized":realized, "unreal":unreal, "comm":comm, "errs":errs}
def main():
    cfg=json.load(open(str(R/"config.json"), encoding="utf-8"))
    prices=_cur_prices()
    print("id  ticker  trades  open   avg      cur      realized   unreal     comm    errs")
    tr=0.0; tu=0.0; tc=0.0
    for r in cfg.get("robots", []):
        rid=r.get("id")
        row=_pnl_for(rid, prices.get(rid,0))
        if row is None:
            print(rid, r.get("ticker"), "no trades"); continue
        tr+=row["realized"]; tu+=row["unreal"]; tc+=row["comm"]
        print(str(rid).ljust(4), row["ticker"].ljust(7), str(row["trades"]).ljust(7), str(row["open"]).ljust(7), str(round(row["avg"],2)).ljust(8), str(round(row["cur"],2)).ljust(8), str(round(row["realized"],2)).ljust(10), str(round(row["unreal"],2)).ljust(10), str(round(row["comm"],2)).ljust(7), row["errs"])
    print("---")
    print("TOTAL realized: ", round(tr,2), "  unrealized: ", round(tu,2), "  commissions: ", round(tc,2))
if __name__ == "__main__":
    main()