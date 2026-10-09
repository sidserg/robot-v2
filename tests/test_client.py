# -*- coding: utf-8 -*-
"""test_client.py - mock-тесты на TInvestClient."""
import pathlib
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from broker.client import TInvestClient


def test_sandbox_url_by_default():
    c = TInvestClient("tok", mode="sandbox")
    assert "sandbox" in c.base_url


def test_real_url_when_mode_real():
    c = TInvestClient("tok", mode="real")
    assert "sandbox" not in c.base_url
    assert "tbank.ru" in c.base_url or "tinkoff.ru" in c.base_url


def test_rate_limit_from_config():
    c = TInvestClient("tok")
    assert c.rate_limit == 200


@pytest.mark.asyncio
async def test_call_success():
    c = TInvestClient("tok")
    c._client = MagicMock()
    resp = MagicMock()
    resp.status_code = 200
    resp.json = MagicMock(return_value={"ok": True})
    c._client.post = AsyncMock(return_value=resp)
    r = await c.call("TestEndpoint", {})
    assert r == {"ok": True}
    c._client.post.assert_awaited_once()


@pytest.mark.asyncio
async def test_call_429_then_success():
    c = TInvestClient("tok", retries=3)
    c._client = MagicMock()
    r1 = MagicMock()
    r1.status_code = 429
    r1.headers = {"Retry-After": "0"}
    r2 = MagicMock()
    r2.status_code = 200
    r2.json = MagicMock(return_value={"ok": True})
    c._client.post = AsyncMock(side_effect=[r1, r2])
    result = await c.call("TestEndpoint", {})
    assert result == {"ok": True}
    assert c._client.post.await_count == 2


@pytest.mark.asyncio
async def test_call_400_raises():
    c = TInvestClient("tok", retries=1)
    c._client = MagicMock()
    r = MagicMock()
    r.status_code = 400
    r.text = "bad"
    r.raise_for_status = MagicMock(side_effect=Exception("400"))
    c._client.post = AsyncMock(return_value=r)
    with pytest.raises(Exception):
        await c.call("TestEndpoint", {})