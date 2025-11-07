# Быстрый старт FinGuru

## Предварительные требования

- Python 3.11+
- Node.js 18+
- npm или yarn

## Запуск проекта

### 1. Backend

#### Windows (простой способ):

```bash
cd backend
start.bat
```

#### Или вручную:

```bash
# Перейдите в директорию backend
cd backend

# Создайте виртуальное окружение (если еще не создано)
python -m venv venv

# Активируйте виртуальное окружение
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt

# Создайте .env файл (скопируйте из .env.sample и заполните)
# Минимально необходимые переменные для демо:
# APP_ENV=dev
# REQUESTING_BANK_ID=team200
# VBANK_CLIENT_ID=your_client_id
# VBANK_CLIENT_SECRET=your_client_secret
# (и аналогично для ABANK и SBANK)

# Запустите сервер
uvicorn app.main:app --reload
```

Backend будет доступен на: **http://localhost:8000**

Проверьте: http://localhost:8000/health (должен вернуть `{"status":"ok"}`)

### 2. Frontend

Откройте **новый терминал**:

```bash
# Перейдите в директорию frontend
cd frontend

# Установите зависимости (если еще не установлены)
npm install

# Запустите dev сервер
npm run dev
```

Frontend будет доступен на: **http://localhost:5173**

## Проверка работы

1. Откройте браузер: http://localhost:5173
2. Dashboard должен загрузить данные (если backend запущен и настроен)
3. Если видите ошибку "Backend сервер не запущен" - проверьте, что backend работает на порту 8000

## Важно

- Backend должен быть запущен **до** открытия frontend
- Убедитесь, что порты 8000 (backend) и 5173 (frontend) свободны
- Для работы с реальными данными нужно настроить переменные окружения в `.env`

## Troubleshooting

### Ошибка 500 на frontend
- Проверьте, что backend запущен: http://localhost:8000/health
- Проверьте логи backend в терминале
- Убедитесь, что CORS настроен правильно

### Ошибка подключения
- Проверьте, что оба сервера запущены
- Проверьте настройки прокси в `vite.config.ts`
- Убедитесь, что нет конфликтов портов

