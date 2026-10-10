# -*- coding: utf-8 -*-
import sys,pathlib
ROOT=pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))

import pytest
from broker.orders import post_order,post_stop_order

@pytest.mark.asyncio
async def test_post_order_rejects_zero_qty():
    with pytest.raises(ValueError):
        await post_order(None,chr(97)+chr(99)+chr(99),chr(102)+chr(105)+chr(103)+chr(105),0,chr(66)+chr(85)+chr(89))

@pytest.mark.asyncio
async def test_post_order_rejects_negative_qty():
    with pytest.raises(ValueError):
        await post_order(None,chr(97)+chr(99)+chr(99),chr(102)+chr(105)+chr(103)+chr(105),-5,chr(66)+chr(85)+chr(89))

@pytest.mark.asyncio
async def test_post_order_limit_requires_price():
    with pytest.raises(ValueError):
        await post_order(None,chr(97)+chr(99)+chr(99),chr(102)+chr(105)+chr(103)+chr(105),10,chr(66)+chr(85)+chr(89),order_type=chr(79)+chr(82)+chr(68)+chr(69)+chr(82)+chr(95)+chr(84)+chr(89)+chr(80)+chr(69)+chr(95)+chr(76)+chr(73)+chr(77)+chr(73)+chr(84),price=0)

@pytest.mark.asyncio
async def test_post_stop_rejects_zero_price():
    with pytest.raises(ValueError):
        await post_stop_order(None,chr(97)+chr(99)+chr(99),chr(102)+chr(105)+chr(103)+chr(105),10,0)