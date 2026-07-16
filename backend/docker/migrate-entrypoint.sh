#!/usr/bin/env bash

set -e

echo "========================================"
echo "Running Alembic Migrations..."
echo "========================================"

exec uv run alembic upgrade head