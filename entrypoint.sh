set -e

echo "Применение миграций..."
alembic upgrade head
echo "---"

echo "Запуск uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"
