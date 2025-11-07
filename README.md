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

## Как запустить

### Локально (без Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### С Docker

**Production:**
```bash
# Создайте .env файл с необходимыми переменными (см. .env.sample)
docker compose up -d
```

**Development:**
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

После запуска:
- Frontend: http://localhost (или http://localhost:5173 в dev режиме)
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432

