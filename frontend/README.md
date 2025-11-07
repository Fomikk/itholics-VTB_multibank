# FinGuru Frontend

React приложение с TypeScript для отображения агрегированных финансовых данных и мини-игры для активации кешбека.

## Установка

### Windows

Если возникают проблемы с установкой (ошибки EBUSY, EPERM):

1. Закройте все процессы, которые могут использовать файлы (IDE, терминалы)
2. Удалите `node_modules` и `package-lock.json`:
   ```bash
   Remove-Item -Recurse -Force node_modules
   Remove-Item -Force package-lock.json
   ```
3. Установите зависимости:
   ```bash
   npm install
   ```

Если проблема с esbuild (отсутствует @esbuild/win32-x64):
```bash
npm install esbuild --save-dev
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
