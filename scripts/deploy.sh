#!/bin/bash

set -Eeuo pipefail

APP_DIR="/opt/millwater"

cd "$APP_DIR"

echo "=================================="
echo "Starting production deployment"
echo "=================================="

echo "Pulling latest prod..."

git fetch origin prod
git checkout prod
git reset --hard origin/prod

echo "Current commit:"
git rev-parse --short HEAD

echo "Building Docker images..."

docker compose build

echo "Running migrations..."

docker compose run --rm app alembic upgrade head

echo "Starting services..."

docker compose up -d --remove-orphans

echo "Removing unused images..."

docker image prune -f

echo "Checking containers..."

docker compose ps

echo "=================================="
echo "Deployment completed"
echo "=================================="