# -*- coding: utf-8 -*-
from __future__ import annotations
import os
import pathlib
import tempfile
import pytest
_TMP = tempfile.mkdtemp(prefix="robotv2_test_")
os.environ["ROBOTV2_DB"] = str(pathlib.Path(_TMP) / "test.db")
@pytest.fixture(autouse=True)
def _clean_db():
    from db import repo
    repo._DB_PATH = None
    try:
        repo.init_db()
    except Exception:
        pass
    yield
    try:
        import sqlite3
        c = sqlite3.connect(os.environ["ROBOTV2_DB"])
        c.execute("DELETE FROM trades")
        c.execute("DELETE FROM robot_state")
        c.commit(); c.close()
    except Exception:
        pass