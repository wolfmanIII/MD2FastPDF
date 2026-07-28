#!/bin/bash
# AEGIS_SERVICE_BOOTSTRAP: garantisce che Gotenberg sia raggiungibile prima
# dell'avvio del server.
#
# Ollama NON è gestito da questo script: va sempre nativo, mai in Docker
# (vedi docs/configurazione-docker.md).
#
# Per Gotenberg, spesso già gestito da un container condiviso con altre app
# della stessa macchina (restart:unless-stopped proprio, definito altrove):
#   1. Se qualcosa risponde già all'endpoint configurato, viene usato così
#      com'è — non tocchiamo nulla che non abbiamo creato noi.
#   2. Se non risponde ma Docker ha comunque già un container che pubblica
#      quella porta (esiste ma sta ancora salendo — capita al boot, prima che
#      il suo restart:unless-stopped l'abbia riportato su), NON viene creato
#      un fallback di progetto: occuperebbe la porta al posto del container
#      condiviso e gli impedirebbe di ripartire quando è pronto — bug reale
#      già capitato, non un'ipotesi. Si aspetta più a lungo e poi si avvisa.
#   3. Solo se Docker non ha proprio nulla su quella porta (e l'host è locale,
#      Docker disponibile) viene creato un container dedicato al progetto,
#      con nome riconoscibile (md2fastpdf-gotenberg).
set -u

_read_config() {
    # Legge config/settings.json con solo la stdlib (nessuna dipendenza da
    # anyio/poetry: questo script può girare prima che il venv sia pronto).
    python3 - "$1" "$2" <<'PYEOF'
import json
import sys
from urllib.parse import urlparse

key, default_url = sys.argv[1], sys.argv[2]
try:
    with open("config/settings.json") as f:
        data = json.load(f)
    url = data.get(key) or default_url
except (FileNotFoundError, json.JSONDecodeError):
    url = default_url

p = urlparse(url)
print(url)
print(p.hostname or "localhost")
print(p.port or (443 if p.scheme == "https" else 80))
PYEOF
}

_ensure_service() {
    local label="$1" settings_key="$2" default_url="$3" health_path="$4" \
          container_name="$5" image="$6" internal_port="$7"

    local url host port
    { read -r url; read -r host; read -r port; } < <(_read_config "$settings_key" "$default_url")

    # Retry (non un check singolo): al boot il container "giusto" può metterci
    # qualche secondo a salire (Docker daemon appena partito) — senza questo
    # loop il primo curl falliva sempre troppo presto e lo script ne creava
    # uno nuovo, duplicato, mentre quello vero stava ancora avviandosi.
    for _ in $(seq 1 15); do
        if curl -sf -m 2 "${url%/}${health_path}" >/dev/null 2>&1; then
            echo "[${label}] istanza già attiva su ${url} — la uso così com'è"
            return 0
        fi
        sleep 1
    done

    if [[ "$host" != "localhost" && "$host" != "127.0.0.1" ]]; then
        echo "[${label}] ATTENZIONE: ${settings_key} punta a un host remoto (${host}) non raggiungibile — verificalo manualmente, nessun container locale può sostituirlo"
        return 0
    fi

    if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
        echo "[${label}] ATTENZIONE: nessuna istanza raggiungibile su ${url} e Docker non è disponibile — servizio non attivo finché non viene avviato manualmente"
        return 0
    fi

    # Un container (nostro o condiviso con altre app) che pubblica già questa
    # porta esiste — anche se non risponde ancora — non va mai duplicato: gli
    # impedirebbe di riprendersi la porta quando è pronto. Si aspetta più a
    # lungo invece di crearne uno nostro sopra.
    local existing_on_port
    existing_on_port="$(docker ps -a --filter "publish=${port}" --format '{{.Names}} ({{.Status}})' | grep -v "^${container_name} " || true)"
    if [[ -n "$existing_on_port" ]]; then
        echo "[${label}] container già presente sulla porta ${port} ma non ancora pronto: ${existing_on_port} — attendo, nessun fallback creato"
        for _ in $(seq 1 60); do
            if curl -sf -m 2 "${url%/}${health_path}" >/dev/null 2>&1; then
                echo "[${label}] istanza attiva su ${url}"
                return 0
            fi
            sleep 1
        done
        echo "[${label}] ATTENZIONE: ${existing_on_port} occupa la porta ${port} ma non risponde ancora su ${url}${health_path} — verificalo manualmente"
        return 0
    fi

    if docker container inspect "$container_name" >/dev/null 2>&1; then
        echo "[${label}] riavvio il container di progetto esistente (${container_name})"
        if ! docker start "$container_name" >/dev/null; then
            echo "[${label}] ERRORE: avvio del container esistente (${container_name}) fallito — vedi 'docker logs ${container_name}'"
            return 1
        fi
    else
        echo "[${label}] nessuna istanza raggiungibile — creo il container di progetto (${container_name}) sulla porta ${port}"
        if ! docker run -d --name "$container_name" --restart unless-stopped \
            -p "${port}:${internal_port}" "$image" >/dev/null; then
            echo "[${label}] ERRORE: creazione del container (${container_name}) fallita — porta ${port} già occupata? immagine non scaricabile?"
            return 1
        fi
    fi

    for _ in $(seq 1 20); do
        curl -sf -m 2 "${url%/}${health_path}" >/dev/null 2>&1 && { echo "[${label}] container attivo e pronto"; return 0; }
        sleep 1
    done
    echo "[${label}] ATTENZIONE: il container è partito ma non risponde ancora su ${url}${health_path}"
}

_ensure_service "gotenberg" "gotenberg_ip" "http://localhost:3000" "/health" \
    "md2fastpdf-gotenberg" "gotenberg/gotenberg:8" 3000
