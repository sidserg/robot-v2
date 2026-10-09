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