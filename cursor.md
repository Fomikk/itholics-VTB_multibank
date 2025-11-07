
```markdown
# FinGuru — Multibank + Cashback Game (Cursor Context)

**Цель:** реализовать мультибанковский агрегатор (VBank, ABank, SBank) и простую мини-игру для активации повышенного кэшбэка на выбранную категорию.  
**Что важно:** глубоко и корректно использовать предоставленные OpenAPI, аккуратно работать с токенами (bank_token/client_token), показывать единый дашборд.

---

## 1) Текущее состояние проекта

**Структура**
```

backend/
app/
**init**.py
main.py
settings.py
routers/
health.py         # /health
banks.py          # (TODO)
services/
abank.py          # (TODO)
sbank.py          # (TODO)
vbank.py          # (TODO)
clients/
abank_client.py   # (TODO) — вызовы OpenAPI
sbank_client.py   # (TODO)
vbank_client.py   # (TODO)
pyproject.toml | requirements.txt

frontend/
src/
App.tsx
pages/Dashboard.tsx      # (TODO)
api/                     # (опц. автогенерация клиентов из OpenAPI)
widgets/                 # (TODO)
package.json
vite.config.ts

openapi/
abank.json
sbank.json
vbank.json

docs/
architecture.drawio        # (опционально)
demo-screens/              # (опционально)

.env.sample
.gitignore
README.md
CONTRIBUTING.md
LICENSE
cursor.md

```

**Переменные окружения** (`.env.sample`)
```

APP_ENV=dev
REQUESTING_BANK_ID=team200

VBANK_BASE_URL=[https://vbank.open.bankingapi.ru](https://vbank.open.bankingapi.ru)
ABANK_BASE_URL=[https://abank.open.bankingapi.ru](https://abank.open.bankingapi.ru)
SBANK_BASE_URL=[https://sbank.open.bankingapi.ru](https://sbank.open.bankingapi.ru)

VBANK_CLIENT_ID=
VBANK_CLIENT_SECRET=
ABANK_CLIENT_ID=
ABANK_CLIENT_SECRET=
SBANK_CLIENT_ID=
SBANK_CLIENT_SECRET=

HTTP_TIMEOUT_SECONDS=15
CACHE_TTL_SECONDS=300

````

---

## 2) Технические принципы

- **Бэкенд:** FastAPI, httpx, Pydantic.  
- **Фронтенд:** React + Vite + TypeScript, Recharts (или аналог) для графиков.  
- **Безопасность:** не логируем токены, не коммитим `.env`.  
- **Слои:** `clients` (сырой HTTP к банкам) → `services` (бизнес-логика агрегации) → `routers` (API нашего бэкенда).  
- **Коды банков:** `vbank`, `abank`, `sbank`.  
- **Заголовки межбанка:** `Authorization: Bearer <bank_token>`, `X-Requesting-Bank: <REQUESTING_BANK_ID>`, `X-Consent-Id: <consent_id>` (когда требуется).

---

## 3) Минимальный функционал для демо

### 3.1 Бэкенд API (наше)

1. `GET /health` — уже есть, возвращает `{ "status": "ok" }`.

2. `POST /api/tokens/{bank}`  
   **Назначение:** получить и закэшировать `bank_token` для `vbank|abank|sbank`.  
   **Вход:** `{}` (креды берём из env).  
   **Выход:** `{ access_token, expires_in, bank }`.  
   **Примечание:** запрос к `/{bank}/auth/bank-token?client_id=...&client_secret=...`.

3. `POST /api/consents/accounts`  
   **Назначение:** создать согласие для межбанкового доступа к счетам.  
   **Вход:** `{ bank: "vbank"|"abank"|"sbank", client_id: "team200-1", permissions: [...] }`.  
   **Выход:** `{ consent_id, status, auto_approved }`.  
   **Заголовки к банку:** `Authorization: Bearer <bank_token>`, `X-Requesting-Bank: team200`.

4. `GET /api/accounts/aggregate?client_id=team200-1`  
   **Назначение:** собрать все счета пользователя из всех банков.  
   **Внутри:** при необходимости создать согласие и использовать его в `X-Consent-Id`.  
   **Выход:** массив унифицированных аккаунтов:
   ```ts
   type Account = {
     account_id: string;
     bank: "vbank"|"abank"|"sbank";
     currency: string;
     account_type: string;
     nickname?: string;
     servicer?: any;
   };
````

5. `GET /api/transactions/aggregate?client_id=team200-1&from=...&to=...`
   **Назначение:** собрать транзакции по всем счетам.
   **Выход:** массив унифицированных транзакций (id, account_id, amount, currency, bookingDate, description, mcc?).

6. `GET /api/analytics/summary?client_id=team200-1&period=30d`
   **Назначение:** вернуть агрегаты для дашборда: общий баланс, расходы по категориям, топ-траты, недельная динамика.

7. `POST /api/cashback/activate`
   **Назначение:** активировать повышенный кэшбек по категории после выигрыша в мини-игре.
   **Вход:** `{ client_id, category, bonus_percent, valid_until }`.
   **Выход:** `{ activated: true }`.
   **Пока без реального списания — просто сохраняем и отдаём фронту состояние бонусов.**

### 3.2 Фронтенд (PWA)

* Страница `Dashboard`:

  * **Cards:** Net Worth, последние транзакции.
  * **Charts:** расходы по категориям (Pie), динамика расходов (Line).
  * **CTA:** «Активировать кэшбек» → переход на страницу мини-игры.
* Страница `CashbackGame`: простая игра (memory/лови-монеты). По успешному завершению — `POST /api/cashback/activate`.

---

## 4) Работа с внешними API (краткие рецепты)

### 4.1 Получение bank_token

`POST {BANK_BASE_URL}/auth/bank-token?client_id=...&client_secret=...`
**Ответ:** `{ "access_token": "...", "token_type": "bearer", "client_id": "...", "expires_in": 86400 }`

### 4.2 Согласие на доступ к счетам

`POST {BANK_BASE_URL}/account-consents/request`
**Headers:**

* `Authorization: Bearer <bank_token>`
* `X-Requesting-Bank: team200`
  **Body (пример):**

```json
{
  "client_id": "team200-1",
  "permissions": ["ReadAccountsDetail", "ReadBalances"],
  "reason": "Aggregation for FinGuru",
  "requesting_bank": "team200",
  "requesting_bank_name": "FinGuru App"
}
```

**Ответ (ожидаемо):** `{ status, consent_id, auto_approved }`
**Далее:** `GET /accounts?client_id=...` с заголовками `Authorization`, `X-Requesting-Bank`, `X-Consent-Id`.

### 4.3 Счета, балансы, транзакции

* `GET {BANK_BASE_URL}/accounts?client_id=...`
* `GET {BANK_BASE_URL}/accounts/{account_id}`
* `GET {BANK_BASE_URL}/accounts/{account_id}/balances`
* `GET {BANK_BASE_URL}/accounts/{account_id}/transactions?from_booking_date_time=...&to_booking_date_time=...`

---

## 5) Задачи для Cursor (пошаговые Prompt’ы)

### Backend / Clients

1. **Создай httpx-клиент и обёртки** в `backend/app/clients/*_client.py`:

   * `get_bank_token()`
   * `get_accounts(client_id, consent_id?)`
   * `get_account_details(account_id, ...)`
   * `get_balances(account_id, ...)`
   * `get_transactions(account_id, from, to, ...)`
   * `request_accounts_consent(client_id, permissions)`
   * Общий helper: добавлять `Authorization`, `X-Requesting-Bank`, `X-Consent-Id` при необходимости.

2. **Реализуй сервис агрегации** в `backend/app/services/*.py`:

   * Нормализация структур счетов/транзакций к единому типовому виду.
   * Кеширование токенов по банку с учётом `expires_in`.

3. **Роуты** в `backend/app/routers/banks.py`:

   * Все эндпоинты из раздела 3.1
   * Обработка ошибок: таймаут→`503`, 403 `CONSENT_REQUIRED`→создать согласие и повторить.

### Frontend

1. **API слой** `frontend/src/api/*` (можно автогенерацией из `openapi/*.json`).
2. **Dashboard** `pages/Dashboard.tsx`:

   * Вызовы `/api/analytics/summary`, `/api/transactions/aggregate`.
   * Графики и таблицы.
3. **CashbackGame** `pages/CashbackGame.tsx`:

   * Игра (простая реализация), на успех — `POST /api/cashback/activate`.

---

## 6) Проверки и критерии готовности

* Бэкенд:

  * `/health` → 200 OK.
  * `/api/accounts/aggregate` возвращает массив ≥ 1 из хоть одного банка песочницы.
  * Ретраи и внятные ошибки при недоступности банка.
* Фронтенд:

  * Дашборд рисует суммарный баланс и графики.
  * Игра работает, по успеху состояние «кэшбек активирован» сохраняется и отображается.
* Репозиторий:

  * `.env.sample` есть, `.env` не в репо.
  * `README.md` описывает запуск.
  * `openapi/*.json` доступны.

---

## 7) Быстрый старт локально

**Backend**

```bash
cd backend
# если pip
pip install -r requirements.txt
uvicorn app.main:app --reload
# если poetry
poetry install
poetry run uvicorn app.main:app --reload
```

**Frontend**

```bash
cd frontend
npm i
npm run dev
```

---

## 8) Ограничения и упрощения для демо

* Кэшбек — виртуальный, без реальных расчётов списаний/партнёрских выплат.
* Аналитика категорий — начальные эвристики (по описанию/MCC), без ML.
* Для межбанковских данных допускается автосоздание согласия в песочнице.

---

## 9) Что НЕ делаем сейчас

* Монетизация/подписки — исключено.
* Продвинутый ИИ-советник — позже.
* Хранение конфиденциальных данных карт — запрещено.

---

## 10) Полезные подсказки для Cursor

* «Сгенерируй httpx-клиент для VBank на основе `openapi/vbank.json`, функции: get_bank_token, get_accounts, get_transactions. Добавь заголовки Authorization/X-Requesting-Bank/X-Consent-Id по параметрам функции.»
* «Реализуй `GET /api/accounts/aggregate` — зови клиентов V/A/S параллельно, нормализуй формат, верни единый массив. При 403 CONSENT_REQUIRED попробуй создать согласие и повторить запрос один раз.»
* «Сделай страницу `Dashboard.tsx` с карточками суммарного баланса и графиками расходов (Line + Pie) на данных `/api/analytics/summary`.»

---

```
```
