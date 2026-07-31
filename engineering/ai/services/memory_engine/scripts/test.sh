#!/bin/bash
# Test script for Memory Engine

set -e

echo "🧪 Running Memory Engine tests..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    pip install uv
fi

# Install test dependencies
echo "📦 Installing test dependencies..."
uv pip install -e ".[dev]"

# Run linting
echo "🔍 Running linter..."
uv run ruff check src/ tests/

# Run type checking
echo "📝 Running type checker..."
uv run mypy src/

# Run unit tests
echo "🏃 Running unit tests..."
uv run pytest tests/unit/ -v --cov=memory_engine --cov-report=term-missing --cov-report=html

# Run integration tests
echo "🔗 Running integration tests..."
uv run pytest tests/integration/ -v

# Run all tests
echo "📊 Running all tests with coverage..."
uv run pytest tests/ -v --cov=memory_engine --cov-report=term-missing --cov-report=html --cov-fail-under=80

echo "✅ All tests passed!"