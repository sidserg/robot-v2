# -*- coding: utf-8 -*-
from __future__ import annotations
import json, pathlib, sqlite3, sys, time
R=pathlib.Path(__file__).resolve().parent.parent
if str(R) not in sys.path:
    sys.path.insert(0, str(R))
from backtest.data import load_candles_sync
from backtest.engine import run_backtest
from strategies.sma import SMAStrategy
DB=R/"data"/"robot.db"
def _schema(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS mass_test (ticker TEXT PRIMARY KEY, days INTEGER, sma_pct REAL, bh_pct REAL, alpha REAL, trades INTEGER, ts TEXT)")
    conn.commit()
def main():
    toks=json.loads((R/"data"/"tickers_tqbr.json").read_text(encoding="utf-8"))
    conn=sqlite3.connect(str(DB))
    _schema(conn)
    ts=time.strftime("%Y-%m-%d %H:%M:%S")
    n=0
    for tk in sorted(toks.keys()):
        fg=toks[tk]["figi"]
        try:
            c=load_candles_sync(fg, days=730, timeframe="D1", mode="sandbox")
        except Exception:
            continue
        if not c or len(c)<30:
            continue
        m=run_backtest(SMAStrategy({"fast":5,"slow":20}), c, qty_limit=100, stop_loss=0.05, take_profit=0.15)
        px0=c[0].close; pxN=c[-1].close
        bh=(pxN-px0)/px0*100.0
        conn.execute("REPLACE INTO mass_test VALUES (?,?,?,?,?,?,?)", (tk, len(c), m.pnl_pct, bh, m.pnl_pct-bh, m.trades_total, ts))
        conn.commit()
        n+=1
        if n%10==0:
            print("  tested", n, flush=True)
    print("done", n)
    conn.close()
if __name__=="__main__":
    main()