# Python 3.12+ base image
FROM python:3.12-slim@sha256:3e3d6b8e9c57e1c5f7731e2c7d9d7e3e3c3e3e3e3e3e3e3e3e3e3e3e3e3e3e3

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install UV package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY .python-version* ./

# Install Python dependencies
RUN uv sync --no-dev --no-install-project

# Copy source code
COPY src/ ./src/
COPY tests/ ./tests/

# Expose ports
# 8000: Notifier service (FastAPI)
# 8080: Sentinel health check
EXPOSE 8000 8080

# Health check using Python stdlib
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Default command runs the notifier service
CMD ["uv", "run", "uvicorn", "notifier_service:app", "--host", "0.0.0.0", "--port", "8000"]
