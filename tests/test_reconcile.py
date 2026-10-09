# -*- coding: utf-8 -*-
"""test_reconcile.py - tests for engine/reconcile."""
import pathlib
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from broker.models import OrderResult
from engine import reconcile as rec


@pytest.mark.asyncio
async def test_ensure_stop_no_position():
    loop = MagicMock()
    loop.stop_order_id = None
    loop.stop_loss = 0.05
    loop.rid = 1
    loop.c = MagicMock()
    loop.account_id = "acc"
    loop.figi = "FIGI"
    with patch("engine.reconcile.od.post_stop_order", new=AsyncMock()) as m:
        await rec.ensure_stop(loop, 0, 0)
        m.assert_not_awaited()


@pytest.mark.asyncio
async def test_ensure_stop_places_when_missing():
    loop = MagicMock()
    loop.stop_order_id = None
    loop.stop_loss = 0.05
    loop.rid = 1
    loop.c = MagicMock()
    loop.account_id = "acc"
    loop.figi = "FIGI"
    with patch("engine.reconcile.od.post_stop_order", new=AsyncMock(return_value=OrderResult(order_id="new-id", status="STOP"))) as m:
        await rec.ensure_stop(loop, 10, 100.0)
        m.assert_awaited_once()
        assert loop.stop_order_id == "new-id"


@pytest.mark.asyncio
async def test_ensure_stop_keeps_active():
    loop = MagicMock()
    loop.stop_order_id = "existing"
    loop.stop_loss = 0.05
    loop.rid = 1
    loop.c = MagicMock()
    loop.account_id = "acc"
    loop.figi = "FIGI"
    with patch("engine.reconcile.od.get_stop_orders", new=AsyncMock(return_value=[{"stopOrderId": "existing"}])):
        with patch("engine.reconcile.od.post_stop_order", new=AsyncMock()) as m:
            await rec.ensure_stop(loop, 10, 100.0)
            m.assert_not_awaited()
            assert loop.stop_order_id == "existing"


@pytest.mark.asyncio
async def test_reconcile_trades_no_ops():
    loop = MagicMock()
    loop.rid = 1
    loop.figi = "FIGI"
    loop.c = MagicMock()
    loop.account_id = "acc"
    with patch("engine.reconcile.pf.get_operations", new=AsyncMock(return_value=[])):
        n = await rec.reconcile_trades(loop, window_min=60)
        assert n == 0