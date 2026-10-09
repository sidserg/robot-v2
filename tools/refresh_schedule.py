# -*- coding: utf-8 -*-
from __future__ import annotations
import asyncio
import json
import pathlib
import sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from broker.client import TInvestClient
def _tok():
    return (ROOT / "token.txt").read_text(encoding="utf-8-sig").strip()
async def main():
    async with TInvestClient(_tok(), mode="sandbox") as c:
        r = await c.call("InstrumentsService/TradingSchedules", {"exchange": "MOEX"})
        ex = r.get("exchanges", [])
        if not ex:
            print("no data"); return
        days = ex[0].get("days", [])
        out = {}
        for d in days:
            k = str(d.get("date", ""))[:10]
            out[k] = bool(d.get("isTradingDay", False))
        p = ROOT / "data" / "schedule.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print("saved", len(out), "days")
asyncio.run(main())