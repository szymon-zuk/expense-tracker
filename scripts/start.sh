#!/bin/bash

set -e

echo "Waiting for database to be ready..."
while ! nc -z db 5432; do
  sleep 0.1
done

echo "Database is ready. Running migrations..."
uv run alembic upgrade head

echo "Starting FastAPI application with fastapi dev..."
exec uv run fastapi dev backend/app/main.py --host 0.0.0.0 --port 8000 