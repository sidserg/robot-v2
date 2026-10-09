# -*- coding: utf-8 -*-
"""multi.py - запуск N роботов в одном asyncio-процессе."""
from __future__ import annotations
import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
if str(_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_ROOT))
import asyncio
import logging
import pathlib
import sys

from config import loader
from broker.client import TInvestClient
from engine.loop import RobotLoop


def setup_logging(cfg):
    log_file = cfg.get("log_file", "logs/robot.log")
    pathlib.Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, cfg.get("log_level", "INFO")),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def read_token(cfg):
    p = pathlib.Path(cfg.get("token_file", "token.txt"))
    if not p.exists():
        raise FileNotFoundError("token file not found: " + str(p))
    return p.read_text(encoding="utf-8-sig").strip()


async def run_all():
    cfg = loader.load()
    setup_logging(cfg)
    log = logging.getLogger("runner")

    token = read_token(cfg)
    robots_cfg = [r for r in cfg.get("robots", []) if r.get("enabled")]
    if not robots_cfg:
        log.warning("no enabled robots in config.json")
        return

    log.info("starting %d robots", len(robots_cfg))

    _modes = list(set([r.get("mode", "sandbox") for r in robots_cfg]))
    _mode = _modes[0] if _modes else "sandbox"
    async with TInvestClient(token, mode=_mode) as client:
        loops = [RobotLoop(cfg, r, client) for r in robots_cfg]
        tasks = [asyncio.create_task(lp.run(), name="robot-" + str(lp.rid)) for lp in loops]
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            log.info("cancelled, stopping robots")
            for t in tasks:
                t.cancel()


def main():
    try:
        asyncio.run(run_all())
    except KeyboardInterrupt:
        print("stopped by user")


if __name__ == "__main__":
    main()