# =============================================================================
# Worker Dockerfile - Celery worker for dev and prod
# =============================================================================
# Usage:
#   Dev:  docker build --target dev -t worker:dev .
#   Prod: docker build --target prod -t worker:prod .
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Base - Common dependencies
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install analysis engine requirements first (changes less frequently)
COPY analysis_engine/requirements.txt /app/analysis_engine/requirements.txt
RUN pip install --no-cache-dir -r /app/analysis_engine/requirements.txt

# Copy and install API requirements (includes Celery dependencies)
COPY api/requirements.txt /app/api/requirements.txt
RUN pip install --no-cache-dir -r /app/api/requirements.txt

# Copy application code
COPY analysis_engine /app/analysis_engine
COPY api /app/api

# Create output directory
RUN mkdir -p /app/data/output

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

WORKDIR /app/api

# -----------------------------------------------------------------------------
# Stage 2: Development - Celery worker with auto-reload
# -----------------------------------------------------------------------------
FROM base AS dev

# Dev uses volume mounts for hot reload
CMD ["celery", "-A", "api.celery_app", "worker", "--loglevel=info", "--concurrency=2"]

# -----------------------------------------------------------------------------
# Stage 3: Production - Optimized Celery worker
# -----------------------------------------------------------------------------
FROM base AS prod

# Health check - verify celery worker is responding
HEALTHCHECK --interval=60s --timeout=30s --start-period=30s --retries=3 \
    CMD celery -A api.celery_app inspect ping -d celery@$HOSTNAME || exit 1

# Run celery worker with production settings
# - concurrency: number of worker processes
# - prefetch-multiplier: tasks to prefetch per worker (1 = fair scheduling for long tasks)
# - max-tasks-per-child: restart worker after N tasks (prevents memory leaks)
CMD ["celery", "-A", "api.celery_app", "worker", \
    "--loglevel=info", \
    "--concurrency=2", \
    "--prefetch-multiplier=1", \
    "--max-tasks-per-child=50"]
