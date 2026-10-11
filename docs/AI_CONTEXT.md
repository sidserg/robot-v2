# AI Context - RobotV2

Static overview. Regenerate manually or from a new AI chat.
For live state use: python tools/status.py

## 1. What is this

Trading bot for T-Invest API (Tinkoff/T-Bank).
5 robots in one process, all on SMA 5/20 slope, D1 candles.
Mode: sandbox. Ready for real: ~80 percent.

## 2. Stack

- Python 3.12+
- asyncio + httpx
- SQLite (WAL) + pydantic v2
- Windows (taskkill, python.exe processes)

## 3. Robots (current config)

| ID | Ticker | Strategy | Notes |
|----|--------|----------|-------|
| 1 | TATN | SMA 5/20 slope | strong (backtest +13.8 percent 9mo) |
| 2 | ROSN | SMA 5/20 slope | replaced GAZP 2026-10-11 |
| 3 | TATNP | SMA 5/20 slope | best (backtest +14.8 percent) |
| 4 | SFIN | SMA 5/20 slope | replaced VTBR 2026-10-11 |
| 5 | SIBN | SMA 5/20 slope | ok (+11.2 percent) |

## 4. Not to do

- Telegram (never)
- Docker (Windows-only project)
- Multi-line strings in python -c (cmd breaks)
- Edit files through Notepad (use python scripts)
- Russian text in bash here-strings
- Overengineering: add only what is needed

## 5. Key files

| File | Purpose |
|------|---------|
| engine/loop.py | robot trading loop |
| engine/risk.py | RiskManager, circuit breaker, guards |
| engine/reconcile.py | trades and stops reconciliation |
| engine/startup_filter.py | warmup + market drop alert |
| broker/client.py | httpx T-Invest client |
| broker/orders.py | post_order, post_stop_order |
| broker/session_guard.py | MOEX session phases |
| strategies/sma.py | SMA 5/20 slope |
| strategies/adxregime.py | ADX regime switch (testing) |
| runner/multi.py | 5 robots in one process |
| runner/supervisor.py | auto-restart crashed tasks |
| db/repo.py | SQLite wrapper |
| tools/chart.py | web chart on :8771 |
| tools/real_ready.py | pre-flight check for real |
| config.json | robots config |
## 6. Safety guards

### Trading
- SELL clamp: cannot sell more than position
- SELL skip if qty=0
- Order validation: qty>0, limit needs price>0
- Stop order: new placed before old cancelled (no gap)
- Stop persistence in DB immediately
- Deterministic order_id (sha1 figi+direction+minute)
- API-stop on exchange (works offline)
- Trailing stop (trail_pct)
- Limit timeout + market fallback
- Pending persistence (survives restart)

### Risk management
- Daily kill-switch (daily_loss_limit)
- Drawdown stop (max_drawdown)
- Velocity breaker: 3 percent drop in 5 min -> cooldown 30 min -> half-open 50 percent size
- Reject storm: 10 rejects / 5 min -> halt
- max_consecutive_losses (default 5)
- max_trades_per_day (default 0 = off)
- Anomaly guard: qty>0 and avg=0 -> skip
- Negative position -> halt
- max_jump_percent 15 percent (blocks crazy moves)

### Connection and data
- Gap-detection: offline > 3x interval -> force reconcile
- Halt after 3 gaps in a row
- Fresh-price guard: > 15 percent deviation -> use candle
- Reconnect httpx on network errors
- No-retry on 4xx (except 401)
- 30079/30049 (exchange closed) -> info, skip tick
- Candles cache 30 sec
- Session-aware spread guard (real only)

### Recovery
- Reconcile trades: fills missing trades in DB, dedup by (kind, ts, 3h)
- Startup position reconciliation: broker vs DB drift -> alert + force reconcile
- Stop reconcile by figi+price (2 percent)
- External watchdog: restart multi.py if log stale > 5 min
- Internal supervisor: auto-restart crashed background tasks
- Single-instance lock (runner/lock.py)
- Warmup: 3 ticks after start, no trades
## 7. Backtest results (D1, 730 days, SMA 5/20 slope)

| Ticker | PnL percent | Trades | Alpha vs B and H |
|--------|---------|--------|------------------|
| TATNP | +17.63 | 16 | +12.11 |
| TATN | +15.53 | 19 | +5.82 |
| SIBN | +5.82 | 21 | +15.92 |
| ROSN | +0.94 | 13 | - |
| GAZP | +0.39 | 16 | +23.10 |
| SFIN | +20.77 | 20 | - |
| VTBR | +1.60 | 20 | +37.30 |

Monthly backtest 2026 Jan-Sep (D1, with slippage 0.1 percent):

| Ticker | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Total |
|--------|-----|-----|-----|-----|-----|-----|-----|-----|-----|-------|
| TATN | -0.2 | -3.1 | +9.3 | -2.6 | +3.0 | -0.6 | +2.3 | -1.0 | +6.7 | +13.8 |
| TATNP | -0.1 | -3.2 | +6.2 | -2.1 | +2.6 | 0.0 | +3.1 | +2.7 | +5.3 | +14.8 |
| SFIN | +0.5 | -2.2 | 0.0 | +11.0 | -3.6 | -0.5 | +6.6 | +1.9 | 0.0 | +13.7 |
| SIBN | -0.4 | -1.2 | +1.5 | -0.2 | -1.5 | 0.0 | +6.0 | +4.6 | +2.0 | +11.2 |
| ROSN | +1.8 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | +0.9 |

Intraday (M5, Sep 2026) - REJECTED

| Strategy | TATN | ROSN | TATNP | SFIN | SIBN |
|----------|------|------|-------|------|------|
| ADX-regime | -7.3 | -1.6 | -10.9 | -1.9 | -1.4 |
| SMA slope | -27.2 | -19.1 | -32.1 | -9.6 | -3.7 |
| Bollinger | -9.3 | -4.4 | -9.0 | -0.9 | -0.4 |

Verdict: M5 does not work, commissions eat everything. Test M15.
## 8. How to run

Start robots:
```cmd
cd /d C:\Users\cl\Desktop\RobotV2
python runner\multi.py
```

Stop:
```cmd
python tools\stop_all.py
```

Run tests:
```cmd
python -m pytest tests/ -q
```

Pre-flight check before real:
```cmd
python tools\real_ready.py
```

Current status (live data):
```cmd
python tools\status.py
```

Validate config:
```cmd
python tools\validate_config.py
```

Save (git add + commit + push):
```cmd
python tools\save_all.py "commit message"
```

Update this file after major changes:
```cmd
python tools\update_ai_context.py
```

## 9. URLs

- Dashboard: http://127.0.0.1:8770/
- Health: http://127.0.0.1:8770/health
- Equity: http://127.0.0.1:8770/equity
- Chart: http://127.0.0.1:8771/

## 10. Testing rules

- Backtest BEFORE any strategy change
- One change per commit
- Real money only after 3+ days clean sandbox
- Start real with 1 robot, small amount, not 5 at once
- If any incident (short, missing stop, wrong position) - STOP immediately

## 11. Contact context

Owner: sidserg
Location: Orenburg (UTC+5)
Language: Russian (user), English (code/docs preferred)