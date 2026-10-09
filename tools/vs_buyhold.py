# -*- coding: utf-8 -*-
from __future__ import annotations
import pathlib,sys
R=pathlib.Path(__file__).resolve().parent.parent
if str(R) not in sys.path:
    sys.path.insert(0, str(R))
from backtest.data import load_candles_sync
from backtest.engine import run_backtest
from strategies.sma import SMAStrategy
FIGIS=[("TATN","BBG004RVFFC0"),("GAZP","BBG004730RP0"),("TATNP","BBG004S68829"),("VTBR","BBG004730ZJ9")]
def bh(candles, qty_limit=100):
    if not candles:
        return 0.0,0.0
    px0=candles[0].close
    pxN=candles[-1].close
    cost=px0*qty_limit
    final=pxN*qty_limit
    return (final-cost)/cost*100.0, px0, pxN
def main():
    print("ticker   days  SMA%    BuyHold%  delta   cand")
    for tk,fg in FIGIS:
        try:
            candles=load_candles_sync(fg, days=365, timeframe="D1", mode="sandbox")
        except Exception as e:
            print(tk,"ERR",str(e)[:80]); continue
        if not candles or len(candles)<30:
            print(tk,"no candles"); continue
        sp={"fast":5,"slow":20}
        m=run_backtest(SMAStrategy(sp), candles, qty_limit=100, stop_loss=0.05, take_profit=0.15)
        bhpct,_,_=bh(candles, 100)
        print(tk.ljust(7), str(len(candles)).ljust(5), str(round(m.pnl_pct,2)).ljust(7), str(round(bhpct,2)).ljust(9), str(round(m.pnl_pct-bhpct,2)).ljust(7), len(candles))
if __name__=="__main__":
    main()