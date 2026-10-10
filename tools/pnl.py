# -*- coding: utf-8 -*-
from __future__ import annotations
import pathlib, sys, json, urllib.request
R = pathlib.Path(__file__).resolve().parent.parent
if str(R) not in sys.path:
    sys.path.insert(0, str(R))
from db import repo

def _cur_prices():
    try:
        r = json.loads(urllib.request.urlopen("http://127.0.0.1:8770/api/state", timeout=5).read().decode("utf-8"))
        return {int(p["robot_id"]): float(p.get("price") or 0) for p in r.get("positions", [])}
    except Exception:
        return {}

def _stats_for(rid, cur_px):
    trades = repo.get_trades(limit=10000, robot_id=rid)
    if not trades:
        return None
    tk = trades[-1].get("ticker", "?")
    qty_held = 0.0
    cost = 0.0
    comm = 0.0
    errs = 0
    closes = []
    for t in trades:
        k = (t.get("kind") or "").upper()
        st = (t.get("status") or "").upper()
        if "ERROR" in st or "REJECTED" in st:
            errs += 1
            continue
        q = float(t.get("qty") or 0)
        px = float(t.get("price") or 0)
        c = float(t.get("commission") or 0)
        comm += c
        if k == "BUY":
            qty_held += q
            cost += q * px
        elif k == "SELL":
            avg_buy = cost / qty_held if qty_held > 0 else 0.0
            realized_this = (px - avg_buy) * q - c
            closes.append(realized_this)
            cost -= avg_buy * q
            qty_held -= q
            if qty_held < 1e-9:
                qty_held = 0.0
                cost = 0.0
    open_q = qty_held
    avg = cost / open_q if open_q > 0 else 0.0
    realized = sum(closes)
    unreal = open_q * (cur_px - avg) if (open_q > 0 and cur_px > 0 and avg > 0) else 0.0
    wins = sum(1 for x in closes if x > 0)
    losses = sum(1 for x in closes if x < 0)
    n_closes = wins + losses
    winrate = (wins / n_closes * 100) if n_closes > 0 else 0.0
    avg_pnl = realized / n_closes if n_closes > 0 else 0.0
    return {"ticker": tk, "trades": len(trades), "open": open_q, "avg": avg, "cur": cur_px,
            "realized": realized, "unreal": unreal, "comm": comm, "errs": errs,
            "wins": wins, "losses": losses, "winrate": winrate, "n_closes": n_closes,
            "avg_pnl": avg_pnl}

def main():
    cfg = json.load(open(str(R / "config.json"), encoding="utf-8"))
    prices = _cur_prices()
    print("id  ticker  trades  open   avg      cur      realized   unreal     comm    wr%    W/L    avgPnL")
    tr = 0.0; tu = 0.0; tc = 0.0
    twins = 0; tlosses = 0
    for r in cfg.get("robots", []):
        rid = r.get("id")
        row = _stats_for(rid, prices.get(rid, 0))
        if row is None:
            print(rid, r.get("ticker"), "no trades")
            continue
        tr += row["realized"]; tu += row["unreal"]; tc += row["comm"]
        twins += row["wins"]; tlosses += row["losses"]
        wr = round(row["winrate"], 1)
        wl = str(row["wins"]) + "/" + str(row["losses"])
        print(str(rid).ljust(4), row["ticker"].ljust(7), str(row["trades"]).ljust(7),
              str(row["open"]).ljust(7), str(round(row["avg"], 2)).ljust(8),
              str(round(row["cur"], 2)).ljust(8), str(round(row["realized"], 2)).ljust(10),
              str(round(row["unreal"], 2)).ljust(10), str(round(row["comm"], 2)).ljust(7),
              str(wr).ljust(6), wl.ljust(6), round(row["avg_pnl"], 2))
    print("---")
    print("TOTAL realized:", round(tr, 2), " unrealized:", round(tu, 2), " commissions:", round(tc, 2))
    n_total = twins + tlosses
    if n_total > 0:
        print("Closed trades:", n_total, " wins:", twins, " losses:", tlosses,
              " winrate:", round(twins / n_total * 100, 1), "%")

if __name__ == "__main__":
    main()
