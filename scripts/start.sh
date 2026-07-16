#!/bin/bash
# Startup script for the application
# Runs migrations and starts the FastAPI server

set -e

echo "🔧 Creating required directories..."
mkdir -p uploads
mkdir -p data

echo "🗄️  Running database migrations..."
poetry run alembic upgrade head

echo "🚀 Starting FastAPI server..."
poetry run uvicorn src.app.main:app --host 0.0.0.0 --port 8000
