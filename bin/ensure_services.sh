#!/bin/bash
# AEGIS_SERVICE_BOOTSTRAP: verifica che Gotenberg e Ollama siano raggiungibili
# prima dell'avvio del server. Solo diagnostica, nessuna creazione né avvio:
# entrambi sono servizi esterni, gestiti fuori da questo progetto (nativi,
# systemd, o container di un altro progetto/stack). L'endpoint di ciascuno
# va configurato in Settings (o config/settings.json, gotenberg_ip/ollama_ip).
#
# Gotenberg creava in passato un container di progetto dedicato
# (md2fastpdf-gotenberg) come fallback — rimosso: troppi bug di
# sovrapposizione con container Gotenberg condivisi tra più app della stessa
# macchina (vedi docs/Stato-dell-Arte.md).
#
# Ollama va sempre nativo, mai in Docker (vedi docs/configurazione-docker.md)
# — qui viene solo controllato, mai avviato.
set -u

# Root del progetto risolta dalla posizione dello script, non dalla CWD di chi
# lo lancia — se invocato da una directory diversa (o CWD imprevista) un path
# relativo a "config/settings.json" fallirebbe silenziosamente e userebbe
# sempre i default hardcoded, senza nessun avviso.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SETTINGS_FILE="${SCRIPT_DIR}/../config/settings.json"

_read_config() {
    # Legge config/settings.json con solo la stdlib (nessuna dipendenza da
    # anyio/poetry: questo script può girare prima che il venv sia pronto).
    python3 - "$1" "$2" "$SETTINGS_FILE" <<'PYEOF'
import json
import sys

key, default_url, settings_file = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    with open(settings_file) as f:
        data = json.load(f)
    url = data.get(key) or default_url
except (FileNotFoundError, json.JSONDecodeError):
    url = default_url

print(url)
PYEOF
}

_check_service() {
    local label="$1" settings_key="$2" default_url="$3" health_path="$4"

    local url
    url="$(_read_config "$settings_key" "$default_url")"

    # Retry: al boot l'istanza (nativa o container) può metterci qualche
    # secondo a rispondere.
    for _ in $(seq 1 15); do
        if curl -sf -m 2 "${url%/}${health_path}" >/dev/null 2>&1; then
            echo "[${label}] istanza attiva su ${url}"
            return 0
        fi
        sleep 1
    done

    echo "[${label}] ATTENZIONE: nessuna istanza raggiungibile su ${url}${health_path} — configura ${settings_key} da Settings e avvia il servizio manualmente"
}

_check_service "gotenberg" "gotenberg_ip" "http://localhost:3000" "/health"
_check_service "ollama" "ollama_ip" "http://localhost:11434" "/api/tags"
