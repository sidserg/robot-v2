# RobotV2

Торговый робот для T-Invest API. Асинхронный, Linux-ready, SQLite.

## Что это

Изолированный торговый робот, работает с T-Invest API (sandbox и real), поддерживает multi-инстансы в одном процессе.
Встроенный веб-дашборд: http://127.0.0.1:8770/

## Стек

- Python 3.12+
- httpx (async HTTP)
- pydantic v2
- SQLite (WAL)
- asyncio

## Структура

```
broker/       - T-Invest API клиент, портфель, ордера, модели
strategies/   - логика сигналов (SMA, MACD, RSI, Bollinger, Grid)
engine/       - торговый цикл, риск-менеджмент, lot-aware, budget, reconcile
db/           - SQLite (trades, orders, robot_state) + миграции
notify/       - desktop-тосты
runner/       - multi-инстансы в одном процессе + дашборд + lock
backtest/     - единый бэктест-движок
config/       - загрузка config.json
tests/        - pytest (85+ тестов)
docs/         - документация
tools/        - утилиты (chart, watchdog, pnl, save_all, stop_all)
```

## Возможности

- Market и Limit-ордера (use_limit=true в params робота)
- Lot-aware размер позиции (округление вниз до лота)
- Budget check перед покупкой: свободные деньги + max_position_rub
- API-стоп-ордера на бирже (работают без интернета)
- Трейлинг-стоп (trail_pct)
- Daily kill-switch и drawdown-stop (velocity breaker)
- Reconcile trades и стопов через API
- Preflight проверки (apiTradeAvailableFlag)
- Desktop-уведомления о сделках и ошибках
- Веб-график свечей с маркерами сделок (порт 8771)

## Установка

```
pip install -r requirements.txt
```

Токен T-Invest положить в token.txt в корне.

## Запуск

```
python runner/multi.py
```

Роботы берутся из config.json -> robots[].
Для real-режима: armed=true в config.json (иначе real-роботы блокируются).

Защита от двойного запуска: runner/lock.py — нельзя запустить два multi.py одновременно.

## Дашборд

Открывается автоматически при старте: http://127.0.0.1:8770/
API: http://127.0.0.1:8770/api/state

## График

Запуск: python tools/chart.py
Открывается: http://127.0.0.1:8771/

Маркеры сделок (кружки B/S), hover-тултип с ценой и временем.
Сделки вне диапазона свечей не рисуются.

## Тесты

```
python -m pytest tests/ -q
```

## Документация

- docs/ROBOT_V2.md - заметки для этой версии
- docs/BACKTESTS.md - результаты бэктестов
- docs/AI_CHECKLIST.md - правила работы

## Мониторинг (отдельные окна)

```
start "robotv2" cmd /k "python runner/multi.py"
start "chart" cmd /k "python tools/chart.py"
start "watchdog" cmd /k "python tools/watch_robot.py"
start "pilot" cmd /k "python tools/pilot.py"
```

- runner/multi.py - N роботов в одном процессе
- tools/watch_robot.py - внешний watchdog: рестарт если logs/robot.log не обновлялся >5 мин
- tools/chart.py - веб-график свечей и сделок
- tools/pilot.py - desktop-алерты (log silent, price stuck, trade error)

Или через start_all.bat — поднимает всё сразу.

## Что НЕ входит

- Аналитика портфеля (XIRR, календарь, heatmap) — см. отдельный проект
- Telegram

## Защиты от сбоев

### Торговые

- **API-стоп на бирже** — работает без интернета (главная защита)
- **SELL clamp** — нельзя продать больше текущей позиции (защита от шорта)
- **SELL skip** — если позиции нет, SELL не отправляется
- **Order validation** — qty>0, limit требует price>0, stop требует price>0
- **Stop placement order** — сначала ставим новый стоп, потом отменяем старый (нет окна без стопа)
- **Stop persistence** — stop_order_id и _api_stop_price пишутся в БД при каждом изменении
- **Limit timeout + market fallback** — 3 тика, потом market
- **Pending persistence** — лимитник переживает рестарт
- **Slippage alert** — стоп исполнен хуже ожидаемого >1% -> toast
- **Preflight** — проверка apiTradeAvailableFlag перед real-стартом

### Риск-менеджмент

- **Daily kill-switch** — daily_loss_limit из config.json
- **Drawdown stop** — max_drawdown из config.json
- **Drawdown velocity breaker** — потеря 3% за 5 мин -> остановка
- **Anomaly guard** — qty>0, avg=0 -> alert + skip
- **max_jump_percent** — блок новых входов при скачке >5%
- **Cross-kill** — общая просадка по всем счетам >5% -> halt всех роботов

### Связь и данные

- **Gap-detection** — offline >3x interval -> force reconcile + alert
- **Halt после 3 гэпов подряд** — не торгуем вслепую при нестабильной связи
- **Fresh-price guard** — цена из портфеля >15% от свечи -> берём свечу
- **Reconnect httpx** — авто-сброс клиента при ошибках сети
- **No-retry 4xx** — 4xx не ретраится, падает сразу (кроме 401 auth)
- **30079 handling** — «биржа закрыта» -> info, skip tick (не спамит ERROR)
- **Market hours skip** — real-режим не дёргает API когда биржа закрыта (sandbox работает 24/7)
- **Candles cache** — кэш свечей 30 сек (снижение нагрузки на API)

### Восстановление

- **Reconcile trades** — ищет сделки в API, которых нет в БД, дозаписывает
- **Дедупликация** — по (kind, ts, 3ч допуск), не задваивает
- **Stop reconcile** — поиск по figi+цене (2%), отмена лишних
- **External watchdog** — рестарт multi.py при зависании (лог молчит >5 мин)
- **Single-instance lock** — нельзя запустить два runner одновременно

## Тесты

- tests/test_critical.py — SELL clamp, reconcile kind, risk config, 4xx no-retry
- tests/test_orders.py — валидация qty и price в post_order/post_stop_order

## История изменений

- 2026-10-10: SELL clamp, reconcile writes, order validation, stop order sequence, watchdog, lock
- 2026-10-09: reconcile, gap-detection, halt, fresh-price, max_jump
- 2026-10-09: API-стоп, трейлинг, daily kill-switch, drawdown-stop