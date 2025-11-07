# FinGuru Backend

FastAPI приложение для агрегации данных из нескольких банков через Open Banking API.

## Установка

1. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` на основе `.env.sample` и заполните необходимые переменные окружения.

## Запуск

```bash
uvicorn app.main:app --reload
```

API будет доступно по адресу: http://localhost:8000

Документация API: http://localhost:8000/docs

## Структура проекта

- `app/main.py` - точка входа приложения
- `app/settings.py` - настройки приложения
- `app/routers/` - API роуты
- `app/services/` - бизнес-логика
- `app/clients/` - HTTP клиенты для банковских API
- `app/core/` - общие утилиты и исключения
