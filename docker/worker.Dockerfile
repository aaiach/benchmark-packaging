FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
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
RUN mkdir -p /app/output

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

WORKDIR /app/api
