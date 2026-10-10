# -*- coding: utf-8 -*-
"""risk.py - risk management."""
from __future__ import annotations
import collections
from datetime import datetime, timezone
from typing import Any

class RiskManager:
    def __init__(self, params):
        p = params or {}
        self.daily_limit = float(p.get("daily_loss_limit", p.get("daily_loss_limit_percent", 0.0)) or 0.0)
        self.max_dd = float(p.get("max_drawdown", p.get("global_loss_limit_percent", 0.0)) or 0.0)
        self.day_date = None
        self.day_equity_start = 0.0
        self.day_stopped = False
        self.peak_value = 0.0
        self.stopped = False
        self.stopped_reason = ""
        self.stopped_date = None
        self.velocity_pct = float(p.get("velocity_limit", 0.03))
        self.velocity_window = int(p.get("velocity_window_sec", 300))
        self._eq_hist = collections.deque(maxlen=64)

    def check(self, equity: float) -> tuple[bool, str]:
        today = datetime.now(timezone.utc).date()
        if self.stopped:
            _is_vel = "velocity" in (self.stopped_reason or "")
            if _is_vel and self.stopped_date != today:
                self.stopped = False
                self.stopped_reason = ""
                self._eq_hist.clear()
            else:
                return False, self.stopped_reason or "stopped"
        if self.day_date != today:
            self.day_date = today
            self.day_equity_start = equity
            self.day_stopped = False
        if self.daily_limit > 0 and self.day_equity_start > 0 and not self.day_stopped:
            dl = (self.day_equity_start - equity) / self.day_equity_start
            if dl >= self.daily_limit:
                self.day_stopped = True
                return False, "daily limit {:.2%}".format(dl)
        if self.day_stopped:
            return False, "daily stopped"
        _now = datetime.now(timezone.utc).timestamp()
        self._eq_hist.append((_now, equity))
        while self._eq_hist and _now - self._eq_hist[0][0] > self.velocity_window:
            self._eq_hist.popleft()
        if self.velocity_pct > 0 and len(self._eq_hist) >= 2:
            _base = self._eq_hist[0][1]
            if _base > 0:
                _drop = (_base - equity) / _base
                if _drop >= self.velocity_pct:
                    self.stopped = True
                    self.stopped_reason = "velocity drop {:.2%} in {}s".format(_drop, self.velocity_window)
                    self.stopped_date = today
                    return False, self.stopped_reason
        if equity > self.peak_value:
            self.peak_value = equity
        if self.max_dd > 0 and self.peak_value > 0:
            dd = (self.peak_value - equity) / self.peak_value
            if dd >= self.max_dd:
                self.stopped = True
                self.stopped_reason = "max drawdown {:.2%}".format(dd)
                return False, self.stopped_reason
        return True, "ok"