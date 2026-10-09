# -*- coding: utf-8 -*-
from __future__ import annotations
import pathlib, os, sys
R = pathlib.Path(__file__).resolve().parent.parent
SRC = R / "start_all.bat"
if not SRC.exists():
    print("not found: ", SRC); sys.exit(1)
startup = pathlib.Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
startup.mkdir(parents=True, exist_ok=True)
dst = startup / "robotv2_autostart.bat"
import shutil
shutil.copyfile(str(SRC), str(dst))
print("installed: " + str(dst))
print("remove: del " + chr(34) + str(dst) + chr(34))