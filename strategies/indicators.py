# -*- coding: utf-8 -*-
"""indicators.py - pure numpy indicators (no numta)."""
from __future__ import annotations
import numpy as np

def _arr(v):
    return np.asarray(v, dtype=float)

def sma(values, period):
    a = _arr(values)
    if len(a) < period: return None
    return float(a[-period:].mean())

def slope(values, period):
    a = _arr(values)
    if len(a) < period + 1: return 0.0
    y = a[-period:]
    x = np.arange(period)
    m = float(np.polyfit(x, y, 1)[0])
    return m

def rsi(closes, period=14):
    a = _arr(closes)
    if len(a) < period + 1: return None
    d = np.diff(a)
    up = np.where(d > 0, d, 0.0)
    dn = np.where(d < 0, -d, 0.0)
    au = up[:period].mean()
    ad = dn[:period].mean()
    for i in range(period, len(d)):
        au = (au * (period - 1) + up[i]) / period
        ad = (ad * (period - 1) + dn[i]) / period
    if ad == 0: return 100.0
    rs = au / ad
    return float(100.0 - 100.0 / (1.0 + rs))

def atr(highs, lows, closes, period=14):
    h = _arr(highs); l = _arr(lows); c = _arr(closes)
    if len(c) < period + 1: return None
    tr = np.maximum(h[1:] - l[1:], np.maximum(np.abs(h[1:] - c[:-1]), np.abs(l[1:] - c[:-1])))
    a = tr[:period].mean()
    for i in range(period, len(tr)):
        a = (a * (period - 1) + tr[i]) / period
    return float(a)

def adx(highs, lows, closes, period=14):
    h = _arr(highs); l = _arr(lows); c = _arr(closes)
    n = len(c)
    if n < period * 2: return None
    pdm = np.where((h[1:] - h[:-1]) > (l[:-1] - l[1:]), np.maximum(h[1:] - h[:-1], 0.0), 0.0)
    ndm = np.where((l[:-1] - l[1:]) > (h[1:] - h[:-1]), np.maximum(l[:-1] - l[1:], 0.0), 0.0)
    tr = np.maximum(h[1:] - l[1:], np.maximum(np.abs(h[1:] - c[:-1]), np.abs(l[1:] - c[:-1])))
    atr_ = tr[:period].mean()
    ap = pdm[:period].mean()
    an = ndm[:period].mean()
    dxs = []
    for i in range(period, len(tr)):
        atr_ = (atr_ * (period - 1) + tr[i]) / period
        ap = (ap * (period - 1) + pdm[i]) / period
        an = (an * (period - 1) + ndm[i]) / period
        if atr_ == 0: continue
        pdi = 100.0 * ap / atr_
        ndi = 100.0 * an / atr_
        s = pdi + ndi
        if s == 0: continue
        dx = 100.0 * abs(pdi - ndi) / s
        dxs.append(dx)
    if not dxs: return None
    if len(dxs) < period: return float(np.mean(dxs))
    adx_ = np.mean(dxs[:period])
    for dx in dxs[period:]:
        adx_ = (adx_ * (period - 1) + dx) / period
    return float(adx_)

def bollinger(closes, period=20, mult=2.0):
    if len(closes) < period:
        return None, None, None
    window = closes[-period:]
    mid = sum(window) / period
    var = sum((x - mid) ** 2 for x in window) / period
    sd = var ** 0.5
    return mid - mult * sd, mid, mid + mult * sd

def ema(values, period):
    if len(values) < period:
        return None
    k = 2.0 / (period + 1)
    e = sum(values[:period]) / period
    for x in values[period:]:
        e = x * k + e * (1 - k)
    return e

def macd(closes, fast=12, slow=26, signal=9):
    if len(closes) < slow + signal:
        return None, None, None
    def _ema_series(vals, p):
        k = 2.0 / (p + 1)
        out = []
        e = sum(vals[:p]) / p
        out.append(e)
        for x in vals[p:]:
            e = x * k + e * (1 - k)
            out.append(e)
        return out
    ef = _ema_series(closes, fast)
    es = _ema_series(closes, slow)
    n = min(len(ef), len(es))
    macd_line = [ef[len(ef)-n+i] - es[len(es)-n+i] for i in range(n)]
    sig = _ema_series(macd_line, signal)
    return macd_line[-1], sig[-1], macd_line[-1] - sig[-1]
