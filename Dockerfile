# Python 3.12+ base image
FROM python:3.12-slim

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

# Copy project files
COPY pyproject.toml ./
COPY .python-version* ./

# Copy source code BEFORE install (editable install needs source tree)
COPY src/ ./src/

# Install Python dependencies
RUN uv sync --no-dev --no-install-project

# Expose ports
# 8000: Notifier service (FastAPI)
# 8080: Sentinel health check
EXPOSE 8000 8080

# Health check using Python stdlib
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Default command runs the notifier service
CMD ["uv", "run", "uvicorn", "notifier_service:app", "--host", "0.0.0.0", "--port", "8000"]
