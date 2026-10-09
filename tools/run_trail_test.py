from __future__ import annotations
import pathlib,sys
R=pathlib.Path(__file__).resolve().parent.parent
if str(R) not in sys.path:
    sys.path.insert(0, str(R))
from backtest.data import load_candles_sync
from backtest.engine import run_backtest
from strategies.sma import SMAStrategy
FIGIS=[("TATN","BBG004RVFFC0"),("GAZP","BBG004730RP0"),("TATNP","BBG004S68829"),("VTBR","BBG004730ZJ9")]
def main():
    print("ticker  FIX5%   TRAIL3%  TRAIL5%  best")
    for tk,fg in FIGIS:
        try:
            candles=load_candles_sync(fg, days=730, timeframe="D1", mode="sandbox")
        except Exception as e:
            print(tk,"ERR"); continue
        sp={"fast":5,"slow":20}
        f=run_backtest(SMAStrategy(sp), candles, qty_limit=100, stop_loss=0.05, take_profit=0.15, trail_pct=0.0)
        t3=run_backtest(SMAStrategy(sp), candles, qty_limit=100, stop_loss=0.05, take_profit=0.15, trail_pct=0.03)
        t5=run_backtest(SMAStrategy(sp), candles, qty_limit=100, stop_loss=0.05, take_profit=0.15, trail_pct=0.05)
        arr=[("FIX",f.pnl_pct),("T3",t3.pnl_pct),("T5",t5.pnl_pct)]
        best=max(arr,key=lambda x:x[1])[0]
        print(tk.ljust(7), str(f.pnl_pct).ljust(7), str(t3.pnl_pct).ljust(8), str(t5.pnl_pct).ljust(8), best)
if __name__=="__main__":
    main()