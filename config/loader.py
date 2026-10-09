# -*- coding: utf-8 -*-
"""loader.py — загрузка config.json с кэшем."""
from __future__ import annotations
import json
import pathlib
from typing import Any

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_CACHE = None

def load(path: str | pathlib.Path | None = None) -> dict[str, Any]:
    global _CACHE
    if _CACHE is not None and path is None:
        return _CACHE
    p = pathlib.Path(path) if path else (_ROOT / "config.json")
    data = json.loads(p.read_text(encoding="utf-8"))
    if path is None:
        _CACHE = data
    return data

def reset_cache() -> None:
    global _CACHE
    _CACHE = None