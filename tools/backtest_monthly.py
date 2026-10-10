# -*- coding: utf-8 -*-
from __future__ import annotations
import sys, pathlib
from datetime import date
sys.path.insert(0, str(pathlib.Path.cwd()))
from backtest.data import load_candles_sync
from strategies.sma import SMAStrategy
COMMISSION = 0.0005
SLIPPAGE = 0.001
START_CAP = 100000.0
QTY = 100.0
STOP = 0.05
TP = 0.15

def main():
    cd = load_candles_sync(chr(66)+chr(66)+chr(71)+chr(48)+chr(48)+chr(52)+chr(82)+chr(86)+chr(70)+chr(70)+chr(67)+chr(48), days=300, timeframe=chr(68)+chr(49))
    start = date(2026, 1, 1)
    end = date(2026, 9, 30)
    cd = [c for c in cd if start <= date.fromisoformat(c.time[:10]) <= end]
    if not cd:
        print(chr(110)+chr(111)+chr(32)+chr(100)+chr(97)+chr(116)+chr(97))
        return
    print(chr(99)+chr(97)+chr(110)+chr(100)+chr(108)+chr(101)+chr(115)+chr(61), len(cd))
    strat = SMAStrategy({chr(102)+chr(97)+chr(115)+chr(116): 5, chr(115)+chr(108)+chr(111)+chr(119): 20, chr(115)+chr(105)+chr(103)+chr(110)+chr(97)+chr(108)+chr(95)+chr(109)+chr(111)+chr(100)+chr(101): chr(115)+chr(108)+chr(111)+chr(112)+chr(101)})
    cash = START_CAP
    qty = 0.0
    avg = 0.0
    cur_m = cd[0].time[:7]
    m_start = cash
    tr_m = 0
    total_tr = 0
    print(chr(109)+chr(111)+chr(110)+chr(116)+chr(104)+chr(32)+chr(32)+chr(114)+chr(101)+chr(116)+chr(37)+chr(32)+chr(32)+chr(116)+chr(114)+chr(97)+chr(100)+chr(101)+chr(115)+chr(32)+chr(32)+chr(101)+chr(113)+chr(117)+chr(105)+chr(116)+chr(121))
    for i, c in enumerate(cd):
        px = c.close
        if qty > 0 and avg > 0:
            sl = avg * (1 - STOP)
            tp = avg * (1 + TP)
            if px <= sl or px >= tp:
                spx = px * (1 - SLIPPAGE)
                fee = spx * qty * COMMISSION
                cash += spx * qty - fee
                qty = 0.0; avg = 0.0; tr_m += 1; total_tr += 1
        sig = strat.signal(cd[:i+1], qty, avg)
        if sig.action == chr(66)+chr(85)+chr(89) and qty <= 0:
            bpx = px * (1 + SLIPPAGE)
            cost = bpx * QTY
            fee = cost * COMMISSION
            if cash >= cost + fee:
                cash -= (cost + fee)
                qty = QTY; avg = bpx; tr_m += 1; total_tr += 1
        elif sig.action == chr(83)+chr(69)+chr(76)+chr(76) and qty > 0:
            spx = px * (1 - SLIPPAGE)
            fee = spx * qty * COMMISSION
            cash += spx * qty - fee
            qty = 0.0; avg = 0.0; tr_m += 1; total_tr += 1
        m = c.time[:7]
        if m != cur_m:
            eq = cash + qty * px
            ret = (eq - m_start) / m_start * 100.0
            print(cur_m + chr(32) + format(ret, chr(43)+chr(46)+chr(50)+chr(102)) + chr(37) + chr(32) + str(tr_m) + chr(32) + str(int(eq)))
            cur_m = m
            m_start = eq
            tr_m = 0
    px = cd[-1].close
    eq = cash + qty * px
    ret = (eq - m_start) / m_start * 100.0
    print(cur_m + chr(32) + format(ret, chr(43)+chr(46)+chr(50)+chr(102)) + chr(37) + chr(32) + str(tr_m) + chr(32) + str(int(eq)))
    print(chr(45)+chr(45)+chr(45))
    tot = (eq - START_CAP) / START_CAP * 100.0
    print(chr(84)+chr(79)+chr(84)+chr(65)+chr(76) + chr(32) + str(int(eq)) + chr(32) + format(tot, chr(43)+chr(46)+chr(50)+chr(102)) + chr(37) + chr(32) + chr(116)+chr(114)+chr(97)+chr(100)+chr(101)+chr(115)+chr(61) + str(total_tr))

if __name__ == chr(95)+chr(95)+chr(109)+chr(97)+chr(105)+chr(110)+chr(95)+chr(95):
    main()