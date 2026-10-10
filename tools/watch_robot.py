# -*- coding: utf-8 -*-
from __future__ import annotations
import pathlib
import subprocess
import time
ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECK_SEC = 60
def _has_robot():
    try:
        r = subprocess.run(["wmic","process","where","name=python.exe","get","CommandLine"], capture_output=True, text=True, timeout=15)
        out = (r.stdout or "").lower()
        return "multi.py" in out
    except Exception:
        return True
def _spawn():
    c = "cd /d " + str(ROOT) + " && python runner\\multi.py"
    subprocess.Popen([chr(99)+chr(109)+chr(100), chr(47)+chr(107), c], cwd=str(ROOT), creationflags=subprocess.CREATE_NEW_CONSOLE)
def main():
    print(chr(91)+chr(119)+chr(93)+chr(32)+chr(115)+chr(116)+chr(97)+chr(114)+chr(116), flush=True)
    while True:
        try:
            if _has_robot():
                print(chr(91)+chr(119)+chr(93)+chr(32)+chr(111)+chr(107)+chr(32)+time.strftime(chr(37)+chr(72)+chr(58)+chr(37)+chr(77)+chr(58)+chr(37)+chr(83)), flush=True)
            else:
                print(chr(91)+chr(119)+chr(93)+chr(32)+chr(110)+chr(111)+chr(32)+chr(114)+chr(111)+chr(98)+chr(111)+chr(116), flush=True)
                time.sleep(5)
                _spawn()
                time.sleep(30)
        except Exception as e:
            print(chr(91)+chr(119)+chr(93)+chr(32)+chr(101)+chr(114)+chr(114)+chr(32)+str(e), flush=True)
        time.sleep(CHECK_SEC)
if __name__ == "__main__":
    main()