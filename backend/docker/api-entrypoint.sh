#!/usr/bin/env bash

set -e

echo "========================================"
echo "Starting FastAPI API..."
echo "========================================"

# Create runtime directories if they don't exist
mkdir -p app/storage/uploads
mkdir -p app/storage/outputs
mkdir -p logs

echo "Launching Uvicorn..."

exec uv run uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000