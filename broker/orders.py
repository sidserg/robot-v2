# -*- coding: utf-8 -*-
"""orders.py - order operations."""
from __future__ import annotations
import uuid
from typing import Any, Optional
from broker.client import TInvestClient
from broker.models import Money, OrderResult

def _f(v):
    return Money.from_any(v).to_float()

def _money(val) -> dict:
    try:
        val = float(val)
    except Exception:
        return {"units": "0", "nano": 0}
    units = int(val)
    nano = int(round((val - units) * 1e9))
    if nano < 0:
        nano = 0
    return {"units": str(units), "nano": nano}

async def post_order(c: TInvestClient, account_id: str, figi: str, qty: float, direction: str, order_type: str = "ORDER_TYPE_MARKET", order_id: Optional[str] = None) -> OrderResult:
    if not order_id:
        order_id = str(uuid.uuid4())
    body = {"instrumentId": figi, "quantity": str(int(qty)), "direction": direction, "accountId": account_id, "orderType": order_type, "orderId": order_id}
    r = await c.call("OrdersService/PostOrder", body, retries=1)
    return OrderResult(order_id=r.get("orderId", order_id), status=r.get("executionReportStatus", ""), executed_qty=_f(r.get("lotsExecuted")), executed_price=_f(r.get("executedOrderPrice")), commission=_f(r.get("executedCommission")), raw=r)

async def post_stop_order(c: TInvestClient, account_id: str, figi: str, qty: float, stop_price: float, direction: str = "STOP_ORDER_DIRECTION_SELL") -> OrderResult:
    body = {"figi": figi, "quantity": str(int(qty)), "stopPrice": _money(stop_price), "direction": direction, "accountId": account_id, "stopOrderType": "STOP_ORDER_TYPE_TAKE_PROFIT", "expirationType": "STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL"}
    r = await c.call("StopOrdersService/PostStopOrder", body, retries=1)
    return OrderResult(order_id=r.get("stopOrderId", ""), status="STOP", raw=r)

async def cancel_stop_order(c: TInvestClient, account_id: str, stop_order_id: str) -> bool:
    if not stop_order_id or len(stop_order_id) < 30:
        return False
    try:
        await c.call("StopOrdersService/CancelStopOrder", {"accountId": account_id, "stopOrderId": stop_order_id}, retries=1)
        return True
    except Exception:
        return False

async def get_stop_orders(c: TInvestClient, account_id: str) -> list[dict]:
    r = await c.call("StopOrdersService/GetStopOrders", {"accountId": account_id})
    return r.get("stopOrders", [])

async def get_order_state(c: TInvestClient, account_id: str, order_id: str) -> dict:
    r = await c.call("OrdersService/GetOrderState", {"accountId": account_id, "orderId": order_id})
    return r