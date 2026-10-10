# -*- coding: utf-8 -*-
from __future__ import annotations
import pathlib, subprocess, sys, time
R = pathlib.Path(__file__).resolve().parent.parent
TOKEN_FILE = pathlib.Path(r"C:\Users\cl\Desktop\token_gh.txt")
def run(cmd):
    r = subprocess.run(cmd, cwd=str(R), capture_output=True, text=True)
    return r.returncode, (r.stdout or r.stderr or "")
def main():
    msg = "auto-save "+time.strftime("%Y-%m-%d %H:%M")
    if len(sys.argv) > 1:
        msg = " ".join(sys.argv[1:])
    print("[1/3] git add")
    run(["git","add","-A"])
    print("[2/3] git commit")
    _mf = pathlib.Path(str(R)) / ".commit_msg"
    try:
        _mf.write_text(msg, encoding="utf-8")
        rc, out = run(["git","commit","-F", str(_mf)])
        _mf.unlink()
    except Exception:
        rc, out = run(["git","commit","-m", msg])
    if rc != 0 or "nothing to commit" in out:
        print("  no changes")
    else:
        first = out.strip().splitlines()[0] if out.strip() else "ok"
        print("  "+first)
    print("[3/3] git push")
    if not TOKEN_FILE.exists():
        print("  no token file")
        print("done (skip push)")
        return
    tok = TOKEN_FILE.read_text(encoding="utf-8-sig").strip()
    url = "https://"+tok+"@github.com/sidserg/robot-v2.git"
    rc, out = run(["git","push", url, "main"])
    if rc == 0:
        print("  pushed")
    else:
        print("  push err: "+out[-200:])
    print("done")
if __name__ == "__main__":
    main()