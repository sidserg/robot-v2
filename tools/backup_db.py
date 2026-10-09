# -*- coding: utf-8 -*-
from __future__ import annotations
import pathlib,sqlite3,time,sys
R=pathlib.Path(__file__).resolve().parent.parent
SRC=R/"data"/"robot.db"
DST=R/"backups"
KEEP_DAYS=7
def main():
    if not SRC.exists():
        print("no db: ", SRC); sys.exit(1)
    DST.mkdir(exist_ok=True)
    ts=time.strftime("%Y%m%d_%H%M%S")
    dst=DST/("robot_"+ts+".db")
    src=sqlite3.connect(str(SRC))
    dstc=sqlite3.connect(str(dst))
    with dstc:
        src.backup(dstc)
    dstc.close(); src.close()
    size=dst.stat().st_size
    print("backup: "+str(dst)+" ("+str(size)+" bytes)")
    cut=time.time()-KEEP_DAYS*86400
    n=0
    for f in DST.glob("robot_*.db"):
        if f.stat().st_mtime < cut:
            f.unlink(); n+=1
    print("purged: "+str(n)+" old")
    _cfg = R / "config.json"
    if _cfg.exists():
        _cdst = DST / ("config_"+ts+".json")
        try:
            import shutil
            shutil.copyfile(str(_cfg), str(_cdst))
            print("config backup: "+str(_cdst))
        except Exception as _e:
            print("config backup err: "+str(_e)[:100])
        _cut = time.time() - KEEP_DAYS * 86400
        _n = 0
        for f in DST.glob("config_*.json"):
            if f.stat().st_mtime < _cut:
                f.unlink(); _n += 1
        if _n:
            print("config purged: "+str(_n))
if __name__=="__main__":
    main()