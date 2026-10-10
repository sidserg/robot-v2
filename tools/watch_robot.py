# -*- coding: utf-8 -*-
from __future__ import annotations
import os
import pathlib
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECK_SEC = 60
MY_PID = os.getpid()


def _pids_of_multi():
    try:
        r = subprocess.run(["wmic", "process", "where", "name=python.exe", "get", "ProcessId,CommandLine"], capture_output=True, text=True, timeout=15)
        out = r.stdout or ""
        pids = []
        for ln in out.splitlines():
            low = ln.lower()
            if "multi.py" in low and "watch" not in low:
                parts = ln.split()
                try:
                    pids.append(int(parts[-1]))
                except Exception:
                    pass
        return pids
    except Exception:
        return []


def _kill(pids):
    for p in pids:
        if p == MY_PID:
            continue
        try:
            subprocess.run(["taskkill", "/F", "/PID", str(p)], capture_output=True, timeout=10)
        except Exception:
            pass


def _spawn():
    cmd = "cd /d " + str(ROOT) + " && python runner\\multi.py"
    subprocess.Popen(["cmd", "/k", cmd], cwd=str(ROOT), creationflags=subprocess.CREATE_NEW_CONSOLE)


def main():
    print("[w] watchdog start pid=" + str(MYP_ID), flush=True)
    while True:
        try:
            pids = _pids_of_multi()
            n = len(pids)
            if n == 0:
                print("[w] no robot, restart", flush=True)
                time.sleep(3)
                _spawn()
                time.sleep(20)
            elif n > 1:
                print("[w] duplicates " + str(n) + ", keep first", flush=True)
                _kill(pids[1:])
                time.sleep(5)
            else:
                print("[w] ok " + time.strftime("%H:%M:%S"), flush=True)
        except Exception as e:
            print("[w] err " + str(e), flush=True)
        time.sleep(CHECK_SEC)


if __name__ == "__main__":
    main()
