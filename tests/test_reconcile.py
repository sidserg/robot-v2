import pathlib,sys
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from broker.models import OrderResult
from engine import reconcile as rec
def _mk():
    l=MagicMock()
    l.stop_order_id=None
    l.stop_loss=0.05
    l.rid=1
    l.c=MagicMock()
    l.account_id="acc"
    l.figi="FIGI"
    l._round_price = lambda x: round(x, 2)
    return l
@pytest.mark.asyncio
async def test_no_pos():
    l=_mk()
    with patch("engine.reconcile.od.get_stop_orders", new=AsyncMock(return_value=[])):
        with patch("engine.reconcile.od.post_stop_order", new=AsyncMock()) as m:
            await rec.ensure_stop(l,0,0)
            m.assert_not_awaited()
@pytest.mark.asyncio
async def test_place():
    l=_mk()
    with patch("engine.reconcile.od.get_stop_orders", new=AsyncMock(return_value=[])):
        with patch("engine.reconcile.od.post_stop_order", new=AsyncMock(return_value=OrderResult(order_id="new", status="S"))):
            await rec.ensure_stop(l,10,100.0)
            assert l.stop_order_id=="new"
@pytest.mark.asyncio
async def test_keep():
    l=_mk()
    act=[{"stopOrderId": "k1", "figi": "FIGI", "stopPrice": {"units": "95", "nano": 0}}]
    with patch("engine.reconcile.od.get_stop_orders", new=AsyncMock(return_value=act)):
        with patch("engine.reconcile.od.post_stop_order", new=AsyncMock()) as m:
            await rec.ensure_stop(l,10,100.0)
            m.assert_not_awaited()
            assert l.stop_order_id=="k1"
@pytest.mark.asyncio
async def test_ops():
    l=_mk()
    with patch("engine.reconcile.pf.get_operations", new=AsyncMock(return_value=[])):
        n=await rec.reconcile_trades(l,60)
        assert n==0