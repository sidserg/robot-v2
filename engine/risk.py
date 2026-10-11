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
        self.reject_threshold = int(p.get("reject_storm_threshold", 10) or 10)
        self.reject_window_sec = int(p.get("reject_storm_window_sec", 300) or 300)
        self._rejects = collections.deque(maxlen=64)
        self.reject_stopped = False
        self.reject_stopped_date = None
        self.velocity_cooldown_sec = int(p.get("velocity_cooldown_sec", 1800) or 1800)
        self.velocity_cooldown_until = 0.0
        self.velocity_half_open = False
        self.risk_scale = 1.0

    def record_reject(self):
        _now = datetime.now(timezone.utc).timestamp()
        self._rejects.append(_now)
        while self._rejects and _now - self._rejects[0] > self.reject_window_sec:
            self._rejects.popleft()
        if self.reject_threshold > 0 and len(self._rejects) >= self.reject_threshold:
            self.reject_stopped = True
            self.reject_stopped_date = datetime.now(timezone.utc).date()

    def record_success(self):
        if self.velocity_half_open:
            self.velocity_half_open = False
            self.risk_scale = 1.0
            self.velocity_cooldown_until = 0.0

    def check(self, equity: float) -> tuple[bool, str]:
        today = datetime.now(timezone.utc).date()
        if self.reject_stopped:
            if self.reject_stopped_date != today:
                self.reject_stopped = False
                self._rejects.clear()
            else:
                return False, "reject storm ("+str(len(self._rejects))+" in "+str(self.reject_window_sec)+"s)"
        if self.stopped:
            _is_vel = "velocity" in (self.stopped_reason or "")
            if _is_vel:
                import time as _tm
                if self.velocity_cooldown_until > 0 and _tm.time() < self.velocity_cooldown_until:
                    _left = int(self.velocity_cooldown_until - _tm.time())
                    return False, "velocity cooldown "+str(_left)+"s left"
                self.stopped = False
                self.stopped_reason = ""
                self.velocity_half_open = True
                self.risk_scale = 0.5
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
                    import time as _tm2
                    self.stopped = True
                    self.velocity_cooldown_until = _tm2.time() + self.velocity_cooldown_sec
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