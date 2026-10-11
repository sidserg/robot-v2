# -*- coding: utf-8 -*-
from __future__ import annotations
from strategies.base import Strategy
from broker.models import Signal
from strategies import indicators as ind

class ADXRegimeStrategy(Strategy):
    name = chr(97)+chr(100)+chr(120)+chr(114)+chr(101)+chr(103)+chr(105)+chr(109)+chr(101)
    def signal(self, candles, position_qty, avg_price):
        p = self.params
        adx_period = int(p.get(chr(97)+chr(100)+chr(120)+chr(95)+chr(112)+chr(101)+chr(114)+chr(105)+chr(111)+chr(100), 14))
        adx_trend = float(p.get(chr(97)+chr(100)+chr(120)+chr(95)+chr(116)+chr(114)+chr(101)+chr(110)+chr(100), 25.0))
        adx_flat = float(p.get(chr(97)+chr(100)+chr(120)+chr(95)+chr(102)+chr(108)+chr(97)+chr(116), 20.0))
        fast = int(p.get(chr(102)+chr(97)+chr(115)+chr(116), 5))
        slow = int(p.get(chr(115)+chr(108)+chr(111)+chr(119), 20))
        bb_p = int(p.get(chr(98)+chr(98)+chr(95)+chr(112)+chr(101)+chr(114)+chr(105)+chr(111)+chr(100), 20))
        bb_m = float(p.get(chr(98)+chr(98)+chr(95)+chr(109)+chr(117)+chr(108)+chr(116), 2.0))
        rsi_p = int(p.get(chr(114)+chr(115)+chr(105)+chr(95)+chr(112)+chr(101)+chr(114)+chr(105)+chr(111)+chr(100), 14))
        closes=[c.close for c in candles]
        highs=[c.high for c in candles]
        lows=[c.low for c in candles]
        if len(closes) < max(slow, bb_p, adx_period*2) + 5:
            return Signal(action=chr(72)+chr(79)+chr(76)+chr(68), reason=chr(110)+chr(111)+chr(116)+chr(32)+chr(101)+chr(110)+chr(111)+chr(117)+chr(103)+chr(104))
        _adx = ind.adx(highs, lows, closes, adx_period)
        if _adx is None:
            return Signal(action=chr(72)+chr(79)+chr(76)+chr(68), reason=chr(97)+chr(100)+chr(120)+chr(32)+chr(78)+chr(111)+chr(110)+chr(101))
        if _adx >= adx_trend:
            _f = ind.sma(closes, fast)
            _s = ind.sma(closes, slow)
            _fp = ind.sma(closes[:-1], fast)
            _sp = ind.sma(closes[:-1], slow)
            if None in (_f,_s,_fp,_sp):
                return Signal(action=chr(72)+chr(79)+chr(76)+chr(68), reason=chr(115)+chr(109)+chr(97)+chr(32)+chr(78)+chr(111)+chr(110)+chr(101))
            if _f > _s and _fp <= _sp and position_qty <= 0:
                return Signal(action=chr(66)+chr(85)+chr(89), reason=chr(116)+chr(114)+chr(101)+chr(110)+chr(100)+chr(32)+chr(117)+chr(112))
            if _f < _s and _fp >= _sp and position_qty > 0:
                return Signal(action=chr(83)+chr(69)+chr(76)+chr(76), reason=chr(116)+chr(114)+chr(101)+chr(110)+chr(100)+chr(32)+chr(100)+chr(111)+chr(119)+chr(110))
            return Signal(action=chr(72)+chr(79)+chr(76)+chr(68), reason=chr(116)+chr(114)+chr(101)+chr(110)+chr(100)+chr(32)+chr(97)+chr(100)+chr(120)+str(round(_adx,1)))
        if _adx <= adx_flat:
            _lo, _mid, _hi = ind.bollinger(closes, bb_p, bb_m)
            if _lo is None:
                return Signal(action=chr(72)+chr(79)+chr(76)+chr(68), reason=chr(98)+chr(98)+chr(32)+chr(78)+chr(111)+chr(110)+chr(101))
            _r = ind.rsi(closes, rsi_p)
            if _r is None:
                return Signal(action=chr(72)+chr(79)+chr(76)+chr(68), reason=chr(114)+chr(115)+chr(105)+chr(32)+chr(78)+chr(111)+chr(110)+chr(101))
            _last = closes[-1]
            if _last <= _lo and _r < 30 and position_qty <= 0:
                return Signal(action=chr(66)+chr(85)+chr(89), reason=chr(102)+chr(108)+chr(97)+chr(116)+chr(32)+chr(98)+chr(98)+chr(32)+chr(114)+chr(115)+chr(105)+str(round(_r,1)))
            if _last >= _hi and _r > 70 and position_qty > 0:
                return Signal(action=chr(83)+chr(69)+chr(76)+chr(76), reason=chr(102)+chr(108)+chr(97)+chr(116)+chr(32)+chr(98)+chr(98)+chr(32)+chr(114)+chr(115)+chr(105)+str(round(_r,1)))
            return Signal(action=chr(72)+chr(79)+chr(76)+chr(68), reason=chr(102)+chr(108)+chr(97)+chr(116)+chr(32)+chr(97)+chr(100)+chr(120)+str(round(_adx,1)))
        return Signal(action=chr(72)+chr(79)+chr(76)+chr(68), reason=chr(109)+chr(105)+chr(100)+chr(32)+chr(97)+chr(100)+chr(120)+str(round(_adx,1)))