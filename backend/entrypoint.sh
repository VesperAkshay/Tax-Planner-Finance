#!/bin/sh
set -e

echo "==> Personal Finance + Tax Regime Planner Backend Starting..."
echo "==> Running database migrations via Alembic..."

# Execute Alembic migrations to bring Neon PostgreSQL schema to latest revision
alembic -c backend/alembic.ini upgrade head || {
    echo "Warning: Alembic migration encountered an issue or database is starting up. Retrying in 5 seconds..."
    sleep 5
    alembic -c backend/alembic.ini upgrade head
}

echo "==> Migrations completed successfully."

PORT="${PORT:-8000}"

echo "==> Launching single-process Uvicorn ASGI server on port ${PORT}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
