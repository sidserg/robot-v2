# -*- coding: utf-8 -*-
"""client.py - httpx async client for T-Invest API."""
from __future__ import annotations
import asyncio
import logging
import time
from typing import Any, Optional
import httpx
from config import loader

log = logging.getLogger("broker.client")

class TInvestClient:
    def __init__(self, token, base_url=None, timeout=30.0, retries=3, mode=None):
        cfg = loader.load()
        ti = cfg.get("tinvest", {})
        self.token = token.strip()
        _SB = "https://sandbox-invest-public-api.tinkoff.ru/rest/tinkoff.public.invest.api.contract.v1"
        _RE = "https://invest-public-api.tbank.ru/rest/tinkoff.public.invest.api.contract.v1"
        _m = (mode or ti.get("mode", "sandbox"))
        _default = _SB if _m == "sandbox" else _RE
        self.base_url = (base_url or ti.get("base_url") or _default).rstrip("/").rstrip(".")
        self.timeout = float(timeout or ti.get("timeout_sec", 30))
        self.retries = int(retries or ti.get("retries", 3))
        self._client = None
        self.auth_failed = False
        self.rate_limit = int(ti.get("rate_limit_per_min", 200))
        self._last_call = None
    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _reset(self):
        try:
            if self._client is not None:
                await self._client.aclose()
        except Exception:
            pass
        self._client = httpx.AsyncClient(timeout=self.timeout)

    def _headers(self):
        return {"Authorization": "Bearer " + self.token, "Content-Type": "application/json"}
    async def call(self, endpoint, body=None, retries=None):
        if self._client is None:
            raise RuntimeError("client not opened")
        url = self.base_url + "." + endpoint.lstrip("/")
        body = body or {}
        attempts = self.retries if retries is None else int(retries)
        last_exc = None
        for attempt in range(attempts):
            try:
                await self._rate_wait()
                r = await self._client.post(url, json=body, headers=self._headers())
                if r.status_code == 429:
                    ra = r.headers.get("Retry-After", "5")
                    try: ra = int(ra)
                    except Exception: ra = 5
                    log.warning("429 rate limit, sleep %ss", ra)
                    await asyncio.sleep(ra)
                    continue
                if r.status_code >= 400:
                    _txt = r.text or ""
                    _auth = (r.status_code == 401) or ("40003" in _txt) or ("UNAUTHENTICATED" in _txt)
                    if _auth:
                        self.auth_failed = True
                        log.error("AUTH FAILED %s: %s", r.status_code, _txt[:200])
                    else:
                        if "30079" in _txt or "not available for trading" in _txt.lower():
                            log.info("HTTP %s %s (exchange closed): %s", r.status_code, endpoint, _txt[:120])
                        else:
                            log.error("HTTP %s %s text=%s", r.status_code, endpoint, _txt)
                    r.raise_for_status()
                return r.json()
            except Exception as e:
                last_exc = e
                _ename = type(e).__name__
                if _ename in ("ConnectError", "ReadError", "RemoteProtocolError", "ConnectTimeout", "PoolTimeout"):
                    log.warning("connection error %s, resetting client", _ename)
                    try:
                        await self._reset()
                    except Exception:
                        pass
                if attempt < attempts - 1:
                    await asyncio.sleep(2 + attempt * 2)
        raise last_exc if last_exc else RuntimeError("call failed")

    async def _rate_wait(self):
        # Простой rate-limit: не более rate_limit_per_min запросов в минуту
        if self._last_call is None:
            self._last_call = time.monotonic()
            return
        min_gap = 60.0 / max(1, self.rate_limit)
        elapsed = time.monotonic() - self._last_call
        if elapsed < min_gap:
            await asyncio.sleep(min_gap - elapsed)
        self._last_call = time.monotonic()