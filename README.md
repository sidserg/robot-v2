# RobotV2

Торговый робот для T-Invest API. Асинхронный, Linux-ready, SQLite.

## Что это

Изолированный торговый робот без дашборда и аналитики портфеля.
Работает с T-Invest API (sandbox и real), поддерживает multi-инстансы.

## Стек

- Python 3.12+
- httpx (async HTTP)
- pydantic v2
- SQLite (WAL)
- asyncio

## Структура

```
broker/       — T-Invest API клиент, портфель, ордера, модели
strategies/   — логика сигналов (SMA)
engine/       — торговый цикл, риск-менеджмент
db/           — SQLite (trades, orders, robot_state)
notify/       — desktop-тосты
runner/       — multi-инстансы в одном процессе
backtest/     — единый бэктест-движок
config/       — загрузка config.json
tests/        — pytest
docs/         — документация
tools/        — утилиты
```

## Установка

```
pip install -r requirements.txt
```

Токен T-Invest положить в `token.txt` в корне.

## Запуск

```
python runner/multi.py
```

Роботы берутся из `config.json` → `robots[]`.

## Тесты

```
python -m pytest tests/ -q
```

## Документация

- `docs/ROBOT_V2.md` — заметки для этой версии
- `docs/BACKTESTS.md` — результаты бэктестов
- `docs/AI_CHECKLIST.md` — правила работы

## Что НЕ входит

- Дашборд портфеля
- Аналитика (XIRR, календарь, heatmap)
- Панель управления
- Telegram