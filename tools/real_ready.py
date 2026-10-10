# -*- coding: utf-8 -*-
from __future__ import annotations
import json,sqlite3,subprocess,sys,pathlib
from datetime import datetime,timezone,timedelta
R=pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0,str(R))

def _cfg():
    return json.loads((R/"config.json").read_text(encoding="utf-8"))

def _log():
    p=R/"logs"/"robot.log"
    return p.read_text(encoding="utf-8",errors="replace") if p.exists() else ""

def check_armed():
    c=_cfg()
    if c.get("armed"):
        return False,"armed=true - real разблокирован"
    return True,"armed=false (защита ок)"

def check_config():
    try:
        c=_cfg()
        robots=c.get("robots",[])
        if not robots: return False,"robots пусто"
        for r in robots:
            if not r.get("figi") or not r.get("ticker") or not r.get("account_id"):
                return False,"robot без figi/ticker/account_id: "+str(r.get("id"))
        return True,str(len(robots))+" роботов, поля заполнены"
    except Exception as e:
        return False,"config error: "+str(e)[:100]

def check_db():
    p=R/"data"/"robot.db"
    if not p.exists(): return False,"robot.db не существует"
    sz=p.stat().st_size
    if sz<1024: return False,"robot.db слишком мал"
    return True,"robot.db: "+str(sz//1024)+" KB"
def check_tests():
    r=subprocess.run([sys.executable,"-m","pytest","tests/","-q","--no-header"],cwd=str(R),capture_output=True,text=True,timeout=180)
    out=(r.stdout or "")+(r.stderr or "")
    for l in out.splitlines():
        if "passed" in l: return True,l.strip()
    return False,"tests FAILED: "+out[-200:]
def check_log_errors():
    n=0
    for ln in _log().splitlines():
        if "[ERROR]" in ln: n+=1
    if n==0: return True,"0 ERROR в логе"
    if n<5: return True,str(n)+" ERROR (, приемлемо)"
    return False,str(n)+" ERROR - слишком много"

def check_stops():
    try:
        c=sqlite3.connect(str(R/"data"/"robot.db"))
        rows=dict(c.execute("SELECT robot_id, COALESCE(stop_order_id, '') FROM robot_state").fetchall())
        c.close()
    except Exception as e:
        return False,"db error: "+str(e)[:100]
    miss=[]
    for r in _cfg().get("robots",[]):
        rid=r.get("id")
        if not rows.get(rid): miss.append(str(rid)+" "+str(r.get("ticker")))
    if miss: return False,"нет стопа у: "+", ".join(miss)
    return True,"у всех роботов есть стоп"
def check_reconcile():
    n=0
    for ln in _log().splitlines():
        if "RECONCILED" in ln: n+=1
    if n==0: return True,"reconcile: расхождений нет"
    return True,"reconcile: "+str(n)+" восстановленных (не критично)"

def main():
    print("="*50)
    print("REAL READINESS CHECK")
    print("="*50)
    checks=[("armed",check_armed),("config",check_config),("db",check_db),("tests",check_tests),("stops",check_stops),("log_errors",check_log_errors),("reconcile",check_reconcile)]
    ok_all=True
    for name,fn in checks:
        try:
            ok,msg=fn()
            print(("[OK]   " if ok else "[FAIL] ")+name+": "+msg)
            if not ok: ok_all=False
        except Exception as e:
            print("[ERR]  "+name+": "+str(e)[:120])
            ok_all=False
    print("="*50)
    if ok_all:
        print("RESULT: ГОТОВ к real")
        return 0
    print("RESULT: НЕ готов - исправь FAIL")
    return 1

if __name__=="__main__":
    sys.exit(main())