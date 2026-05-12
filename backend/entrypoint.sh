#!/bin/bash
# Entrypoint script untuk auto-run migrations dan seeding

set -e

echo "Waiting for database..."
while ! nc -z db 5432; do
  sleep 1
done

echo "Database is ready!"
echo ""

# Run migrations
echo "Running Alembic migrations..."
alembic upgrade head

# Run seed script
echo "Running database seeding..."
python seed.py

# Start the FastAPI application
echo "Starting FastAPI application..."
exec "$@"
