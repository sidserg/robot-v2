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