# ROBOT V2 - заметки для новой версии

Сформировано: 2026-10-09
Назначение: выводы из опыта Аналитика v1. Для будущего переписывания робота.

## 1. Архитектура
- Один процесс вместо 11. Сейчас дашборд + пилот + панель + bug_tracker + 5 multi + 2 watchdog. Должно быть: один Python + asyncio-tasks.
- Один robot/, не дубль robot/ и robot/multi/. Дублирование дало баг с trail_pct.
- Strategy как чистые функции: signal(candles) -> BUY/SELL/HOLD. Торговля отдельно.
- Broker-слой между стратегией и API. Стратегия сама не зовёт post_order.
- Watchdog внутри основного процесса, а не отдельный скрипт.

## 2. Данные
- SQLite с самого начала (JSONL - костыли).
- Единый config.json: dashboard, pilot, main_robot, multi_robots[].
- Один тип логов (JSON lines: ts, level, robot_id, msg) вместо 5 файлов.

## 3. Стратегии
- Не делать 4 стратегии сразу. Реально работают 2: SMA-slope и Grid.
- SMA 5/20 D1: TATN, TATNP (+15-25% за 2 года).
- SMA 10/50 D1: PIKK, NVTK (+8-18%).
- Grid в боковике: SBER, GAZP (+3-5% к b&h).
- ОФЗ: держать + купоны (318k/год).
- Трейлинг 3%: только D1 + трендовые (VSEH, LKOH, SIBN, NLMK, MOEX, ROSN, SBER).
- НЕ использовать: DCA, Interval на год, Grid в тренде.

## 4. Безопасность
- Kill-switch с самого начала: daily loss, max drawdown, global loss.
- armed-флаг с самого начала: в real без подтверждения - не торговать.
- Graceful shutdown: единая команда stop_all.
- Sandbox удерживает больше, чем цена x qty. Проверять эмпирически.

## 5. Технологии
- Python + asyncio + httpx (вместо urllib).
- Pydantic (валидация, типы).
- SQLite WAL (вместо JSONL).
- structlog (один структурированный лог).
- Linux + systemd (вместо Windows + .bat).

## 6. Тесты и бэктесты
- Тесты до кода: сначала mock-API, потом стратегия.
- Бэктест-фреймворк в день 1: backtest(strategy, params, candles) -> metrics.
- BACKTESTS.md с самого начала - главный документ проекта.

## 7. Структура нового проекта
config.json, broker/ (client.py, models.py), strategies/ (sma.py, grid.py), engine.py, backtest.py, db.py, api/, tests/

## 8. Главный вывод
Проект получился снизу вверх - от экспериментов к платформе. Если строить заново - сверху вниз: сначала архитектура (конфиг, БД, broker-слой, watchdog), потом стратегии.

Самое ценное для переноса: BACKTESTS.md, CONTEXT.md, RULES.md, опыт (SMA-slope на трендовых, Grid в боковике, трейлинг только D1+тренд, ОФЗ держать).

Технологии - 20% успеха. Остальные 80% - дисциплина тестирования и документирования.
---

## 9. Что реализовано в RobotV2 (2026-10-09)

Проверено в sandbox, 4 робота: TATN, GAZP, TATNP, VTBR (SMA 5/20 D1).

### Broker
- httpx async, auto-reconnect (ConnectError/ReadError/Timeout/PoolTimeout)
- Rate limit, retry, 429
- Spread check перед ордером
- Market + Limit ордера (limit_offset=0.002)
- API-стоп-ордера, cancel, get_stop_orders

### Engine
- Прерываемый цикл (Stop за 1-2 сек), graceful shutdown
- Lot-aware sizing (_floor_lot, GAZP lot=10)
- Budget check: свободные деньги + max_position_rub
- Risk: daily kill-switch, drawdown, global loss
- Reconcile: stop по figi+stopPrice (2% допуск), отмена лишних
- Stop missing alert: 3 фейла подряд → desktop toast

### Данные
- SQLite WAL: trades, orders, robot_state, миграции
- Auto-backup БД раз в сутки (pilot), keep 7 дней
- Desktop-тосты о сделках и ошибках

### Мониторинг
- tools/watch_robot.py — рестарт при мёртвом логе >240с
- tools/pilot.py — алерты: log silent, price stuck, trade ERROR/REJECTED, backup
- start_all.bat + install_autostart.py (Startup)
- Дашборд на http://127.0.0.1:8770/

### Утилиты
- tools/pnl.py — P&L сводка из БД
- tools/vs_buyhold.py — SMA vs Buy&Hold (альфа +11..+41 п.п. на 2г)
- tools/run_offset_test.py — limit offset 0.1/0.2/0.3/0.5%
- tools/backup_db.py — backup + purge 7 дней

### Тесты
- 37 passed (client, engine, grid, sma, risk, reconcile, lot_budget)

---

## 10. Обновление 2026-10-10

### Стратегии (5 роботов)
- TATN: SMA 5/20 + trail 3%
- GAZP: MACD 12/26/9 (+1.8% vs +0.87% SMA на 2г)
- TATNP: SMA 5/20
- VTBR: SMA 10/50
- SIBN: SMA 5/20 + trail 3%
- Зарегистрированы ещё: RSI, Bollinger
- Mass-test 7 стратегий x 254 бумаги → MACD лидер на NVTK/ROSN

### Защиты (обновление)
- Schedule-aware: не торгует при закрытой бирже (MOEX 09:10-18:59, пн-пт)
- Расписание из API GetTradingSchedules, автоперезагрузка раз в 6ч
- Preflight GetTradingStatus для real (apiTradeAvailableFlag)
- Fresh-price guard: отклонение >15% от свечи → берём свечу
- Velocity breaker: 3% потери за 5 мин → halt (сброс на след. день)
- Cross-robot kill-switch: 5% общий drop → стоп всех
- Heartbeat: tick frozen > 5 мин → алерт
- Stale-candle: > 2x timeframe → алерт
- Anomaly guard: qty>0 avg=0 → skip
- Slippage alert: SELL исполнен >1% хуже ожидаемого
- Pending persistence: лимитник переживает рестарт
- Limit timeout 3 тика → market fallback

### Инфраструктура
- 1 процесс: 5 роботов + dashboard + watchdog + pilot + heartbeat + cross-kill + daily report + schedule refresh
- Watchdog следит за количеством процессов, убивает дубли
- Уникальный AppUserModelID RobotV2.Notifications (Windows toasts)
- check_interval=15 сек (было 60)
- Timestamps в БД в UTC (совместимо с T-Invest)
- Backup БД раз в сутки через pilot

### Тесты
- 46 passed (client, engine, grid, sma, risk, reconcile, lot_budget, guards)
- Live-проверено: gap-detection (312s offline), stop-loss (SIBN +1561 RUB), market fallback

### Известные ограничения
- WebSocket только для real (sandbox не поддерживает)
- GetTradingStatus в sandbox возвращает 404 — preflight пропускается
