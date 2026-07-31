#!/bin/bash
# Development script for Memory Engine

set -e

echo "🚀 Starting Memory Engine in development mode..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    pip install uv
fi

# Install dependencies
echo "📦 Installing dependencies..."
uv pip install -e ".[dev]"

# Run database migrations (if any)
echo "🗄️  Running migrations..."
# python -m alembic upgrade head

# Start the development server
echo "🌐 Starting server on http://localhost:8004..."
uv run uvicorn memory_engine.main:app --host 0.0.0.0 --port 8004 --reload