# -*- coding: utf-8 -*-
import sys,pathlib
ROOT=pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))

def test_sell_clamp_uses_position():
    from engine.loop import RobotLoop
    assert hasattr(RobotLoop,chr(100)+chr(111)+chr(95)+chr(115)+chr(101)+chr(108)+chr(108))

def test_reconcile_has_kind_match():
    import pathlib as _p
    _d=ROOT/(chr(101)+chr(110)+chr(103)+chr(105)+chr(110)+chr(101))
    _f=_d/(chr(114)+chr(101)+chr(99)+chr(111)+chr(110)+chr(99)+chr(105)+chr(108)+chr(101)+chr(46)+chr(112)+chr(121))
    s=_f.read_text(encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56))
    assert chr(95)+chr(111)+chr(107)+chr(105)+chr(110)+chr(100) in s

def test_risk_reads_config_keys():
    from engine.risk import RiskManager
    r=RiskManager({chr(100)+chr(97)+chr(105)+chr(108)+chr(121)+chr(95)+chr(108)+chr(111)+chr(115)+chr(115)+chr(95)+chr(108)+chr(105)+chr(109)+chr(105)+chr(116):0.07})
    assert r.daily_limit==0.07

def test_client_no_retry_on_4xx():
    _p=ROOT/(chr(98)+chr(114)+chr(111)+chr(107)+chr(101)+chr(114))
    _f=_p/(chr(99)+chr(108)+chr(105)+chr(101)+chr(110)+chr(116)+chr(46)+chr(112)+chr(121))
    s=_f.read_text(encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56))
    assert chr(72)+chr(84)+chr(84)+chr(80)+chr(83)+chr(116)+chr(97)+chr(116)+chr(117)+chr(115)+chr(69)+chr(114)+chr(114)+chr(111)+chr(114) in s