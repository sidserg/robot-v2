# -*- coding: utf-8 -*-
"""repo.py — SQLite-обёртка RobotV2."""
from __future__ import annotations
import json
import sqlite3
import pathlib
import threading
from typing import Any, Optional
from config import loader

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_lock = threading.RLock()
_DB_PATH = None

def db_path() -> pathlib.Path:
    global _DB_PATH
    if _DB_PATH is None:
        import os
        _env = os.environ.get("ROBOTV2_DB")
        if _env:
            _DB_PATH = pathlib.Path(_env)
        else:
            cfg = loader.load()
            _DB_PATH = _ROOT / cfg.get("db_path", "data/robot.db")
    return _DB_PATH

def _connect() -> sqlite3.Connection:
    p = db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p), timeout=10.0, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    schema = (_ROOT / "db" / "schema.sql").read_text(encoding="utf-8")
    with _lock:
        conn = _connect()
        try:
            conn.executescript(schema)
            from db import migrations
            migrations.apply_all(conn)
        finally:
            conn.close()

def add_trade(rec: dict[str, Any]) -> int:
    with _lock:
        conn = _connect()
        try:
            cur = conn.execute(
                "INSERT INTO trades (robot_id, ts, kind, ticker, figi, qty, price, total, commission, order_id, status, mode, strategy) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (int(rec.get("robot_id", 0)), rec.get("ts", ""), rec.get("kind", ""), rec.get("ticker", ""), rec.get("figi", ""), float(rec.get("qty", 0) or 0), float(rec.get("price", 0) or 0), float(rec.get("total", 0) or 0), float(rec.get("commission", 0) or 0), rec.get("order_id", ""), rec.get("status", ""), rec.get("mode", ""), rec.get("strategy", "")))
            return int(cur.lastrowid or 0)
        finally:
            conn.close()

def get_trades(limit: int = 100, robot_id: int | None = None) -> list[dict[str, Any]]:
    with _lock:
        conn = _connect()
        try:
            if robot_id is None:
                cur = conn.execute("SELECT * FROM trades ORDER BY id DESC LIMIT ?", (int(limit),))
            else:
                cur = conn.execute("SELECT * FROM trades WHERE robot_id=? ORDER BY id DESC LIMIT ?", (int(robot_id), int(limit)))
            rows = [dict(r) for r in cur.fetchall()]
            rows.reverse()
            return rows
        finally:
            conn.close()

def count_trades(robot_id: int | None = None) -> int:
    with _lock:
        conn = _connect()
        try:
            if robot_id is None:
                cur = conn.execute("SELECT COUNT(*) AS c FROM trades")
            else:
                cur = conn.execute("SELECT COUNT(*) AS c FROM trades WHERE robot_id=?", (int(robot_id),))
            return int(cur.fetchone()["c"])
        finally:
            conn.close()

def save_state(robot_id, running=None, last_ts=None, day_date=None, day_equity_start=None, day_stopped=None, peak_value=None, stop_order_id=None):
    with _lock:
        conn = _connect()
        try:
            cur = conn.execute("SELECT robot_id FROM robot_state WHERE robot_id=?", (int(robot_id),))
            row = cur.fetchone()
            if row is None:
                conn.execute("INSERT INTO robot_state (robot_id, running, last_ts, day_date, day_equity_start, day_stopped, peak_value, stop_order_id) VALUES (?,?,?,?,?,?,?,?)", (int(robot_id), int(running or 0), last_ts, day_date, float(day_equity_start or 0), int(day_stopped or 0), float(peak_value or 0), stop_order_id))
            else:
                fields = []
                vals = []
                if running is not None: fields.append("running=?"); vals.append(int(running))
                if last_ts is not None: fields.append("last_ts=?"); vals.append(last_ts)
                if day_date is not None: fields.append("day_date=?"); vals.append(day_date)
                if day_equity_start is not None: fields.append("day_equity_start=?"); vals.append(float(day_equity_start))
                if day_stopped is not None: fields.append("day_stopped=?"); vals.append(int(day_stopped))
                if peak_value is not None: fields.append("peak_value=?"); vals.append(float(peak_value))
                if stop_order_id is not None: fields.append("stop_order_id=?"); vals.append(stop_order_id)
                if fields:
                    vals.append(int(robot_id))
                    conn.execute("UPDATE robot_state SET " + ",".join(fields) + " WHERE robot_id=?", vals)
        finally:
            conn.close()

def load_state(robot_id):
    with _lock:
        conn = _connect()
        try:
            cur = conn.execute("SELECT * FROM robot_state WHERE robot_id=?", (int(robot_id),))
            r = cur.fetchone()
            return dict(r) if r else None
        finally:
            conn.close()

def list_states():
    with _lock:
        conn = _connect()
        try:
            cur = conn.execute("SELECT * FROM robot_state ORDER BY robot_id")
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

def summary():
    with _lock:
        conn = _connect()
        try:
            cur = conn.execute("SELECT robot_id, COUNT(*) AS n FROM trades GROUP BY robot_id")
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()