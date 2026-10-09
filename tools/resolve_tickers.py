# -*- coding: utf-8 -*-
from __future__ import annotations
import asyncio
import json
import pathlib
import sys

R=pathlib.Path(__file__).resolve().parent.parent
if str(R) not in sys.path:
    sys.path.insert(0, str(R))

from broker.client import TInvestClient

def load_token():
    return (R/"token.txt").read_text(encoding="utf-8-sig").strip()

async def main():
    async with TInvestClient(load_token(), mode="sandbox") as c:
        body = {"instrumentStatus": "INSTRUMENT_STATUS_BASE"}
        r = await c.call("InstrumentsService/Shares", body)
        shares = r.get("instruments", [])
        tqbr = [x for x in shares if x.get("classCode") == "TQBR" and x.get("apiTradeAvailableFlag")]
        out = {}
        for x in tqbr:
            out[x["ticker"]] = {"figi": x["figi"], "name": x.get("name",""), "lot": int(x.get("lot",1) or 1)}
        p = R/"data"/"tickers_tqbr.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print("saved", len(out), "tickers")

asyncio.run(main())
