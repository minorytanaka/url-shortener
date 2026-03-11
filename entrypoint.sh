set -e

echo "Applying migrations..."
alembic upgrade head
echo "---"

echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"
