# -*- coding: utf-8 -*-
"""spawn_silent.py - запуск роботов без окон."""
import sys
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOGS = ROOT / "logs"
PYW = str(pathlib.Path(sys.executable).parent / "pythonw.exe")

def main():
    LOGS.mkdir(exist_ok=True)
    out = open(str(LOGS / "runner.out.log"), "a", encoding="utf-8")
    subprocess.Popen([PYW, "runner/multi.py"], cwd=str(ROOT), stdout=out, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
    print("started runner (no window)")

if __name__ == "__main__": main()