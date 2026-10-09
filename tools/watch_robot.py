# -*- coding: utf-8 -*-
from __future__ import annotations
import pathlib
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECK_SEC = 60


def _count_robots():
    try:
        r = subprocess.run(["wmic", "process", "where", "name=python.exe", "get", "CommandLine"], capture_output=True, text=True, timeout=15)
        out = (r.stdout or "").lower()
        return out.count("multi.py")
    except Exception:
        return -1


def _kill_all():
    try:
        subprocess.run(["wmic", "process", "where", "name=python.exe", "call", "terminate"], capture_output=True, timeout=15)
    except Exception:
        pass


def _spawn():
    cmd = "cd /d " + str(ROOT) + " && python runner\\multi.py"
    subprocess.Popen(["cmd", "/k", cmd], cwd=str(ROOT), creationflags=subprocess.CREATE_NEW_CONSOLE)


def main():
    print("[w] watchrdog start " + str(ROOT), flush=True)
    while True:
        try:
            n = _count_robots()
            if n == 0:
                print("[w] no robot, restarting", flush=True)
                time.sleep(3)
                _spawn()
                time.sleep(20)
            elif n > 1:
                print("[w] duplicates " + str(n) + ", killing all", flush=True)
                _kill_all()
                time.sleep(5)
            else:
                print("[w] ok " + time.strftime("%H:%M:%S"), flush=True)
        except Exception as e:
            print("[w] err " + str(e), flush=True)
        time.sleep(CHECK_SEC)


if __name__ == "__main__":
    main()
