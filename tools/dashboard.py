# -*- coding: utf-8 -*-
"""dashboard.py - минимальный веб-дашборд RobotV2.

Читает SQLite, показывает позиции, сделки, статус.
Порт 8770. Не трогает торговлю.
"""
from __future__ import annotations
import asyncio
import json
import pathlib
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db import repo
from broker.client import TInvestClient
from broker import portfolio as pf
from config import loader

PORT = 8770

HTML = """<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<title>RobotV2</title>
<style>
body{background:#12161c;color:#e6ebf1;font-family:sans-serif;padding:20px;max-width:1200px;margin:0 auto}
h1{margin:0 0 16px} h2{margin:24px 0 12px;font-size:16px;color:#8892a0}
table{width:100%;border-collapse:collapse;font-size:14px;background:#1e2229;border-radius:8px;overflow:hidden}
th,td{padding:10px 12px;text-align:left;border-bottom:1px solid #2a2f38}
th{background:#252932;color:#8892a0;font-weight:normal;font-size:12px}
.buy{color:#22c55e} .sell{color:#ef4444}
.pnl-pos{color:#22c55e} .pnl-neg{color:#ef4444}
.info{color:#8892a0;font-size:13px;margin-top:8px}
.card{background:#1e2229;border-radius:10px;padding:14px 18px;margin-bottom:12px}
.refresh{color:#4a90d9;cursor:pointer;font-size:13px}
</style></head><body>
<h1>RobotV2 <span class="refresh" onclick="location.reload()">обновить</span></h1>
<div class="info">__TS__</div>
<h2>Роботы</h2><div id="robots"></div>
<h2>Позиции</h2><div id="positions"></div>
<h2>Последние сделки</h2><div id="trades"></div>
<script>
function fmt(n){return (n||0).toLocaleString('ru-RU',{maximumFractionDigits:2})}
function render(d){
  var rb='';
  if(!d.states||!d.states.length){rb='<div class="card">нет данных</div>'}
  else for(var i=0;i<d.states.length;i++){
    var s=d.states[i];
    rb+='<div class="card"><b>#'+s.robot_id+'</b> '+(s.running?'<span style="color:#22c55e">running</span>':'<span style="color:#ef4444">stopped</span>')+' <span class="info">last: '+s.last_ts+'</span></div>';
  }
  document.getElementById('robots').innerHTML=rb;
  var p='';
  if(!d.positions||!d.positions.length){p='<div class="card">пусто</div>'}
  else{
    p='<table><tr><th>Робот</th><th>Тикер</th><th>Кол-во</th><th>Ср. цена</th><th>Тек. цена</th><th>Стоимость</th><th>P&L</th></tr>';
    for(var j=0;j<d.positions.length;j++){
      var x=d.positions[j];
      var cls=x.yield>=0?'pnl-pos':'pnl-neg';
      p+='<tr><td>#'+x.robot_id+'</td><td>'+x.ticker+'</td><td>'+x.qty+'</td><td>'+fmt(x.avg)+'</td><td>'+fmt(x.price)+'</td><td>'+fmt(x.value)+' ₽</td><td class="'+cls+'">'+fmt(x.yield)+' ₽</td></tr>';
    }
    p+='</table>';
  }
  document.getElementById('positions').innerHTML=p;
  var t='';
  if(!d.trades||!d.trades.length){t='<div class="card">пусто</div>'}
  else{
    t='<table><tr><th>Время</th><th>Робот</th><th>Действие</th><th>Тикер</th><th>Кол-во</th><th>Цена</th><th>Статус</th></tr>';
    for(var k=d.trades.length-1;k>=0;k--){
      var tr=d.trades[k];
      var c=(tr.kind||'').toUpperCase().indexOf('BUY')>=0?'buy':'sell';
      t+='<tr><td>'+tr.ts+'</td><td>#'+tr.robot_id+'</td><td class="'+c+'">'+tr.kind+'</td><td>'+tr.ticker+'</td><td>'+tr.qty+'</td><td>'+fmt(tr.price)+'</td><td>'+tr.status+'</td></tr>';
    }
    t+='</table>';
  }
  document.getElementById('trades').innerHTML=t;
}
fetch('/api/state').then(function(r){return r.json();}).then(render);
setInterval(function(){fetch('/api/state').then(function(r){return r.json();}).then(render);},15000);
</script></body></html>
"""


def _read_token():
    cfg = loader.load()
    p = pathlib.Path(cfg.get("token_file", "token.txt"))
    return p.read_text(encoding="utf-8-sig").strip()


async def _collect():
    out = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "states": [], "positions": [], "trades": []}
    try:
        out["states"] = repo.list_states()
    except Exception:
        pass
    try:
        out["trades"] = repo.get_trades(limit=30)
    except Exception:
        pass

    cfg = loader.load()
    token = _read_token()
    robots = [r for r in cfg.get("robots", []) if r.get("enabled")]
    try:
        async with TInvestClient(token, mode=cfg.get("tinvest", {}).get("mode", "sandbox")) as c:
            for r in robots:
                aid = r.get("account_id")
                figi = r.get("figi")
                if not aid:
                    continue
                try:
                    p = await pf.get_portfolio(c, aid)
                except Exception:
                    continue
                for pos in p.positions:
                    if pos.figi == figi:
                        out["positions"].append({
                            "robot_id": r.get("id"),
                            "ticker": pos.ticker or r.get("ticker", ""),
                            "qty": pos.qty,
                            "avg": pos.avg_price,
                            "price": pos.current_price,
                            "value": pos.value,
                            "yield": pos.expected_yield,
                        })
    except Exception:
        pass
    return out


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/state"):
            data = asyncio.run(_collect())
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/" or self.path.startswith("/?"):
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            html = HTML.replace("__TS__", ts).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, *a):
        pass


def start_in_thread():
    import threading
    def _run():
        srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
        try:
            srv.serve_forever()
        except Exception:
            pass
    t = threading.Thread(target=_run, daemon=True, name="dashboard")
    t.start()
    print("Dashboard: http://127.0.0.1:" + str(PORT) + "/")
    return t


def main():
    start_in_thread()
    import time
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()