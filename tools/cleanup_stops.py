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
from broker import orders as od
def _token():
    return (ROOT / "token.txt").read_text(encoding="utf-8-sig").strip()
def _accounts():
    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    accs = set()
    for r in cfg.get("robots", []):
        aid = r.get("account_id")
        if aid: accs.add(aid)
    return sorted(accs)
async def main():
    tok = _token()
    accs = _accounts()
    total = 0
    async with TInvestClient(tok, mode="sandbox") as c:
        for acc in accs:
            try:
                r = await od.get_stop_orders(c, acc)
            except Exception as e:
                print(acc[:8], "err", str(e)[:80]); continue
            if not r: continue
            by = {}
            for x in r:
                f = x.get("figi", "")
                by.setdefault(f, []).append(x.get("stopOrderId"))
            for f, ids in by.items():
                for extra in ids[1:]:
                    try:
                        await od.cancel_stop_order(c, acc, extra)
                        total += 1
                    except Exception:
                        pass
                if len(ids) > 1:
                    print(acc[:8], f, "cancelled", len(ids)-1)
    print("total cancelled:", total)
if __name__ == "__main__":
    asyncio.run(main())