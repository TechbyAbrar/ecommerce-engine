#!/usr/bin/env bash

set -e

echo "========================================"
echo "Starting Celery Worker..."
echo "========================================"

mkdir -p logs

exec uv run celery \
    -A app.core.celery:celery_app \
    worker \
    --loglevel=info \
    --concurrency=1