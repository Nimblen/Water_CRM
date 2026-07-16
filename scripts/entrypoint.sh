#!/bin/sh
set -e

echo "Applying migrations..."
alembic upgrade head

echo "Creating default admin..."
python -m scripts.create_superuser

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000