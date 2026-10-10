# -*- coding: utf-8 -*-
from __future__ import annotations
import sys, pathlib, json, csv
from datetime import date
sys.path.insert(0, str(pathlib.Path.cwd()))
from backtest.data import load_candles_sync
from strategies.sma import SMAStrategy

COMMISSION = 0.0005
SLIPPAGE = 0.001
START_CAP = 100000.0
QTY = 100.0
STOP = 0.05
TP = 0.15
def run_one(figi):
    cd = load_candles_sync(figi, days=300, timeframe="D1")
    start = date(2026, 1, 1)
    end = date(2026, 9, 30)
    cd = [x for x in cd if start <= date.fromisoformat(x.time[:10]) <= end]
    if len(cd) < 30:
        return None
    strat = SMAStrategy({"fast": 5, "slow": 20, "signal_mode": "slope"})
    cash = START_CAP
    qty = 0.0
    avg = 0.0
    cur_m = cd[0].time[:7]
    m_start = cash
    tr_m = 0
    total_tr = 0
    monthly = {}
    for i, c in enumerate(cd):
        px = c.close
        if qty > 0 and avg > 0:
            sl = avg * (1 - STOP)
            tp = avg * (1 + TP)
            if px <= sl or px >= tp:
                spx = px * (1 - SLIPPAGE)
                fee = spx * qty * COMMISSION
                cash += spx * qty - fee
                qty = 0.0
                avg = 0.0
                tr_m += 1
                total_tr += 1
        sig = strat.signal(cd[:i+1], qty, avg)
        if sig.action == "BUY" and qty <= 0:
            bpx = px * (1 + SLIPPAGE)
            cost = bpx * QTY
            fee = cost * COMMISSION
            if cash >= cost + fee:
                cash -= (cost + fee)
                qty = QTY
                avg = bpx
                tr_m += 1
                total_tr += 1
        elif sig.action == "SELL" and qty > 0:
            spx = px * (1 - SLIPPAGE)
            fee = spx * qty * COMMISSION
            cash += spx * qty - fee
            qty = 0.0
            avg = 0.0
            tr_m += 1
            total_tr += 1
        m = c.time[:7]
        if m != cur_m:
            eq = cash + qty * px
            ret = (eq - m_start) / m_start * 100.0
            monthly[cur_m] = round(ret, 2)
            cur_m = m
            m_start = eq
            tr_m = 0
    px = cd[-1].close
    eq = cash + qty * px
    ret = (eq - m_start) / m_start * 100.0
    monthly[cur_m] = round(ret, 2)
    total = (eq - START_CAP) / START_CAP * 100.0
    return {"monthly": monthly, "total": round(total, 2), "trades": total_tr, "candles": len(cd)}

def main():
    T = json.loads((pathlib.Path("data") / "tickers_tqbr.json").read_text(encoding="utf-8"))
    months = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07", "2026-08", "2026-09"]
    rows = []
    n = 0
    for tk in sorted(T.keys()):
        fg = T[tk].get("figi")
        if not fg:
            continue
        try:
            r = run_one(fg)
        except Exception:
            continue
        if r is None:
            continue
        row = {"ticker": tk, "total": r["total"], "trades": r["trades"], "candles": r["candles"]}
        for m in months:
            row[m] = r["monthly"].get(m, "")
        rows.append(row)
        n += 1
        if n % 20 == 0:
            print("tested", n, flush=True)
    rows.sort(key=lambda x: -x["total"])
    out = pathlib.Path("data") / "monthly_all.csv"
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["ticker", "total", "trades", "candles"] + months)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("saved:", out, "rows:", len(rows))
    print("TOP-20:")
    for r in rows[:20]:
        line = r["ticker"].ljust(7) + str(r["total"]).rjust(8) + str(r["trades"]).rjust(5)
        for m in months:
            v = r.get(m, "")
            line += str(v).rjust(8) if v != "" else "       -"
        print(line)

if __name__ == "__main__":
    main()