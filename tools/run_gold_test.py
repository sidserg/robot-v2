from __future__ import annotations
import pathlib,sys
R=pathlib.Path(__file__).resolve().parent.parent
if str(R) not in sys.path:
    sys.path.insert(0, str(R))
from backtest.data import load_candles_sync
from backtest.engine import run_backtest
from strategies.sma import SMAStrategy
FIGIS=[("SBGD","TCSM44905385"),("TGLD","TCSM75801X50"),("AKGD","TCSM561045N8"),("TATN","BBG004RVFFC0"),("GAZP","BBG004730RP0"),("VTBR","BBG004730ZJ9")]
def main():
    print("ticker  days  SMA%    BuyHold%  delta")
    for tk,fg in FIGIS:
        try:
            candles=load_candles_sync(fg, days=730, timeframe="D1", mode="sandbox")
        except Exception as e:
            print(tk,"ERR",str(e)[:60]); continue
        if not candles or len(candles)<30:
            print(tk,"no candles"); continue
        sp={"fast":5,"slow":20}
        m=run_backtest(SMAStrategy(sp), candles, qty_limit=100, stop_loss=0.05, take_profit=0.15)
        px0=candles[0].close
        pxN=candles[-1].close
        bh=(pxN-px0)/px0*100.0
        print(tk.ljust(7), str(len(candles)).ljust(5), str(round(m.pnl_pct,2)).ljust(7), str(round(bh,2)).ljust(9), str(round(m.pnl_pct-bh,2)))
if __name__=="__main__":
    main()