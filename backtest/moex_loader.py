# -*- coding: utf-8 -*-
from __future__ import annotations
import urllib.request, json, time
from datetime import datetime, timedelta
from broker.models import Candle

def load_m1(ticker, from_date, till_date):
    url = chr(104)+chr(116)+chr(116)+chr(112)+chr(115)+chr(58)+chr(47)+chr(47)+chr(105)+chr(115)+chr(115)+chr(46)+chr(109)+chr(111)+chr(101)+chr(120)+chr(46)+chr(99)+chr(111)+chr(109)+chr(47)+chr(105)+chr(115)+chr(115)+chr(47)+chr(101)+chr(110)+chr(103)+chr(105)+chr(110)+chr(101)+chr(115)+chr(47)+chr(115)+chr(116)+chr(111)+chr(99)+chr(107)+chr(47)+chr(109)+chr(97)+chr(114)+chr(107)+chr(101)+chr(116)+chr(115)+chr(47)+chr(115)+chr(104)+chr(97)+chr(114)+chr(101)+chr(115)+chr(47)+chr(98)+chr(111)+chr(97)+chr(114)+chr(100)+chr(115)+chr(47)+chr(84)+chr(81)+chr(66)+chr(82)+chr(47)+chr(115)+chr(101)+chr(99)+chr(117)+chr(114)+chr(105)+chr(116)+chr(105)+chr(101)+chr(115)+chr(47)+ticker+chr(47)+chr(99)+chr(97)+chr(110)+chr(100)+chr(108)+chr(101)+chr(115)+chr(46)+chr(106)+chr(115)+chr(111)+chr(110)+chr(63)+chr(102)+chr(114)+chr(111)+chr(109)+chr(61)+from_date+chr(38)+chr(116)+chr(105)+chr(108)+chr(108)+chr(61)+till_date+chr(38)+chr(105)+chr(110)+chr(116)+chr(101)+chr(114)+chr(118)+chr(97)+chr(108)+chr(61)+chr(49)
    rows = []
    start = 0
    while True:
        _u = url + chr(38) + chr(115) + chr(116) + chr(97) + chr(114) + chr(116) + chr(61) + str(start)
        r = urllib.request.urlopen(_u, timeout=30).read().decode(chr(117)+chr(116)+chr(102)+chr(45)+chr(56))
        d = json.loads(r)
        _part = d.get(chr(99)+chr(97)+chr(110)+chr(100)+chr(108)+chr(101)+chr(115),{}).get(chr(100)+chr(97)+chr(116)+chr(97),[])
        if not _part:
            break
        rows.extend(_part)
        if len(_part) < 500:
            break
        start += 500
        time.sleep(0.3)
    out = []
    for x in rows:
        try:
            c = Candle(time=x[6], open=float(x[0]), high=float(x[2]), low=float(x[3]), close=float(x[1]), volume=int(x[5] or 0), is_complete=True)
            out.append(c)
        except Exception:
            continue
    return out

def aggregate_m1_to_m5(m1):
    out = []
    buf = []
    for c in m1:
        buf.append(c)
        if len(buf) == 5:
            o = buf[0].open
            h = max(x.high for x in buf)
            l = min(x.low for x in buf)
            cl = buf[-1].close
            v = sum(x.volume for x in buf)
            out.append(Candle(time=buf[0].time, open=o, high=h, low=l, close=cl, volume=v, is_complete=True))
            buf = []
    return out