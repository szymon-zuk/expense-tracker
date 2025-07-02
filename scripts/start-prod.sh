#!/bin/bash

set -e

echo "Waiting for database to be ready..."
while ! nc -z db 5432; do
  sleep 0.1
done

echo "Database is ready. Running migrations..."
uv run alembic upgrade head

echo "Starting FastAPI application for production..."
exec uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 4 