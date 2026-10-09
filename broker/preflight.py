# -*- coding: utf-8 -*-
from __future__ import annotations
import logging
from broker.client import TInvestClient
log = logging.getLogger("broker.preflight")

async def check_real(c: TInvestClient, figi: str, ticker: str, use_limit: bool = False) -> tuple[bool, str]:
    try:
        r = await c.call("InstrumentsService/GetTradingStatus", {"figi": figi})
    except Exception as e:
        return False, "GetTradingStatus failed: " + str(e)[:120]
    api = bool(r.get("apiTradeAvailableFlag", False))
    mo = bool(r.get("marketOrderAvailableFlag", False))
    lo = bool(r.get("limitOrderAvailableFlag", False))
    if not api:
        return False, ticker + ": API trading not available"
    if use_limit and not lo:
        return False, ticker + ": limit orders not available"
    if not use_limit and not mo:
        return False, ticker + ": market orders not available"
    return True, ticker + ": OK (api="+str(api)+" mkt="+str(mo)+" lmt="+str(lo)+")"