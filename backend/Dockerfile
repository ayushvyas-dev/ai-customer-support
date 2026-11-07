# Multi-stage lightweight Python Dockerfile for Render Free Tier
FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered output for fast logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies (curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and knowledge base
COPY app/ ./app/
COPY knowledge_base/ ./knowledge_base/
COPY scripts/ ./scripts/

# Create a non-root user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port (Render sets $PORT dynamically, defaults to 8000)
EXPOSE 8000

# Run uvicorn bound to 0.0.0.0 and the dynamic Render $PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

