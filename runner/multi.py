# -*- coding: utf-8 -*-
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
import time
from config import loader
from broker.client import TInvestClient
from engine.loop import RobotLoop

def setup_logging(cfg):
    log_file = cfg.get("log_file", "logs/robot.log")
    pathlib.Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    from logging.handlers import RotatingFileHandler
    logging.basicConfig(level=getattr(logging, cfg.get("log_level", "INFO")), format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", handlers=[RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8"), logging.StreamHandler(sys.stdout)])
    logging.getLogger("httpx").setLevel(logging.WARNING)

def read_token(cfg):
    p = pathlib.Path(cfg.get("token_file", "token.txt"))
    if not p.exists():
        raise FileNotFoundError("token file not found: " + str(p))
    return p.read_text(encoding="utf-8-sig").strip()

async def _watchdog_task(stop_ev, log, log_path, stale_sec=240):
    while not stop_ev.is_set():
        try:
            age = time.time() - log_path.stat().st_mtime if log_path.exists() else 99999
            if age > stale_sec:
                log.warning("watchdog: log stale " + str(int(age)) + "s")
        except Exception as e:
            log.warning("watchdog err: %s", str(e)[:100])
        try:
            await asyncio.wait_for(stop_ev.wait(), timeout=60)
        except asyncio.TimeoutError:
            pass

async def _pilot_task(stop_ev, log, db_path, log_path):
    import json, sqlite3
    state_file = log_path.parent / ".pilot_state.json"
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception:
        state = {}
    last_px = {}
    while not stop_ev.is_set():
        try:
            try:
                age = time.time() - log_path.stat().st_mtime
                if age > 180:
                    _now = time.time()
                    if _now - state.get("sil",0) > 300:
                        log.warning("pilot: log silent " + str(int(age)) + "s")
                        state["sil"] = _now
            except Exception:
                pass
            try:
                if db_path.exists():
                    c = sqlite3.connect(str(db_path))
                    pct = chr(37)
                    rows = c.execute("SELECT id,robot_id,ticker,status FROM trades WHERE status LIKE ? OR status LIKE ? ORDER BY id DESC LIMIT 50",(pct+"ERROR"+pct,pct+"REJECTED"+pct)).fetchall()
                    c.close()
                    seen = state.get("tr_err_seen",0)
                    mx = max([r[0] for r in rows], default=0)
                    if mx > seen:
                        for r in rows:
                            if r[0] > seen:
                                log.warning("pilot: trade error R" + str(r[1]) + " " + str(r[2]) + " " + str(r[3]))
                        state["tr_err_seen"] = mx
            except Exception:
                pass
            state_file.write_text(json.dumps(state), encoding="utf-8")
        except Exception as e:
            log.warning("pilot err: %s", str(e)[:100])
        try:
            await asyncio.wait_for(stop_ev.wait(), timeout=60)
        except asyncio.TimeoutError:
            pass

async def run_all():
    cfg = loader.load()
    setup_logging(cfg)
    log = logging.getLogger("runner")
    token = read_token(cfg)
    robots_cfg = [r for r in cfg.get("robots", []) if r.get("enabled")]
    _armed = bool(cfg.get("armed", False))
    _real = [r for r in robots_cfg if r.get("mode") == "real"]
    if _real and not _armed:
        log.error("armed=false, %d real blocked", len(_real))
        robots_cfg = [r for r in robots_cfg if r.get("mode") != "real"]
    if not robots_cfg:
        log.warning("no enabled robots")
        return
    log.info("starting %d robots", len(robots_cfg))
    try:
        _sys.path.insert(0, str(_ROOT / "tools"))
        import dashboard
        dashboard.start_in_thread()
    except Exception as _de:
        log.warning("dashboard failed: %s", _de)
    _modes = list(set([r.get("mode", "sandbox") for r in robots_cfg]))
    _mode = _modes[0] if _modes else "sandbox"
    log_path = pathlib.Path(cfg.get("log_file", "logs/robot.log"))
    db_path = _ROOT / cfg.get("db_path", "data/robot.db")
    stop_ev = asyncio.Event()
    async with TInvestClient(token, mode=_mode) as client:
        loops = [RobotLoop(cfg, r, client) for r in robots_cfg]
        tasks = [asyncio.create_task(lp.run(), name="robot-" + str(lp.rid)) for lp in loops]
        tasks.append(asyncio.create_task(_watchdog_task(stop_ev, log, log_path), name="watchdog"))
        tasks.append(asyncio.create_task(_pilot_task(stop_ev, log, db_path, log_path), name="pilot"))
        try:
            await asyncio.gather(*tasks)
        except (asyncio.CancelledError, KeyboardInterrupt):
            log.info("shutdown: stopping %d robots", len(loops))
            stop_ev.set()
            for lp in loops:
                try:
                    lp.stop()
                except Exception:
                    pass
            _done, _pending = await asyncio.wait(tasks, timeout=10)
            for t in _pending:
                t.cancel()
            if _pending:
                await asyncio.gather(*_pending, return_exceptions=True)
            log.info("shutdown: done")

def main():
    try:
        asyncio.run(run_all())
    except KeyboardInterrupt:
        print("stopped by user")

if __name__ == "__main__":
    main()