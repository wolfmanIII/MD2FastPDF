#!/bin/bash

# Kill all background processes on exit
trap "kill 0" EXIT

echo "--- STARTING MD2FastPDF INDUSTRIAL TERMINAL ---"

# Compile CSS once at start
./tailwindcss -i static/css/main.css -o static/css/output.css

# Start Tailwind watcher in background
./tailwindcss -i static/css/main.css -o static/css/output.css --watch &

# Load or generate persistent session key
KEY_FILE="$HOME/.config/sc-archive/session.key"
if [ ! -f "$KEY_FILE" ]; then
    mkdir -p "$(dirname "$KEY_FILE")"
    openssl rand -hex 32 > "$KEY_FILE"
    chmod 600 "$KEY_FILE"
fi
export AEGIS_SECRET_KEY="$(cat "$KEY_FILE")"

# Start FastAPI server
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
