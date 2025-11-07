# Contributing & AI Coding Rules

- Пишем **чистый, минимальный MVP-код**, без лишних абстракций.
- Для backend:
  - Python 3.11+, FastAPI, httpx, pydantic v2, sqlalchemy.
  - Линт/формат: ruff + black. Типизация обязательна.
  - Ошибки API банков заворачиваем в `HTTPException` с понятным `detail`.
  - Не хранить чувствительные данные клиентов. Токены — только в зашифрованном хранилище/`.env`.
- Для web:
  - React + Vite, TypeScript, Zustand (или Redux Toolkit) для стейта.
  - Компоненты: shadcn/ui или MUI; графики — Recharts.
  - PWA манифест позже; сейчас — упор на дашборд и игру.
- Коммиты: conventional commits (`feat:`, `fix:`, `chore:`).
