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