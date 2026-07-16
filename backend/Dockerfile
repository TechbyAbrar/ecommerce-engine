# syntax=docker/dockerfile:1.7

#############################
# Builder Stage
#############################
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first for better layer caching
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Copy project source
COPY . .

# Install project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Make entrypoint scripts executable
RUN chmod +x \
    docker/api-entrypoint.sh \
    docker/worker-entrypoint.sh \
    docker/migrate-entrypoint.sh


#############################
# Runtime Stage
#############################
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# Create non-root user
RUN groupadd -r app && useradd -r -g app app

WORKDIR /app

COPY --from=builder /app /app

RUN chown -R app:app /app

USER app

EXPOSE 8000

CMD ["./docker/api-entrypoint.sh"]