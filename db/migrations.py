# -*- coding: utf-8 -*-
"""migrations.py - миграции схемы SQLite."""
from __future__ import annotations
import sqlite3
import logging

log = logging.getLogger("db.migrations")

MIGRATIONS = []

def migration(version):
    def deco(fn):
        MIGRATIONS.append((version, fn))
        return fn
    return deco

@migration(1)
def m1_initial(conn):
    pass  # базовая схема уже создана через schema.sql

@migration(2)
def m2_last_tick_ts(conn):
    try:
        conn.execute("ALTER TABLE robot_state ADD COLUMN last_tick_ts TEXT")
    except Exception:
        pass

@migration(3)
def m3_pending_order_id(conn):
    try:
        conn.execute("ALTER TABLE robot_state ADD COLUMN pending_order_id TEXT")
    except Exception:
        pass

@migration(4)
def m4_pending_info(conn):
    try:
        conn.execute("ALTER TABLE robot_state ADD COLUMN pending_info TEXT")
    except Exception:
        pass

@migration(5)
def m5_equity_history(conn):
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS equity_history (id INTEGER PRIMARY KEY AUTOINCREMENT, robot_id INTEGER NOT NULL, ts TEXT NOT NULL, cash REAL, pos_value REAL, total REAL)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_eq_rid_ts ON equity_history(robot_id, ts)")
    except Exception:
        pass

def current_version(conn):
    try:
        cur = conn.execute("SELECT MAX(version) AS v FROM schema_version")
        r = cur.fetchone()
        return int(r["v"] or 0) if r else 0
    except Exception:
        return 0

def apply_all(conn):
    cur_v = current_version(conn)
    for ver, fn in sorted(MIGRATIONS):
        if ver <= cur_v:
            continue
        log.info("applying migration %s", ver)
        try:
            fn(conn)
            conn.execute("INSERT OR IGNORE INTO schema_version(version) VALUES (?)", (ver,))
        except Exception as e:
            log.error("migration %s failed: %s", ver, e)
            raise
    return current_version(conn)