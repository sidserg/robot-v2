# -*- coding: utf-8 -*-
from __future__ import annotations
import json,pathlib,sqlite3,sys,time
R=pathlib.Path(__file__).resolve().parent.parent
if str(R) not in sys.path:
    sys.path.insert(0,str(R))
from broker.models import Candle
from backtest.engine import run_backtest
from strategies.sma import SMAStrategy
from strategies.grid import GridStrategy
from strategies.rsi import RSIStrategy
from strategies.bollinger import BollingerStrategy
from strategies.macd import MACDStrategy
DB=R/"data"/"robot.db"
VARIANTS=[("sma_5_20",lambda:SMAStrategy({"fast":5,"slow":20})),("sma_10_50",lambda:SMAStrategy({"fast":10,"slow":50})),("sma_5_20_tr3",lambda:SMAStrategy({"fast":5,"slow":20})),("grid_10",lambda:GridStrategy({"grid_levels":10,"corridor_days":60,"grid_lower_stop":0.05})),("rsi_14",lambda:RSIStrategy({"rsi_period":14,"rsi_low":30,"rsi_high":70})),("bb_20",lambda:BollingerStrategy({"bb_period":20,"bb_mult":2.0})),("macd",lambda:MACDStrategy({"macd_fast":12,"macd_slow":26,"macd_signal":9}))]
TRAIL={"sma_5_20_tr3":0.03}
def load(conn,tk):
    rs=conn.execute("SELECT ts,o,h,l,c,v FROM candles WHERE ticker=? ORDER BY ts",(tk,)).fetchall()
    return [Candle(time=r[0],open=r[1],high=r[2],low=r[3],close=r[4],volume=r[5]) for r in rs]
def main():
    conn=sqlite3.connect(str(DB))
    conn.execute("CREATE TABLE IF NOT EXISTS mass_test2 (ticker TEXT, variant TEXT, days INT, sma_pct REAL, bh_pct REAL, alpha REAL, trades INT, dd REAL, ts TEXT, PRIMARY KEY(ticker,variant))")
    conn.commit()
    toks=list(json.loads((R/"data"/"tickers_tqbr.json").read_text(encoding="utf-8")).keys())
    ts=time.strftime("%Y-%m-%d %H:%M:%S")
    n=0
    for tk in sorted(toks):
        cds=load(conn,tk)
        if len(cds)<60: continue
        bh=(cds[-1].close-cds[0].close)/cds[0].close*100.0
        for name,mk in VARIANTS:
            try:
                m=run_backtest(mk(),cds,qty_limit=100,stop_loss=0.05,take_profit=0.15,trail_pct=TRAIL.get(name,0.0))
            except Exception:
                continue
            conn.execute("REPLACE INTO mass_test2 VALUES (?,?,?,?,?,?,?,?,?)",(tk,name,len(cds),m.pnl_pct,bh,m.pnl_pct-bh,m.trades_total,m.max_drawdown_pct,ts))
        conn.commit()
        n+=1
        if n%20==0: print("  done",n,flush=True)
    print("total tickers:",n)
    conn.close()
if __name__=="__main__":
    main()