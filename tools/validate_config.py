# -*- coding: utf-8 -*-
from __future__ import annotations
import json,pathlib,sys,re
R=pathlib.Path(__file__).resolve().parent.parent
CFG=R/"config.json"

def _is_uuid(s):
    return bool(re.match(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", str(s).lower()))

def _is_figi(s):
    return bool(re.match(r"BBG[0-9A-Z]{9}$", str(s).upper()))

def _num(p,k,lo=None,hi=None):
    v=p.get(k)
    if v is None: return None,k+" missing"
    try: v=float(v)
    except: return None,k+" not num"
    if lo is not None and v<lo: return None,k+" too low"
    if hi is not None and v>hi: return None,k+" too high"
    return v,None
def validate(cfg):
    errs=[]
    warns=[]
    if not isinstance(cfg,dict): return ["config is not dict"],[]
    armed=bool(cfg.get("armed",False))
    robots=cfg.get("robots",[])
    if not isinstance(robots,list) or not robots: errs.append("robots empty")
    ids=set()
    pairs=set()
    for i,r in enumerate(robots):
        tag="robot["+str(i)+"]"
        rid=r.get("id")
        if rid is None: errs.append(tag+" no id")
        elif rid in ids: errs.append(tag+" duplicate id")
        else: ids.add(rid)
        figi=r.get("figi","")
        if not _is_figi(figi): errs.append(tag+" bad figi: "+str(figi))
        acc=r.get("account_id","")
        if not _is_uuid(acc): errs.append(tag+" bad account_id")
        if not r.get("ticker"): errs.append(tag+" no ticker")
        mode=r.get("mode","sandbox")
        if mode not in ("sandbox","real"): errs.append(tag+" bad mode: "+str(mode))
        if mode=="real" and not armed: warns.append(tag+" real without armed=true")
        key=(acc,figi)
        if key in pairs: errs.append(tag+" duplicate (acc,figi)")
        else: pairs.add(key)
        p = r.get("params", {}) or {}
        f = p.get("fast"); s = p.get("slow")
        if f is not None and s is not None:
            try:
                if int(f) >= int(s): errs.append(tag + " fast>=slow")
            except: errs.append(tag + " fast/slow not int")
        _, e = _num(p, "qty_limit", 1, None)
        if e: errs.append(tag + " qty_limit: " + e)
        _, e = _num(p, "stop_loss", 0.001, 0.5)
        if e: errs.append(tag + " stop_loss: " + e)
        _, e = _num(p, "take_profit", 0.001, 2.0)
        if e: errs.append(tag + " take_profit: " + e)
        _, e = _num(p, "max_position_rub", 1, None)
        if e: errs.append(tag + " max_position_rub: " + e)
        _, e = _num(p, "check_interval", 5, 3600)
        if e: errs.append(tag + " check_interval: " + e)
    return errs, warns
def main():
    try:
        cfg=json.loads(CFG.read_text(encoding="utf-8"))
    except Exception as e:
        print("[FAIL] cannot read config: "+str(e));sys.exit(2)
    errs,warns=validate(cfg)
    if warns:
        for w in warns: print("[WARN] "+w)
    if errs:
        for e in errs: print("[FAIL] "+e)
        print("RESULT: config INVALID ("+str(len(errs))+" errors)")
        sys.exit(1)
    print("RESULT: config OK ("+str(len(cfg.get("robots",[])))+" robots)")
    sys.exit(0)

if __name__=="__main__":
    main()