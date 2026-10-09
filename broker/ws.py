# -*- coding: utf-8 -*-
from __future__ import annotations
import asyncio
import json
import logging
from datetime import datetime, timezone
log = logging.getLogger("broker.ws")
class TInvestWS:
    def __init__(self, token, mode="sandbox"):
        self.token = token.strip()
        _SB = "wss://sandbox-invest-public-api.tinkoff.ru/ws/"
        _RE = "wss://invest-public-api.tbank.ru/ws/"
        self.url = _SB if mode == "sandbox" else _RE
        self.mode = mode
        self._ws = None
        self._stop = asyncio.Event()
        self._connected = False
        self._subs = {}  # figi -> interval
        self._on_candle = None
        self._task = None

    def set_on_candle(self, cb):
        self._on_candle = cb

    def is_connected(self):
        return self._connected

    async def _send_sub(self, figi, interval):
        msg = {"subscribeCandlesRequest": {"subscriptionAction": "SUBSCRIPTION_ACTION_SUBSCRIBE", "instruments": [{"figi": figi, "interval": interval}]}}
        await self._ws.send(json.dumps(msg))
        log.info("ws subscribe " + figi + " " + interval)

    async def _ping_loop(self):
        while not self._stop.is_set():
            try:
                await asyncio.sleep(50)
                if self._ws is None:
                    break
                _t = datetime.now(timezone.utc).isoformat()
                await self._ws.send(json.dumps({"ping": {"time": _t, "streamId": ""}}))
            except Exception:
                break

    async def _recv_loop(self):
        while not self._stop.is_set():
            try:
                raw = await self._ws.recv()
            except Exception as e:
                log.warning("ws recv err: %s", str(e)[:120])
                break
            try:
                data = json.loads(raw)
            except Exception:
                continue
            if "candle" in data and self._on_candle:
                try:
                    self._on_candle(data["candle"])
                except Exception as e:
                    log.warning("ws callback err: %s", str(e)[:120])

    async def _connect_once(self):
        import websockets
        headers = {"Authorization": "Bearer " + self.token}
        self._ws = await websockets.connect(self.url, additional_headers=headers, subprotocols=["json"], open_timeout=15, ping_interval=None)
        self._connected = True
        log.info("ws connected " + self.url)
        for figi, interval in list(self._subs.items()):
            try:
                await self._send_sub(figi, interval)
            except Exception:
                pass
        _pt = asyncio.create_task(self._ping_loop())
        try:
            await self._recv_loop()
        finally:
            _pt.cancel()
            self._connected = False
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None

    async def run_forever(self):
        backoff = [1, 5, 15, 30, 60]
        i = 0
        while not self._stop.is_set():
            try:
                await self._connect_once()
                i = 0
            except Exception as e:
                log.warning("ws connect fail: %s", str(e)[:120])
            if self._stop.is_set():
                break
            _d = backoff[min(i, len(backoff)-1)]
            i += 1
            log.info("ws reconnect in " + str(_d) + "s")
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=_d)
            except asyncio.TimeoutError:
                pass

    async def start(self, subs):
        self._subs = dict(subs)
        self._task = asyncio.create_task(self.run_forever(), name="ws")
        return self._task

    async def stop(self):
        self._stop.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except Exception:
                pass
