#!/bin/bash

# Kill all background processes on exit
trap "kill 0" EXIT

echo "--- STARTING STYLE BUILDING ---"

./tailwindcss -i static/css/main.css -o static/css/output.css