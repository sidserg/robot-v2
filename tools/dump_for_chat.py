# -*- coding: utf-8 -*-
"""dump_for_chat.py - собрать весь проект в один файл для нового чата.

Собирает:
  - структуру папок
  - содержимое .py / .md / .json / .sql / .yml / .bat / .txt файлов
  - git log (последние 20 коммитов)
  - git status
Пропускает: .git, __pycache__, .venv, data, logs, dump, .pytest_cache, *.db
"""
from __future__ import annotations
import pathlib
import datetime
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "dump"
OUT_DIR.mkdir(exist_ok=True)

SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "data", "logs", "dump", ".pytest_cache", ".idea", ".vscode"}
SKIP_EXTS = {".pyc", ".pyo", ".db", ".db-wal", ".db-shm", ".zip", ".out.log", ".log", ".png", ".jpg", ".ico"}

EXTS = {".py", ".md", ".json", ".sql", ".yml", ".yaml", ".bat", ".cmd", ".txt", ".ini", ".cfg", ".service"}

MAX_FILE_BYTES = 200_000


def collect_files():
    out = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() in SKIP_EXTS:
            continue
        if p.suffix.lower() not in EXTS:
            continue
        if "token" in p.name.lower():
            continue
        try:
            if p.stat().st_size > MAX_FILE_BYTES:
                continue
        except Exception:
            continue
        out.append(p)
    return sorted(out, key=lambda x: str(x.relative_to(ROOT)).lower())


def tree():
    lines = []
    def walk(d, prefix=""):
        items = sorted([x for x in d.iterdir() if x.name not in SKIP_DIRS and x.name not in {".gitignore"} or x.name == ".gitignore"],
                       key=lambda x: (not x.is_dir(), x.name.lower()))
        for i, x in enumerate(items):
            last = i == len(items) - 1
            mark = "└── " if last else "├── "
            lines.append(prefix + mark + x.name + ("/" if x.is_dir() else ""))
            if x.is_dir() and x.name not in SKIP_DIRS:
                walk(x, prefix + ("    " if last else "│   "))
    lines.append(ROOT.name + "/")
    walk(ROOT)
    return "\n".join(lines)


def git_info():
    out = []
    for cmd in [["git", "log", "--oneline", "-20"], ["git", "status", "--short"], ["git", "branch", "--show-current"]]:
        try:
            r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace")
            out.append("$ " + " ".join(cmd))
            out.append(r.stdout.strip() or "(empty)")
            out.append("")
        except Exception as e:
            out.append("$ " + " ".join(cmd) + " -> FAILED: " + str(e))
            out.append("")
    return "\n".join(out)


def main():
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = OUT_DIR / ("dump_" + ts + ".txt")
    parts = []
    parts.append("=== PROJECT: " + ROOT.name + " ===")
    parts.append("Dump generated: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    parts.append("")
    parts.append("=== STRUCTURE ===")
    parts.append(tree())
    parts.append("")
    parts.append("=== GIT ===")
    parts.append(git_info())
    parts.append("")

    files = collect_files()
    parts.append("=== FILES (" + str(len(files)) + ") ===")
    parts.append("")
    for p in files:
        rel = p.relative_to(ROOT)
        parts.append("--- " + str(rel) + " ---")
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            txt = "READ ERROR: " + str(e)
        parts.append(txt.rstrip())
        parts.append("")

    out_path.write_text("\n".join(parts), encoding="utf-8")
    size_kb = out_path.stat().st_size / 1024
    print("OK:", out_path)
    print("size: {:.1f} KB, files: {}".format(size_kb, len(files)))


if __name__ == "__main__":
    main()