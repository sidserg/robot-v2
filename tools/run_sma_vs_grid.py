from __future__ import annotations
import pathlib,sys
R=pathlib.Path(__file__).resolve().parent.parent
if str(R) not in sys.path:
    sys.path.insert(0, str(R))
from backtest.data import load_candles_sync
from backtest.engine import run_backtest
from strategies.sma import SMAStrategy
from strategies.grid import GridStrategy
FIGIS=[("GAZP","BBG004730RP0"),("VTBR","BBG004730ZJ9"),("TATN","BBG004RVFFC0"),("TATNP","BBG004S68829")]
def main():
    print("ticker  SMA%    Grid%   best")
    for tk,fg in FIGIS:
        try:
            candles=load_candles_sync(fg, days=365, timeframe="D1", mode="sandbox")
        except Exception as e:
            print(tk,"ERR"); continue
        if not candles or len(candles)<30:
            print(tk,"no candles"); continue
        m=run_backtest(SMAStrategy({"fast":5,"slow":20}), candles, qty_limit=100, stop_loss=0.05, take_profit=0.15)
        g=run_backtest(GridStrategy({"grid_levels":10,"corridor_days":60,"grid_lower_stop":0.05}), candles, qty_limit=100, stop_loss=0.05, take_profit=0.15)
        best = "SMA" if m.pnl_pct >= g.pnl_pct else "Grid"
        print(tk.ljust(7), str(m.pnl_pct).ljust(7), str(g.pnl_pct).ljust(7), best)
if __name__=="__main__":
    main()