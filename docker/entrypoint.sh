#!/bin/bash
set -e

# Runs as root (the container default) to fix ownership on volume-mounted
# paths — Docker creates named volumes root-owned on first use, and upgrades
# from an older root-only image leave existing data root-owned too. Privileges
# are dropped via gosu at the very end, right before exec'ing the app: the
# running server process never holds root.
mkdir -p config blueprints "$HOME/.config/sc-archive" "$HOME/sc-archive"
chown -R aegis:aegis config blueprints "$HOME/.config/sc-archive" "$HOME/sc-archive"

# Write Docker-appropriate settings.json on first start.
# SettingsManager would default to localhost:3000 for Gotenberg — unusable in Docker.
if [ ! -s config/settings.json ]; then
    python3 - << 'PYEOF'
import json, os
settings = {
    "neural_link_enabled": False,
    "pdf_branding_enabled": False,
    "gotenberg_ip": "http://gotenberg:3000",
    "ollama_ip": os.getenv("OLLAMA_IP", "http://localhost:11434"),
    "workspace_base": os.path.expanduser("~/sc-archive"),
    "models": {
        "neural_hint": "qwen2.5-coder:7b",
        "neural_scan": "qwen2.5-coder:7b",
        "mermaid_synthesis": "qwen2.5-coder:7b"
    }
}
os.makedirs("config", exist_ok=True)
with open("config/settings.json", "w") as f:
    json.dump(settings, f, indent=4)
print("[sc-archive] config/settings.json initialized with Docker defaults")
PYEOF
    chown aegis:aegis config/settings.json
fi

# Generate persistent session key (stored in userdata volume)
KEY_FILE="$HOME/.config/sc-archive/session.key"
if [ ! -f "$KEY_FILE" ]; then
    openssl rand -hex 32 > "$KEY_FILE"
    chmod 600 "$KEY_FILE"
    chown aegis:aegis "$KEY_FILE"
    echo "[sc-archive] Session key generated"
fi
export AEGIS_SECRET_KEY="$(cat "$KEY_FILE")"

exec gosu aegis "$@"
