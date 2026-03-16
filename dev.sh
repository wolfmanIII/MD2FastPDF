#!/bin/bash

# Kill all background processes on exit
trap "kill 0" EXIT

echo "--- STARTING MD2FastPDF INDUSTRIAL TERMINAL ---"

# Compile CSS once at start
./tailwindcss -i static/css/main.css -o static/css/output.css

# Start Tailwind watcher in background
./tailwindcss -i static/css/main.css -o static/css/output.css --watch &

# Start FastAPI server
pipenv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
