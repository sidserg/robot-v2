# -*- coding: utf-8 -*-
"""risk.py - risk management."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any

class RiskManager:
    def __init__(self, params):
        p = params or {}
        self.daily_limit = float(p.get("daily_loss_limit", 0.0))
        self.max_dd = float(p.get("max_drawdown", 0.0))
        self.day_date = None
        self.day_equity_start = 0.0
        self.day_stopped = False
        self.peak_value = 0.0
        self.stopped = False

    def check(self, equity: float) -> tuple[bool, str]:
        if self.stopped:
            return False, "stopped"
        today = datetime.now(timezone.utc).date()
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
        if equity > self.peak_value:
            self.peak_value = equity
        if self.max_dd > 0 and self.peak_value > 0:
            dd = (self.peak_value - equity) / self.peak_value
            if dd >= self.max_dd:
                self.stopped = True
                return False, "max drawdown {:.2%}".format(dd)
        return True, "ok"