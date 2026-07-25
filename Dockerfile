# syntax=docker/dockerfile:1

# --- Stage 1: Compile Tailwind CSS (downloads correct binary for build host arch) ---
# debian:bookworm-slim, pinned by digest for reproducible builds (multi-arch index, includes arm64/v8)
FROM --platform=$BUILDPLATFORM debian:bookworm-slim@sha256:7b140f374b289a7c2befc338f42ebe6441b7ea838a042bbd5acbfca6ec875818 AS css-builder
ARG BUILDARCH
ARG TAILWIND_VERSION=4.2.2
# sha256 of the official v4.2.2 release binaries — update together with TAILWIND_VERSION
ARG TAILWIND_SHA256_X64=4ab84f2b496c402d3ec4fd25e0e5559fe1184d886dadae8fb4438344ec044c22
ARG TAILWIND_SHA256_ARM64=ad627e77b496cccada4a6e26eafff698ef0829081e575a4baf3af8524bb00747
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN BINARY="tailwindcss-linux-$([ "$BUILDARCH" = "arm64" ] && echo arm64 || echo x64)" && \
    EXPECTED_SHA256="$([ "$BUILDARCH" = "arm64" ] && echo "$TAILWIND_SHA256_ARM64" || echo "$TAILWIND_SHA256_X64")" && \
    curl -fsSL "https://github.com/tailwindlabs/tailwindcss/releases/download/v${TAILWIND_VERSION}/${BINARY}" \
      -o /usr/local/bin/tailwindcss && \
    echo "${EXPECTED_SHA256}  /usr/local/bin/tailwindcss" | sha256sum -c - && \
    chmod +x /usr/local/bin/tailwindcss
WORKDIR /app
COPY static/css/ ./static/css/
COPY templates/ ./templates/
RUN tailwindcss -i static/css/main.css -o static/css/output.css --minify

# --- Stage 2: Install Python dependencies ---
# python:3.13-slim, pinned by digest for reproducible builds (multi-arch index, includes arm64/v8)
FROM python:3.13-slim@sha256:6771159cd4fa5d9bba1258caf0b82e6b73458c694d178ad97c5e925c2d0e1a91 AS deps-builder
RUN apt-get update && apt-get install -y --no-install-recommends gcc libffi-dev \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir "poetry==2.3.2" "poetry-plugin-export"
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN python -m venv /venv && \
    poetry export -f requirements.txt --without dev --without-hashes | \
    /venv/bin/pip install --no-cache-dir -r /dev/stdin

# --- Stage 3: Runtime image (ARM64-compatible) ---
# python:3.13-slim, pinned by digest for reproducible builds (multi-arch index, includes arm64/v8)
FROM python:3.13-slim@sha256:6771159cd4fa5d9bba1258caf0b82e6b73458c694d178ad97c5e925c2d0e1a91
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
COPY blueprints/ ./blueprints/

# Compiled CSS from css-builder (overrides any stale output.css)
COPY --from=css-builder /app/static/css/output.css ./static/css/output.css

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=3 \
    CMD python3 -c "import urllib.request as u; u.urlopen('http://localhost:8000/login', timeout=2)" || exit 1
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
