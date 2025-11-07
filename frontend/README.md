# FinGuru Frontend

React приложение с TypeScript для отображения агрегированных финансовых данных и мини-игры для активации кешбека.

## Установка

### Windows

Если возникают проблемы с установкой (ошибки EBUSY, EPERM), используйте:

```bash
npm install --ignore-scripts
```

Или закройте все процессы, которые могут использовать файлы (IDE, терминалы), и попробуйте снова:

```bash
npm install
```

### Linux/Mac

```bash
npm install
```

## Запуск

```bash
npm run dev
```

Приложение будет доступно по адресу: http://localhost:5173

## Сборка

```bash
npm run build
```

## Структура проекта

- `src/App.tsx` - главный компонент приложения
- `src/pages/` - страницы приложения (Dashboard, CashbackGame)
- `src/api/` - клиент для работы с API
- `src/components/` - переиспользуемые компоненты

## Технологии

- React 18
- TypeScript
- Vite
- Tailwind CSS
- Recharts (графики)
- Axios (HTTP клиент)
