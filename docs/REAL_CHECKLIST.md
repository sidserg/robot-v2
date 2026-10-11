# REAL CHECKLIST - first launch

Step-by-step for going live. Do not skip.

## Before launch (1 day before)

- [ ] Real token in token.txt (mode=real, works)
- [ ] Account 2133793733 (Torgovyi portfel) topped up to 10000 RUB
- [ ] config.real.json exists and armed=false
- [ ] Sandbox robots stopped: python tools/stop_all.py
- [ ] 78 tests pass: python -m pytest tests/ -q
- [ ] real_ready.py shows all OK (except armed)

## Launch day (10:00 MSK, weekday)

- [ ] Make backups: config.json, data/robot.db
- [ ] Run: python tools/switch_to_real.py
- [ ] Verify config.json now = config.real.json
- [ ] Set armed=true in config.json
- [ ] python tools/real_ready.py  ->  all OK
- [ ] Start: python runner/multi.py
- [ ] Watch log 5 min: warmup 1/5 ... 5/5, then SCANNING
- [ ] Check status: python tools/status.py
- [ ] Check broker: no orders, only 1 robot (TATN)

## First day monitoring

- [ ] Morning: check /health - errors=0
- [ ] Midday: python tools/pnl.py - unrealized near zero
- [ ] Evening: no unexpected orders
- [ ] Every 2h: cat logs/robot.log | findstr ERROR

## First week

- [ ] Day 1-2: only observe. NO code changes.
- [ ] Day 3-4: check commissions vs sandbox
- [ ] Day 5: check slippage. Real market may be wider.
- [ ] Day 6-7: check kill-switch (did it ever trigger?)
- [ ] Weekend: full review of trades and P&L

## Red flags - STOP immediately

- Any SHORT position (negative qty)
- STOP LOSS missing on open position
- POSITION DRIFT (broker vs db)
- 30079 / 30049 errors repeatedly
- Loss > daily_loss_limit (300 RUB)
- Drawdown > max_drawdown (1000 RUB)
- Robot silent > 5 min

If any red flag:
1. python tools/stop_all.py
2. python tools/switch_to_sandbox.py
3. Investigate before restart

## After 2 weeks clean

- [ ] Review total P&L vs sandbox
- [ ] If positive: consider 30k RUB
- [ ] If negative: analyze why, do not scale
- [ ] Add second robot ONLY if first is profitable

## Rules

- No code changes during first week
- No new tickers until TATN is stable
- One robot, one ticker, one account - for now
- Weekly review: what worked, what did not
- Keep sandbox running on separate machine/window for research

## Contacts

Owner: sidserg
Account: 2133793733 (Torgovyi portfel)
Budget: 10000 RUB (start)
Robot: TATN SMA 5/20 slope