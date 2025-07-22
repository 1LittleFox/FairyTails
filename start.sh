#!/bin/bash
# Выходим при любой ошибке
set -e

echo "🚀 Запуск приложения..."

# Проверяем подключение к БД (опционально, для PostgreSQL/MySQL)
echo "📡 Проверяем подключение к базе данных..."

# Применяем миграции Alembic
echo "🔄 Применяем миграции базы данных..."
alembic upgrade head

# Проверяем успешность миграций
if [ $? -eq 0 ]; then
    echo "✅ Миграции успешно применены"
else
    echo "❌ Ошибка при применении миграций"
    exit 1
fi

echo "🌟 Запускаем FastAPI сервер..."
exec gunicorn app.main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --timeout 120 --bind 0.0.0.0:$PORT