# FinGuru (itholics-VTB_multibank)

Мультибанковское PWA + API для агрегации счетов/транзакций и мини-игры с кешбеком.

## Цель
- Подключать банки через Open Banking API (в т.ч. ГОСТ-шлюз).
- Агрегировать счета/балансы/транзакции (ABank, SBank sandbox).
- Показать дашборд (баланс, динамика, категории).
- Дать мини-игру → активировать повышенный кешбек в категории (демо-логика).

## Архитектура (MVP)
- **backend/** FastAPI:
  - adapters/: ABank, SBank (работают по их OpenAPI).
  - services/: Aggregation, Cashback, Games.
  - api/: REST-роуты `/auth`, `/accounts`, `/transactions`, `/cashback`, `/game`.
  - core/: конфиги, клиенты HTTP, обработка ошибок, валидация.
- **web/** React (Vite):
  - Дашборд (Net Worth, графики, категории), список транзакций, экран мини-игры.
- **db:** PostgreSQL (пользователи, соединения с банками, кэш транзакций, игровые бонусы).
- **интеграции:** JWKS валидация токенов банков при межбанковых запросах.

## Банковские спецификации (sandbox)
- `openapi/abank.json` — ABank
- `openapi/sbank.json` — SBank (требует ручное одобрение согласий)
> Файлы добавлены как есть от организаторов.

## Нефункциональные
- Ошибки/ретраи, кэш последних успешных данных.
- Безопасность: `.env` секреты, не коммитить `.env*`.
- Стиль: `black`, `ruff`, `mypy` (backend); ESLint/Prettier (web).

## Как запустить (локально)
- Backend: `uvicorn app.main:app --reload`
- Web: `npm run dev`
- Докер-компоуз: `docker compose up -d` (db + api + web)

