# -*- coding: utf-8 -*-
"""client.py - httpx async client for T-Invest API."""
from __future__ import annotations
import asyncio
import logging
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
    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._client is not None:
            await self._client.aclose()
            self._client = None

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
                r = await self._client.post(url, json=body, headers=self._headers())
                if r.status_code >= 400:
                    log.error("HTTP %s %s", r.status_code, endpoint)
                    r.raise_for_status()
                return r.json()
            except Exception as e:
                last_exc = e
                if attempt < attempts - 1:
                    await asyncio.sleep(1 + attempt)
        raise last_exc if last_exc else RuntimeError("call failed")