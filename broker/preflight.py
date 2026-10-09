# -*- coding: utf-8 -*-
from __future__ import annotations
import logging
from broker.client import TInvestClient
from broker import portfolio as _pf
log = logging.getLogger("broker.preflight")

async def check_real(c: TInvestClient, figi: str, ticker: str, use_limit: bool = False) -> tuple[bool, str]:
    try:
        r = await _pf.get_instrument(c, figi)
    except Exception as e:
        _m = str(e)
        if "404" in _m or "Unimplemented" in _m:
            return True, ticker + ": preflight skipped (sandbox)"
        return False, "GetInstrument failed: " + _m[:120]
    api = bool(r.get("apiTradeAvailableFlag", False))
    bs = bool(r.get("buyAvailableFlag", True))
    ss = bool(r.get("sellAvailableFlag", True))
    if not api:
        return False, ticker + ": API trading not available"
    if not bs:
        return False, ticker + ": buy not available"
    if not ss:
        return False, ticker + ": sell not available"
    return True, ticker + ": OK (api="+str(api)+" buy="+str(bs)+" sell="+str(ss)+")"