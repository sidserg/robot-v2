# -*- coding: utf-8 -*-
from __future__ import annotations
import pathlib,sys
_R = pathlib.Path(__file__).resolve().parent.parent
if str(_R) not in sys.path:
    sys.path.insert(0, str(_R))
from backtest.data import load_candles_sync
from backtest.limit_vs_market import compare
from strategies.sma import SMAStrategy
FIGIS = [("TATN","BBG004RVFFC0"),("GAZP","BBG004730RP0"),("TATNP","BBG004S68829"),("VTBR","BBG004730ZJ9")]
OFFS = [0.001, 0.002, 0.003, 0.005]
def run(tk, fg):
    try:
        candles = load_candles_sync(fg, days=180, timeframe="D1", mode="sandbox")
    except Exception as e:
        print(tk, "ERR", str(e)[:80]); return
    if not candles:
        print(tk, "no candles"); return
    sp = {"fast":5,"slow":20}
    m, _ = compare(candles, SMAStrategy(sp), qty=100, offset=0.001)
    parts = [tk, str(m.pnl_pct)]
    skips = []
    for off in OFFS:
        _, l = compare(candles, SMAStrategy(sp), qty=100, offset=off)
        parts.append(str(l.pnl_pct))
        skips.append(l.skipped)
    print(chr(9).join(parts), skips)
def main():
    print(chr(9).join(["ticker","mkt","0.1%","0.2%","0.3%","0.5%"]))
    for tk, fg in FIGIS:
        run(tk, fg)
if __name__ == "__main__":
    main()