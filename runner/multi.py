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

async def _heartbeat_task(stop_ev, log, loops):
    _last = {}
    while not stop_ev.is_set():
        try:
            for lp in loops:
                _c = int(getattr(lp, "_tick_count", 0) or 0)
                _prev = _last.get(lp.rid, _c)
                if _c == _prev and _c > 0:
                    log.warning("heartbeat: robot-%s frozen at tick %s", lp.rid, _c)
                    try:
                        from notify import desktop as _nd
                        _nd.notify_error(lp.rid, "frozen tick")
                    except Exception:
                        pass
                _last[lp.rid] = _c
        except Exception as e:
            log.warning("heartbeat err: %s", str(e)[:100])
        try:
            await asyncio.wait_for(stop_ev.wait(), timeout=300)
        except asyncio.TimeoutError:
            pass

async def _cross_kill_task(stop_ev, log, cfg, token, mode, loops):
    from broker.client import TInvestClient as _C
    from broker import portfolio as _pf
    _window = 300
    _limit = float(cfg.get("cross_kill_pct", 0.05))
    _peak = 0.0
    _hist = []
    while not stop_ev.is_set():
        try:
            _tot = 0.0
            async with _C(token, mode=mode) as _cl:
                _seen = set()
                for lp in loops:
                    if lp.account_id in _seen:
                        continue
                    _seen.add(lp.account_id)
                    try:
                        p = await _pf.get_portfolio(_cl, lp.account_id)
                        _tot += float(p.total_value or 0)
                    except Exception:
                        pass
            if _tot > 0:
                _now = time.time()
                _hist.append((_now, _tot))
                _hist[:] = [(t,v) for t,v in _hist if _now - t <= _window]
                if _tot > _peak:
                    _peak = _tot
                if _peak > 0 and _limit > 0:
                    _drop = (_peak - _tot) / _peak
                    if _drop >= _limit:
                        log.error("CROSS-KILL: total equity drop %.2f%% > %.2f%%, halting all robots", _drop*100, _limit*100)
                        try:
                            from notify import desktop as _nd
                            _nd.notify_error(0, "CROSS-KILL %.2f%%" % (_drop*100))
                        except Exception:
                            pass
                        for lp in loops:
                            try:
                                lp.stop()
                            except Exception:
                                pass
                        stop_ev.set()
                        return
        except Exception as e:
            log.warning("cross-kill err: %s", str(e)[:100])
        try:
            await asyncio.wait_for(stop_ev.wait(), timeout=60)
        except asyncio.TimeoutError:
            pass

async def _schedule_refresh_task(stop_ev, log):
    import subprocess, sys
    _p = str(_ROOT / "tools" / "refresh_schedule.py")
    while not stop_ev.is_set():
        try:
            r = subprocess.run([sys.executable, _p], cwd=str(_ROOT), capture_output=True, text=True, timeout=60)
            if r.returncode == 0:
                log.info("schedule refreshed")
        except Exception as e:
            log.warning("schedule refresh err: %s", str(e)[:120])
        try:
            await asyncio.wait_for(stop_ev.wait(), timeout=21600)
        except asyncio.TimeoutError:
            pass

async def _backup_task(stop_ev, log):
    import subprocess,sys
    _p=str(_ROOT/"tools"/"backup_db.py")
    while not stop_ev.is_set():
        try:
            r=subprocess.run([sys.executable,_p],cwd=str(_ROOT),capture_output=True,text=True,timeout=60)
            if r.returncode==0:
                log.info("backup: "+((r.stdout or "").strip().splitlines()[0] if r.stdout else "ok"))
            else:
                log.warning("backup failed: "+((r.stderr or "")[:120]))
        except Exception as e:
            log.warning("backup err: "+str(e)[:120])
        try:
            await asyncio.wait_for(stop_ev.wait(),timeout=86400)
        except asyncio.TimeoutError:
            pass

async def _equity_task(stop_ev, log, loops):
    from broker import portfolio as _pf
    from db import repo as _rp
    while not stop_ev.is_set():
        try:
            _accs={}
            for lp in loops:
                if lp.account_id not in _accs:
                    _accs[lp.account_id]=[]
                _accs[lp.account_id].append(lp)
            for acc, lps in _accs.items():
                try:
                    p=await _pf.get_portfolio(lps[0].c, acc)
                    for lp in lps:
                        _pos=0.0
                        for pos in p.positions:
                            if pos.figi==lp.figi:
                                _pos=float(pos.value or 0)
                                break
                        _rp.add_equity(lp.rid, p.cash_rub, _pos, p.total_value)
                    log.info("equity recorded acc=%s robots=%s", acc[:8], len(lps))
                except Exception as _e:
                    log.warning("equity task: %s", str(_e)[:120])
        except Exception as e:
            log.warning("equity err: %s", str(e)[:120])
        try:
            await asyncio.wait_for(stop_ev.wait(), timeout=900)
        except asyncio.TimeoutError:
            pass

async def _daily_report_task(stop_ev, log):
    from datetime import datetime, timezone, timedelta
    MSK = timezone(timedelta(hours=3))
    last_date = None
    while not stop_ev.is_set():
        try:
            now = datetime.now(MSK)
            today = now.strftime("%Y-%m-%d")
            if now.hour >= 10 and last_date != today:
                import subprocess, sys
                _p = str(_ROOT / "tools" / "pnl.py")
                r = subprocess.run([sys.executable, _p], cwd=str(_ROOT), capture_output=True, text=True, timeout=60)
                out = (r.stdout or r.stderr or "").strip()
                log.info("DAILY REPORT:")
                for ln in out.splitlines():
                    log.info("  " + ln)
                try:
                    from notify import desktop as _nd
                    try:
                        from tools.daily import daily_summary
                        _ds = daily_summary()
                    except Exception:
                        _ds = ""
                    _msg = (out.splitlines()[-1] if out else "") + " | " + _ds
                    _nd.notify("RobotV2: daily report", _msg)
                except Exception:
                    pass
                last_date = today
        except Exception as e:
            log.warning("daily report err: %s", str(e)[:120])
        try:
            await asyncio.wait_for(stop_ev.wait(), timeout=1800)
        except asyncio.TimeoutError:
            pass
async def run_all():
    from runner import lock as _lock
    if not _lock.acquire():
        print("another runner already active, exiting")
        return
    try:
        from tools.validate_config import validate
        _cfg_probe=loader.load()
        _errs,_warns=validate(_cfg_probe)
        if _errs:
            print("[FATAL] config invalid:")
            for _e in _errs: print("  "+_e)
            return
        for _w in _warns: print("[WARN] "+_w)
    except Exception as _ve:
        print("[WARN] validate_config: "+str(_ve)[:120])
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
        try:
            _accs = await client.call("UsersService/GetAccounts", {})
            _n = len(_accs.get("accounts", []) or [])
            log.info("connection OK, accounts=%s", _n)
        except Exception as _ce:
            log.error("connection FAILED: %s", str(_ce)[:200])
            try:
                from notify import desktop as _nd
                _nd.notify_error(0, "connection failed: " + str(_ce)[:80])
            except Exception:
                pass
            return
        loops = [RobotLoop(cfg, r, client) for r in robots_cfg]
        tasks = [asyncio.create_task(lp.run(), name="robot-" + str(lp.rid)) for lp in loops]
        tasks.append(asyncio.create_task(_watchdog_task(stop_ev, log, log_path), name="watchdog"))
        tasks.append(asyncio.create_task(_pilot_task(stop_ev, log, db_path, log_path), name="pilot"))
        tasks.append(asyncio.create_task(_cross_kill_task(stop_ev, log, cfg, token, _mode, loops), name="cross_kill"))
        tasks.append(asyncio.create_task(_heartbeat_task(stop_ev, log, loops), name="heartbeat"))
        tasks.append(asyncio.create_task(_daily_report_task(stop_ev, log), name="daily_report"))
        tasks.append(asyncio.create_task(_equity_task(stop_ev, log, loops), name="equity"))
        tasks.append(asyncio.create_task(_schedule_refresh_task(stop_ev, log), name="schedule_refresh"))
        tasks.append(asyncio.create_task(_backup_task(stop_ev, log), name="backup"))
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