# External Ideas - what to borrow from foreign trading bots

Date: 2026-10-11
Source: analysis of open-source bots (BitMEX, Kraken, Freqtrade, Hummingbot, ScalpbotTbank)

## Priority 1: Dead Man switch (DMS)
Idea: bot pings exchange I-am-alive. If it stops, exchange auto-cancels all its orders.
T-Invest API: no DMS endpoint.
Workaround: on connection loss, watch_robot.py cancels extra orders.
Status: deferred.

## Priority 2: Fail-Closed hardening
Idea: on uncertainty - halt, not continue.
TODO:
- 5 consecutive API errors -> halt robot
- reconcile mismatch 3 times in a row -> halt
- stale candle > 3x timeframe -> halt (not just alert)
Status: partial (Reject storm, Gap-detection).

## Priority 3: Circuit Breaker with cooldown and re-arm
Idea: instead of hard stop-till-end-of-day - soft stop with timer.
TODO:
- State machine: Closed -> Open -> Half-Open
- Open: no trading for N minutes
- Half-Open: try with half position size
Status: not implemented. Start with velocity breaker.

## Priority 4: Atomic Writes
Idea: write via tmp + fsync + os.replace.
Status: SQLite WAL already provides this. Not needed.

## Priority 5: Pre-Trade Risk Gate
Idea: all orders pass through a single gate.
TODO:
- max_consecutive_losses
- max_trades_per_day
- max_position_pct of equity
Status: partial (RiskManager).

## Priority 6: Internal task watchdog
Idea: monitor each background task separately.
TODO:
- if tick_count unchanged > 5 min -> restart task
- if equity_task died -> restart
Status: not implemented.

## Do NOT take
- Telegram
- Docker
- Multi-agent AI
- TWAP/VWAP
- React dashboard
