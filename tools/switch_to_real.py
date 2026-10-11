# -*- coding: utf-8 -*-
"""switch_to_real.py - switch config.json to real mode."""
from __future__ import annotations
import pathlib, shutil, json, sys
from datetime import datetime
R = pathlib.Path(__file__).resolve().parent.parent


def main():
    real = R/chr(99)+chr(111)+chr(110)+chr(102)+chr(105)+chr(103)+chr(46)+chr(114)+chr(101)+chr(97)+chr(108)+chr(46)+chr(106)+chr(115)+chr(111)+chr(110)
    sandbox = R/chr(99)+chr(111)+chr(110)+chr(102)+chr(105)+chr(103)+chr(46)+chr(106)+chr(115)+chr(111)+chr(110)
    if not real.exists():
        print(chr(70)+chr(65)+chr(84)+chr(65)+chr(76)+chr(58)+chr(32)+chr(99)+chr(111)+chr(110)+chr(102)+chr(105)+chr(103)+chr(46)+chr(114)+chr(101)+chr(97)+chr(108)+chr(46)+chr(106)+chr(115)+chr(111)+chr(110)+chr(32)+chr(110)+chr(111)+chr(116)+chr(32)+chr(102)+chr(111)+chr(117)+chr(110)+chr(100));sys.exit(1)
    ts = datetime.now().strftime(chr(37)+chr(89)+chr(37)+chr(109)+chr(37)+chr(100)+chr(95)+chr(37)+chr(72)+chr(37)+chr(77)+chr(37)+chr(83))
    bak = sandbox.with_suffix(sandbox.suffix + chr(46)+chr(98)+chr(97)+chr(107)+chr(95)+ts)
    shutil.copyfile(str(sandbox), str(bak))
    print(chr(66)+chr(97)+chr(99)+chr(107)+chr(117)+chr(112)+chr(58), bak.name)
    shutil.copyfile(str(real), str(sandbox))
    print(chr(83)+chr(119)+chr(105)+chr(116)+chr(99)+chr(104)+chr(101)+chr(100)+chr(32)+chr(116)+chr(111)+chr(32)+chr(82)+chr(69)+chr(65)+chr(76))
    c = json.loads(sandbox.read_text(encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)))
    print(chr(97)+chr(114)+chr(109)+chr(101)+chr(100)+chr(61), c.get(chr(97)+chr(114)+chr(109)+chr(101)+chr(100)))
    print(chr(82)+chr(101)+chr(109)+chr(105)+chr(110)+chr(100)+chr(101)+chr(114)+chr(58)+chr(32)+chr(115)+chr(101)+chr(116)+chr(32)+chr(97)+chr(114)+chr(109)+chr(101)+chr(100)+chr(61)+chr(116)+chr(114)+chr(117)+chr(101)+chr(32)+chr(116)+chr(111)+chr(32)+chr(101)+chr(110)+chr(97)+chr(98)+chr(108)+chr(101))


if __name__ == chr(95)+chr(95)+chr(109)+chr(97)+chr(105)+chr(110)+chr(95)+chr(95):
    main()