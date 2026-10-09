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
broker/       — T-Invest API клиент, портфель, ордера, модели
strategies/   — логика сигналов (SMA, ADX/RSI фильтры)
engine/       — торговый цикл, риск-менеджмент, lot-aware, budget
db/           — SQLite (trades, orders, robot_state) + миграции
notify/       — desktop-тосты
runner/       — multi-инстансы в одном процессе + дашборд
backtest/     — единый бэктест-движок
config/       — загрузка config.json
tests/        — pytest
docs/         — документация
tools/        — утилиты
```

## Возможности

- Market и Limit-ордера (use_limit=true в params робота)
- Lot-aware размер позиции (округление вниз до лота, напр. GAZP lot=10)
- Budget check перед покупкой: свободные деньги + max_position_rub
- Авто-переподключение httpx при ConnectError/ReadError/RemoteProtocolError/Timeout
- Прерываемый цикл: Stop за 1-2 секунды, graceful shutdown всех роботов
- API-стоп-ордера, трейлинг, daily kill-switch, drawdown-stop
- Reconcile trades/стопов, preflight проверки
- Desktop-уведомления о сделках и ошибках

## Установка

```
pip install -r requirements.txt
```

Токен T-Invest положить в `token.txt` в корне.

## Запуск

```
python runner/multi.py
```

Роботы берутся из `config.json` -> `robots[]`.
Для real-режима: `armed=true` в config.json (иначе real-роботы блокируются).

## Дашборд

Открывается автоматически при старте: http://127.0.0.1:8770/
API: http://127.0.0.1:8770/api/state

## Тесты

```
python -m pytest tests/ -q
```

## Документация

- `docs/ROBOT_V2.md` — заметки для этой версии
- `docs/BACKTESTS.md` — результаты бэктестов
- `docs/AI_CHECKLIST.md` — правила работы

## Мониторинг (отдельные окна)

```
start "robotv2" cmd /k "python runner/multi.py"
start "watch_robot" cmd /k "python tools/watch_robot.py"
start "pilot" cmd /k "python tools/pilot.py"
```

- `runner/multi.py` — N роботов в одном процессе
- `tools/watch_robot.py` — внешний watchdog: рестарт при мёртвом `logs/robot.log` > 240с
- `tools/pilot.py` — desktop-алерты: `log silent` (>180с), `price stuck` (>10 циклов), `trade error` (ERROR/REJECTED в `data/robot.db`)

## Что НЕ входит

- Аналитика портфеля (XIRR, календарь, heatmap) — см. отдельный проект
- Telegram

## Защиты от сбоев (2026-10-09)

- **API-стоп на бирже** — работает без интернета (главная защита)
- **Gap-detection** — offline > 3x interval → force reconcile + alert
- **Halt после 3 гэпов подряд** — не торгуем вслепую при нестабильной связи
- **Fresh-price guard** — цена из портфеля > 15% от свечи → берём свечу
- **Slippage alert** — стоп исполнен хуже ожидаемого > 1% → toast
- **Drawdown velocity breaker** — потеря 3% за 5 мин → остановка
- **Anomaly guard** — qty>0, avg=0 → alert + skip
- **max_jump_percent** — блок новых входов при скачке > 5%
- **Pending persistence** — лимитник переживает рестарт
- **Limit timeout + market fallback** — 3 тика, потом market
- **Reconnect httpx** — авто-сброс клиента при ошибках сети
- **Stop reconcile** — поиск по figi+цене (2%), отмена лишних
