# SC-ARCHIVE su Raspberry Pi — Deploy con Docker

**Stack**: SC-ARCHIVE (FastAPI) + Gotenberg (PDF) + Caddy (reverse proxy)
**Target**: Raspberry Pi 4/5 con Docker installato
**Ollama**: esterno — gira su PC Linux in LAN

---

## Architettura

```text
Browser (LAN)
     │
     ▼
Caddy :80  ─────────────────────────────┐
     │                                  │
     ▼                          docker network interno
SC-ARCHIVE :8000                        │
     │                                  │
     ├──► Gotenberg :3000 ──────────────┘
     │
     └──► Ollama :11434  (PC Linux esterno — LAN)
```

| Servizio | Container | Porta esposta |
|----------|-----------|---------------|
| SC-ARCHIVE | `sc-archive` | interna (via Caddy) |
| Gotenberg | `gotenberg` | interna |
| Caddy | `caddy` | `80` → LAN |

---

## Prerequisiti sul Raspberry Pi

### Docker + Docker Compose

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

Verifica:

```bash
docker --version
docker compose version
```

### IP statico (consigliato)

Assegnare IP fisso via riserva DHCP sul router oppure in `/etc/dhcpcd.conf`:

```text
interface eth0
static ip_address=192.168.1.20/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1
```

```bash
sudo systemctl restart dhcpcd
```

---

## Installazione

### 1. Clona il repository

```bash
git clone <repo-url> ~/sc-archive
cd ~/sc-archive
```

### 2. Configura le variabili d'ambiente

```bash
cp docker/.env.example .env
nano .env
```

Contenuto `.env`:

```env
# Password admin al primo avvio (cambiabile dalla UI Settings in seguito)
AEGIS_ADMIN_PASSWORD=changeme

# IP Ollama sul PC Linux in LAN
OLLAMA_IP=http://192.168.1.X:11434
```

Sostituire `192.168.1.X` con l'IP effettivo del PC Linux che esegue Ollama.

### 3. Configura il Caddyfile

```bash
nano docker/Caddyfile
```

Contenuto predefinito — nessuna modifica necessaria se si usa `sc-archive.lan`:

```caddy
http://sc-archive.lan:80 {
    reverse_proxy sc-archive:8000
}
```

Per usare un IP diretto invece del nome host (senza DNS):

```caddy
http://:80 {
    reverse_proxy sc-archive:8000
}
```

### 4. Build e avvio

```bash
docker compose up -d --build
```

La prima build scarica il binary Tailwind corretto per l'architettura del Pi (ARM64), compila il CSS, installa le dipendenze Python. Durata stimata: 5-10 minuti su Pi 5.

Verifica che tutti i servizi siano attivi:

```bash
docker compose ps
```

Output atteso:

```hosts
NAME                    STATUS          PORTS
sc-archive-caddy-1      running         0.0.0.0:80->80/tcp
sc-archive-gotenberg-1  running
sc-archive-sc-archive-1 running
```

---

## DNS — Accesso via nome host

Su ogni dispositivo in LAN che deve raggiungere `sc-archive.lan`:

**Linux / macOS** — `/etc/hosts`:

```text
192.168.1.20    sc-archive.lan
```

**Windows** — `C:\Windows\System32\drivers\etc\hosts` (Blocco Note come amministratore):

```text
192.168.1.20    sc-archive.lan
```

```powershell
ipconfig /flushdns
```

> Alternativa: configurare `dnsmasq` o **Pi-hole** sul router per risolvere `sc-archive.lan` automaticamente su tutti i dispositivi della LAN.

---

## Primo avvio — cosa succede

All'avvio del container `sc-archive`, l'entrypoint esegue automaticamente:

1. **Crea `config/settings.json`** con i valori Docker-appropriati:
   - `gotenberg_ip`: `http://gotenberg:3000` (nome container interno)
   - `ollama_ip`: valore da `OLLAMA_IP` nel `.env`
   - `workspace_base`: `/root/sc-archive`

2. **Genera la session key** in `/root/.config/sc-archive/session.key` (persiste nel volume `sc-archive-userdata`)

3. **Bootstrap admin**: se `users.json` è assente, crea l'utente `admin` con la password da `AEGIS_ADMIN_PASSWORD` e il gruppo `"admin"`.

Aprire il browser su `http://sc-archive.lan` e accedere con `admin` / password scelta.

---

## Volumi — Dati persistenti

| Volume | Percorso nel container | Contenuto |
|--------|------------------------|-----------|
| `sc-archive-config` | `/app/config` | `settings.json` |
| `sc-archive-userdata` | `/root/.config/sc-archive` | `users.json`, `groups.json`, `session.key` |
| `sc-archive-workspaces` | `/root/sc-archive` | Workspace file degli utenti |

I dati sopravvivono a `docker compose down`. Per resettare completamente:

```bash
docker compose down -v   # rimuove anche i volumi
```

---

## Configurazione Ollama

Ollama deve girare sul PC Linux con binding su tutte le interfacce (non solo localhost):

```bash
# Sul PC Linux — avvia Ollama accessibile dalla LAN
OLLAMA_HOST=0.0.0.0 ollama serve
```

Oppure, se Ollama è un servizio systemd, aggiungere in `/etc/systemd/system/ollama.service`:

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
```

```bash
sudo systemctl daemon-reload && sudo systemctl restart ollama
```

Verifica che il Pi raggiunga Ollama:

```bash
curl http://192.168.1.X:11434/api/tags
```

---

## Aggiornamento

```bash
git pull
docker compose up -d --build
```

L'immagine viene ricostruita. I volumi (dati utenti, settings) non vengono toccati.

---

## Gestione

### Log

```bash
# SC-ARCHIVE
docker compose logs -f sc-archive

# Tutti i servizi
docker compose logs -f

# Ultime 100 righe
docker compose logs --tail=100 sc-archive
```

### Riavvio singolo servizio

```bash
docker compose restart sc-archive
```

### Stop completo

```bash
docker compose down        # ferma e rimuove container, i volumi restano
docker compose down -v     # ferma + rimuove tutto inclusi i volumi
```

### Shell nel container

```bash
docker compose exec sc-archive bash
```

---

## Troubleshooting

### SC-ARCHIVE non si avvia

```bash
docker compose logs sc-archive
```

Cause comuni:
- `settings.json` corrotto nel volume → `docker compose exec sc-archive cat config/settings.json`
- Porta 80 già occupata sul Pi → `sudo lsof -i :80`

### PDF non funziona

Gotenberg non raggiungibile. Verifica:

```bash
docker compose exec sc-archive curl http://gotenberg:3000/health
```

Output atteso: `{"status":"up"}`

### Ollama non risponde

```bash
docker compose exec sc-archive curl $OLLAMA_IP/api/tags
```

Se fallisce: verificare firewall sul PC Linux (`sudo ufw allow 11434`) e che Ollama sia in ascolto su `0.0.0.0`.

### Reset password admin

```bash
docker compose exec sc-archive python3 -c "
from logic.auth import auth_service
import asyncio
asyncio.run(auth_service.change_password('admin', 'nuova_password'))
print('OK')
"
```

---

## Note

- **Chrome blocca `.local`**: usare `.lan` come TLD.
- **Pi 3 / 1GB RAM**: Gotenberg usa Chromium headless (~300-500MB) — probabile OOM. Pi 4 4GB+ consigliato.
- **HTTPS**: aggiungere dominio pubblico nel Caddyfile — Caddy gestisce Let's Encrypt automaticamente.
- **Backup volumi**:

```bash
docker run --rm \
  -v sc-archive_sc-archive-userdata:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/userdata-backup.tar.gz -C /data .
```

---

*Documentazione operativa SC-ARCHIVE // Aegis Docker Protocol.*
