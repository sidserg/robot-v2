# -*- coding: utf-8 -*-
"""stop_all.py - graceful shutdown RobotV2."""
import sys
import time
try:
    import psutil
except ImportError:
    print("psutil not installed"); sys.exit(1)

KEYS = ["runner/multi.py", "runner\\multi.py", "runner/multi", "robot-v2"]

def find_ours():
    out = []
    for p in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            name = (p.info.get("name") or "").lower()
            if "python" not in name:
                continue
            cmd = " ".join(p.info.get("cmdline") or [])
            if "RobotV2" in cmd and ("multi.py" in cmd or "chart.py" in cmd):
                out.append((p.info["pid"], cmd))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return out

def kill(pid):
    try:
        p = psutil.Process(pid)
        p.terminate()
        try: p.wait(timeout=5)
        except psutil.TimeoutExpired: p.kill()
    except Exception:
        pass

def main():
    ours = find_ours()
    if not ours:
        print("no RobotV2 processes")
        return
    print("found", len(ours))
    for pid, cmd in ours:
        print("kill", pid, cmd[:80])
        kill(pid)
    time.sleep(2)
    left = find_ours()
    print("left:", len(left))

if __name__ == "__main__": main()