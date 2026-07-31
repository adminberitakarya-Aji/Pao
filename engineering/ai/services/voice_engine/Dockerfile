# Multi-stage build for Voice Engine
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy workspace files
COPY engineering/ai/pyproject.toml engineering/ai/uv.lock* ./
COPY engineering/ai/shared ./shared
COPY engineering/ai/services/voice_engine ./voice_engine

# Install dependencies
RUN uv sync --no-dev --frozen

# Runtime stage
FROM python:3.11-slim as runtime

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash --uid 1000 appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /app/.venv .venv
COPY --from=builder /app/shared ./shared
COPY --from=builder /app/voice_engine ./voice_engine

# Set ownership
RUN chown -R appuser:appuser /app

USER appuser

# Environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/shared:/app/voice_engine/src"
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8008

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8008/api/v1/health/live', timeout=5.0)"

# Run the service
CMD ["python", "-m", "voice_engine.main"]