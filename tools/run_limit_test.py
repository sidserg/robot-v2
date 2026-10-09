# -*- coding: utf-8 -*-
from __future__ import annotations
import pathlib,sys
_R = pathlib.Path(__file__).resolve().parent.parent
if str(_R) not in sys.path:
    sys.path.insert(0, str(_R))
from backtest.data import load_candles_sync
from backtest.limit_vs_market import compare
from strategies.sma import SMAStrategy

FIGIS = [
    ("TATN", "BBG004RVFFC0"),
    ("GAZP", "BBG004730RP0"),
    ("TATNP", "BBG004S68829"),
    ("VTBR", "BBG004730ZJ9"),
]

def main():
    print("ticker  market%  limit%  d_mkt  d_lmt  fills  skipped  dd_m  dd_l")
    for tk, fg in FIGIS:
        try:
            candles = load_candles_sync(fg, days=180, timeframe="D1", mode="sandbox")
        except Exception as e:
            print(tk, "ERR", str(e)[:80]); continue
        if not candles:
            print(tk, "no candles"); continue
        strat = SMAStrategy({"fast":5,"slow":20})
        m, l = compare(candles, strat, qty=100, stop_loss=0.05, tp=0.15, offset=0.002)
        print(tk, m.pnl_pct, l.pnl_pct, m.trades, l.trades, l.fills, l.skipped, m.dd, l.dd)

if __name__ == "__main__":
    main()
