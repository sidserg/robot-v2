# -*- coding: utf-8 -*-
from __future__ import annotations
import pathlib
import subprocess
import sys
import time
ROOT = pathlib.Path(__file__).resolve().parent.parent
LOG = ROOT / (chr(108)+chr(111)+chr(103)+chr(115)) / (chr(114)+chr(111)+chr(98)+chr(111)+chr(116)+chr(46)+chr(108)+chr(111)+chr(103))
STALE_SEC = 240
CHECK_SEC = 60
TITLE = chr(114)+chr(111)+chr(98)+chr(111)+chr(116)+chr(118)+chr(50)
def _age():
    if not LOG.exists():
        return 10**9
    return time.time() - LOG.stat().st_mtime
def _kill():
    subprocess.run([chr(116)+chr(97)+chr(115)+chr(107)+chr(107)+chr(105)+chr(108)+chr(108),chr(47)+chr(70),chr(47)+chr(70)+chr(73),chr(87)+chr(73)+chr(78)+chr(68)+chr(79)+chr(87)+chr(84)+chr(73)+chr(84)+chr(76)+chr(69)+chr(32)+chr(101)+chr(113)+chr(32)+TITLE],capture_output=True)
def _spawn():
    cmd = chr(99)+chr(100)+chr(32)+chr(47)+chr(100)+chr(32) + str(ROOT) + chr(32)+chr(38)+chr(38)+chr(32)+chr(112)+chr(121)+chr(116)+chr(104)+chr(111)+chr(110)+chr(32)+chr(114)+chr(117)+chr(110)+chr(110)+chr(101)+chr(114)+chr(47)+chr(109)+chr(117)+chr(108)+chr(116)+chr(105)+chr(46)+chr(112)+chr(121)
    subprocess.Popen([chr(99)+chr(109)+chr(100),chr(47)+chr(107),cmd],cwd=str(ROOT),creationflags=subprocess.CREATE_NEW_CONSOLE)
def main():
    print(chr(91)+chr(119)+chr(93)+chr(32)+chr(115)+chr(116)+chr(97)+chr(114)+chr(116)+chr(32)+str(ROOT),flush=True)
    while True:
        try:
            a = _age()
            if a > STALE_SEC:
                print(chr(91)+chr(119)+chr(93)+chr(32)+chr(115)+chr(116)+chr(97)+chr(108)+chr(101)+chr(32)+str(int(a)),flush=True)
                _kill()
                time.sleep(2)
                _spawn()
                time.sleep(30)
            else:
                print(chr(91)+chr(119)+chr(93)+chr(32)+chr(111)+chr(107)+chr(32)+str(int(a)),flush=True)
        except Exception as e:
            print(chr(91)+chr(119)+chr(93)+chr(32)+chr(101)+chr(114)+chr(114)+chr(32)+str(e),flush=True)
        time.sleep(CHECK_SEC)
if __name__ == chr(95)+chr(95)+chr(109)+chr(97)+chr(105)+chr(110)+chr(95)+chr(95):
    main()
