# -*- coding: utf-8 -*-
from __future__ import annotations
import json, pathlib, sqlite3, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
PORT = 8771
DB = ROOT / "data" / "robot.db"
_LAST_ERR = ""
def _candles_from_api(ticker, tf, limit=200):
    try:
        import asyncio
        from datetime import datetime, timezone, timedelta
        from broker.client import TInvestClient
        from broker import portfolio as pf
        tok = (ROOT / "token.txt").read_text(encoding="utf-8-sig").strip()
        cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
        figi = ""
        for r in cfg.get("robots", []):
            if r.get("ticker") == ticker:
                figi = r.get("figi", "")
                break
        if not figi: return []
        _map = {"M1": "CANDLE_INTERVAL_1_MIN", "M5": "CANDLE_INTERVAL_5_MIN", "M15": "CANDLE_INTERVAL_15_MIN", "H1": "CANDLE_INTERVAL_HOUR"}
        iv = _map.get(tf, "CANDLE_INTERVAL_HOUR")
        days = 7 if tf != "M1" else 1
        async def _t():
            async with TInvestClient(tok, mode="sandbox") as c:
                to_dt = datetime.now(timezone.utc)
                fr_dt = to_dt - timedelta(days=days)
                return await pf.get_candles(c, figi, fr_dt.strftime("%Y-%m-%dT%H:%M:%SZ"), to_dt.strftime("%Y-%m-%dT%H:%M:%SZ"), iv)
        cds = asyncio.run(_t())
        out = []
        for c in cds:
            if not c.is_complete: continue
            out.append([c.time, c.open, c.high, c.low, c.close, int(c.volume or 0)])
        return out[-limit:]
    except Exception as e:
        import traceback
        global _LAST_ERR
        _LAST_ERR = traceback.format_exc()
        return []

def _candles(ticker, limit=180):
    try:
        c = sqlite3.connect(str(DB))
        rows = c.execute("SELECT ts,o,h,l,c,v FROM candles WHERE ticker=? ORDER BY ts DESC LIMIT ?", (ticker, limit)).fetchall()
        c.close()
        return list(reversed(rows))
    except Exception:
        return []
def _trades(ticker, limit=200):
    try:
        c = sqlite3.connect(str(DB))
        rows = c.execute("SELECT id,robot_id,ts,kind,qty,price FROM trades WHERE ticker=? AND status LIKE '%FILL%' ORDER BY id DESC LIMIT ?", (ticker, limit)).fetchall()
        c.close()
        return list(reversed(rows))
    except Exception:
        return []
def _state(rid):
    try:
        c = sqlite3.connect(str(DB))
        r = c.execute("SELECT stop_order_id FROM robot_state WHERE robot_id=?", (rid,)).fetchone()
        c.close()
        return (r[0] if r else "") or ""
    except Exception:
        return ""
def _robots():
    try:
        cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
        return [r for r in cfg.get("robots", []) if r.get("enabled")]
    except Exception:
        return []
class H(BaseHTTPRequestHandler):
    def _send(self, b, ctype):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)
    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            f = ROOT / "static" / "chart.html"
            self._send(f.read_bytes(), "text/html; charset=utf-8")
            return
        if self.path == "/static/chart.css":
            f = ROOT / "static" / "chart.css"
            self._send(f.read_bytes(), "text/css; charset=utf-8")
            return
        if self.path == "/static/js/chart.js":
            f = ROOT / "static" / "js" / "chart.js"
            self._send(f.read_bytes(), "application/javascript; charset=utf-8")
            return
        if self.path.startswith("/api"):
            pr = parse_qs(urlparse(self.path).query)
            if "robots" in pr:
                data = {"robots": [{"ticker": r.get("ticker"), "id": r.get("id")} for r in _robots()]}
            else:
                tk = (pr.get("ticker") or ["TATN"])[0]
                tf = (pr.get("tf") or ["D1"])[0]
                rid = 0
                for r in _robots():
                    if r.get("ticker") == tk:
                        rid = r.get("id") or 0
                        break
                _cd = _candles(tk) if tf == "D1" else _candles_from_api(tk, tf, 200)
                data = {"ticker": tk, "tf": tf, "candles": _cd, "trades": _trades(tk), "stop": _state(rid), "err": _LAST_ERR[-300:]}
            b = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self._send(b, "application/json; charset=utf-8")
            return
        self.send_response(404); self.end_headers()
    def log_message(self, *a): pass
def main():
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    print("Chart: http://127.0.0.1:" + str(PORT) + "/", flush=True)
    try: srv.serve_forever()
    except KeyboardInterrupt: pass
if __name__ == "__main__":
    main()