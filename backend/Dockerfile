# Production Dockerfile for Render Web Service
FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered output for fast logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies (curl for container healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies first to take advantage of Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code, knowledge base markdown files, and scripts
COPY app/ ./app/
COPY knowledge_base/ ./knowledge_base/
COPY scripts/ ./scripts/

# Create a dedicated non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose default port (Render injects $PORT at runtime)
EXPOSE 8000

# Health check using FastAPI /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Launch uvicorn with exec so it receives SIGTERM for graceful shutdown on Render
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
