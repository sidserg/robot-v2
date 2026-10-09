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
if __name__=="__main__":
    main()