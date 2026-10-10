# -*- coding: utf-8 -*-
from __future__ import annotations
import sys,pathlib,json
R=pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0,str(R))
from backtest.data import load_candles_sync
from backtest.engine import run_backtest
from strategies.sma import SMAStrategy
CFG=json.loads((R/"config.json").read_text(encoding="utf-8"))
T=json.loads((R/"data"/"tickers_tqbr.json").read_text(encoding="utf-8"))

def main():
    print("ticker   fix     trail5  trail3")
    for r in CFG.get("robots",[]):
        tk=r.get("ticker")
        if tk not in T: continue
        fg=T[tk]["figi"]
        p=r.get("params",{}) or {}
        fast=int(p.get("fast",5)); slow=int(p.get("slow",20))
        mode=p.get("signal_mode","cross")
        try: c=load_candles_sync(fg,days=730,timeframe="D1")
        except: continue
        if not c or len(c)<30: continue
        st={"fast":fast,"slow":slow,"signal_mode":mode}
        a=run_backtest(SMAStrategy(st),c,qty_limit=100,stop_loss=0.05,take_profit=0.15,slippage_pct=0.001).pnl_pct
        b=run_backtest(SMAStrategy(st),c,qty_limit=100,stop_loss=0.05,take_profit=0.15,trail_pct=0.05,slippage_pct=0.001).pnl_pct
        d=run_backtest(SMAStrategy(st),c,qty_limit=100,stop_loss=0.05,take_profit=0.15,trail_pct=0.03,slippage_pct=0.001).pnl_pct
        print(tk.ljust(7)+str(round(a,2)).ljust(8)+str(round(b,2)).ljust(8)+str(round(d,2)))

if __name__=="__main__":
    main()