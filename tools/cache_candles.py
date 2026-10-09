# -*- coding: utf-8 -*-
from __future__ import annotations
import json,pathlib,sqlite3,sys
R=pathlib.Path(__file__).resolve().parent.parent
if str(R) not in sys.path:
    sys.path.insert(0,str(R))
from backtest.data import load_candles_sync
DB=R/"data"/"robot.db"
def schema(c):
    c.execute("CREATE TABLE IF NOT EXISTS candles (ticker TEXT, ts TEXT, o REAL, h REAL, l REAL, c REAL, v INTEGER, PRIMARY KEY(ticker,ts))")
    c.commit()
def main():
    toks=json.loads((R/"data"/"tickers_tqbr.json").read_text(encoding="utf-8"))
    conn=sqlite3.connect(str(DB))
    schema(conn)
    n=0; skip=0
    for tk in sorted(toks.keys()):
        cnt=conn.execute("SELECT COUNT(*) FROM candles WHERE ticker=?",(tk,)).fetchone()[0]
        if cnt>=100:
            skip+=1; continue
        fg=toks[tk]["figi"]
        try:
            cds=load_candles_sync(fg, days=730, timeframe="D1", mode="sandbox")
        except Exception:
            continue
        if not cds or len(cds)<30:
            continue
        rows=[(tk, c.time, c.open, c.high, c.low, c.close, int(c.volume or 0)) for c in cds]
        conn.executemany("INSERT OR REPLACE INTO candles VALUES (?,?,?,?,?,?,?)", rows)
        conn.commit()
        n+=1
        if n%20==0: print("  cached", n, flush=True)
    print("done new=",n," skip=",skip)
    conn.close()
if __name__=="__main__":
    main()