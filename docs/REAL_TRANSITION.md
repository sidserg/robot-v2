# REAL TRANSITION - переход в реальную торговлю

Сформировано: 2026-10-10

## Что нужно перед запуском в real

### 1. Токен

- Выпустить **production-токен** в личном кабинете T-Invest (https://www.tinkoff.ru/invest/settings/api/).
- Тип: **Full-access** (торговля). Read-only не подойдёт.
- Срок жизни: 3 месяца. Использовать минимум раз в 7 дней (иначе автозакрытие).
- Положить в `token.txt` в корне проекта (файл в .gitignore).
- Sandbox-токен НЕ подойдёт для real - получишь 401.

### 2. Счёт

- Проверить `account_id` брокерского счёта в config.json для каждого робота.
- Убедиться, что на счёте есть деньги (роботы не торгуют в долг).
- Проверить, что счёт активен и не заблокирован.

### 3. Config.json

- Для каждого робота: `mode: "real"` (было "sandbox").
- В корне: `armed: true` (без него real-роботы блокируются).
- Проверить `max_position_rub` - реальный максимум на сделку.
- Проверить `risk_per_trade_pct` - процент капитала на сделку (0.15 = 15%).
- Проверить `daily_loss_limit` - дневной стоп.
- Проверить `max_drawdown` - общий стоп.
- Проверить `velocity_limit` - защита от быстрой потери.

### 4. Armied-флаг (защита)

Без `armed: true` real-роботы не запускаются.
Это защита от случайного запуска - даже если токен подложен.

### 5. Preflight

Перед первым тиком робот проверяет инструмент через GetInstrument:
- `apiTradeAvailableFlag` - торгуется ли через API
- `buyAvailableFlag` - можно ли покупать
- `sellAvailableFlag` - можно ли продавать
Если что-то не так - робот останавливается с алертом.

### 6. Расписание

Робот читает расписание MOEX из API (GetTradingSchedules).
Вне торговых часов - спит, ордера не отправляет.
Выходные - не торгует.

### 7. Что произойдёт при старте

1. Token читается из token.txt.
2. Расписание обновляется из API.
3. Preflight проверяет инструмент.
4. Робот восстанавливает позицию из БД.
5. Если позиция есть и стопа нет - ставит стоп.
6. Начинает торговлю.

## Пошаговый план

```
1. Выпустить production-токен (Full-access)
2. Положить в token.txt
3. В config.json: mode=real для всех роботов
4. В config.json: armed=true
5. Проверить account_id и лимиты
6. Остановить sandbox: taskkill /F /IM python.exe
7. Запустить: start_all.bat
8. Смотреть логи: logs/robot.log
```

## Первые дни

- Начать с **1 робота** (не 5).
- Уменьшить `qty_limit` и `max_position_rub` в 5-10 раз.
- Смотреть каждую сделку вручную.
- Через неделю без сбоев - добавить остальных.

## Что делать при проблемах

- **401** - токен истёк. Робот сам остановится, увидишь алерт.
- **30079** - биржа закрыта. Робот сам спит.
- **429** - rate limit. Робот сам ждёт.
- **Массовые ошибки** - остановить (taskkill), проверить логи.

## Чего НЕ делать

- Не запускать 5 роботов сразу в real на большом капитале.
- Не ставить `armed=true` до полной проверки config.
- Не отключать daily_loss_limit, max_drawdown, velocity_limit.
- Не игнорировать desktop-алерты.

## Статус на 2026-10-10

### Готово ✅

- [x] Все защиты настроены в config.json
- [x] risk_per_trade_pct=0.15 (15% на сделку)
- [x] daily_loss_limit=0.05, max_drawdown=0.20, velocity_limit=0.03
- [x] use_limit=true, limit_offset=0.002
- [x] Preflight через GetInstrument (apiTradeAvailableFlag)
- [x] Token-expiry detection (401/40003 -> halt)
- [x] Trailing stop двигается на бирже
- [x] minPriceIncrement rounding
- [x] Partial fill safe (executed_qty/price)
- [x] Risk state persistent (peak, day_equity)
- [x] 73 теста, все зелёные
- [x] Live-проверка: gap, stop-loss, market fallback, trailing stop
- [x] Документация: README, BACKTESTS, MASS_TEST, ROBOT_V2, REAL_TRANSITION

### Осталось сделать ❌

- [ ] Выпустить production-токен (Full-access)
- [ ] Заменить token.txt на production
- [ ] В config.json: mode=real (5 роботов)
- [ ] В config.json: armed=true
- [ ] Первые 3-7 дней: 1 робот, малый капитал

### Перед запуском real

1. Остановить sandbox: taskkill /F /IM python.exe
2. Заменить token.txt
3. mode=real, armed=true в config.json
4. start_all.bat
5. Смотреть logs/robot.log первые часы
