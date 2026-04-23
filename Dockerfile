# syntax=docker/dockerfile:1

# --- Stage 1: Compile Tailwind CSS (downloads correct binary for build host arch) ---
FROM --platform=$BUILDPLATFORM debian:bookworm-slim AS css-builder
ARG BUILDARCH
ARG TAILWIND_VERSION=4.2.2
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
RUN BINARY="tailwindcss-linux-$([ "$BUILDARCH" = "arm64" ] && echo arm64 || echo x64)" && \
    curl -fsSL "https://github.com/tailwindlabs/tailwindcss/releases/download/v${TAILWIND_VERSION}/${BINARY}" \
      -o /usr/local/bin/tailwindcss && \
    chmod +x /usr/local/bin/tailwindcss
WORKDIR /app
COPY static/css/main.css ./static/css/main.css
COPY templates/ ./templates/
RUN tailwindcss -i static/css/main.css -o static/css/output.css --minify

# --- Stage 2: Install Python dependencies ---
FROM python:3.13-slim AS deps-builder
RUN apt-get update && apt-get install -y --no-install-recommends gcc libffi-dev \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir "poetry==2.3.2" "poetry-plugin-export"
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN python -m venv /venv && \
    poetry export -f requirements.txt --without dev --without-hashes | \
    /venv/bin/pip install --no-cache-dir -r /dev/stdin

# --- Stage 3: Runtime image (ARM64-compatible) ---
FROM python:3.13-slim
RUN apt-get update && apt-get install -y --no-install-recommends openssl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=deps-builder /venv /venv
ENV PATH="/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Application source (no tailwindcss binary, no docs, no tests)
COPY main.py ./
COPY logic/ ./logic/
COPY routes/ ./routes/
COPY templates/ ./templates/
COPY static/ ./static/
COPY config/__init__.py config/settings.py config/templates.py ./config/

# Compiled CSS from css-builder (overrides any stale output.css)
COPY --from=css-builder /app/static/css/output.css ./static/css/output.css

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
