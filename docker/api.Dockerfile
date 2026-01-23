# =============================================================================
# API Dockerfile - Flask application for dev and prod
# =============================================================================
# Usage:
#   Dev:  docker build --target dev -t api:dev .
#   Prod: docker build --target prod -t api:prod .
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

# Copy and install API requirements
COPY api/requirements.txt /app/api/requirements.txt
RUN pip install --no-cache-dir -r /app/api/requirements.txt

# Install gunicorn for production
RUN pip install --no-cache-dir gunicorn==23.0.0

# Copy application code
COPY analysis_engine /app/analysis_engine
COPY api /app/api

# Create output directory
RUN mkdir -p /app/data/output

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

WORKDIR /app/api

# Expose Flask port
EXPOSE 5000

# -----------------------------------------------------------------------------
# Stage 2: Development - Flask dev server with hot reload
# -----------------------------------------------------------------------------
FROM base AS dev

# Dev uses volume mounts, so code is overridden
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000", "--reload"]

# -----------------------------------------------------------------------------
# Stage 3: Production - Gunicorn WSGI server
# -----------------------------------------------------------------------------
FROM base AS prod

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run with gunicorn
# - workers: 2-4 x CPU cores (using 4 as default)
# - threads: for I/O bound work
# - timeout: longer for LLM API calls
CMD ["gunicorn", \
    "--bind", "0.0.0.0:5000", \
    "--workers", "2", \
    "--threads", "4", \
    "--timeout", "300", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "--capture-output", \
    "src.app:create_app()"]
