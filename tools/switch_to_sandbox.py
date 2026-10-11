# -*- coding: utf-8 -*-
"""switch_to_sandbox.py - restore sandbox config."""
from __future__ import annotations
import pathlib, shutil, sys
R = pathlib.Path(__file__).resolve().parent.parent


def main():
    sandbox = R/chr(99)+chr(111)+chr(110)+chr(102)+chr(105)+chr(103)+chr(46)+chr(106)+chr(115)+chr(111)+chr(110)
    baks = sorted(sandbox.parent.glob(chr(99)+chr(111)+chr(110)+chr(102)+chr(105)+chr(103)+chr(46)+chr(106)+chr(115)+chr(111)+chr(110)+chr(46)+chr(98)+chr(97)+chr(107)+chr(95)+chr(42)), reverse=True)
    if not baks:
        print(chr(70)+chr(65)+chr(84)+chr(65)+chr(76)+chr(58)+chr(32)+chr(110)+chr(111)+chr(32)+chr(98)+chr(97)+chr(99)+chr(107)+chr(117)+chr(112)+chr(32)+chr(102)+chr(111)+chr(117)+chr(110)+chr(100));sys.exit(1)
    latest = baks[0]
    print(chr(82)+chr(101)+chr(115)+chr(116)+chr(111)+chr(114)+chr(101)+chr(32)+chr(102)+chr(114)+chr(111)+chr(109)+chr(58), latest.name)
    shutil.copyfile(str(latest), str(sandbox))
    print(chr(83)+chr(119)+chr(105)+chr(116)+chr(99)+chr(104)+chr(101)+chr(100)+chr(32)+chr(116)+chr(111)+chr(32)+chr(83)+chr(65)+chr(78)+chr(68)+chr(66)+chr(79)+chr(88))


if __name__ == chr(95)+chr(95)+chr(109)+chr(97)+chr(105)+chr(110)+chr(95)+chr(95):
    main()