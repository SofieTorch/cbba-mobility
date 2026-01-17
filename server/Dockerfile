FROM python:3.13-slim

WORKDIR /app

# Install system dependencies for psycopg, geoalchemy2, and VS Code dev containers
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    libgeos-dev \
    git \
    curl \
    wget \
    procps \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --frozen --no-dev || uv sync

# Copy application code
COPY . .

EXPOSE 8000

ENV PORT=8000

CMD uv run alembic upgrade head && uv run uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
