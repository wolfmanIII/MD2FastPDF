# SC-ARCHIVE — Configurazione Docker

**Stack**: SC-ARCHIVE (FastAPI) + Caddy (reverse proxy)
**Target**: qualsiasi host Linux con Docker — PC x86_64, server, Raspberry Pi 4/5 (ARM64). Questa non è una guida specifica per Raspberry Pi: la stessa `docker-compose.yml` funziona identica su qualunque architettura, il Pi è solo uno dei target supportati (le immagini sono multi-arch).
**Gotenberg e Ollama**: sempre esterni — nessuno dei due è mai un container di questo stack. Gotenberg gira nella propria istanza/stack Docker indipendente (stesso host o un'altra macchina in LAN), raggiunto via `GOTENBERG_IP`; Ollama sempre nativo (mai Docker), raggiunto via `OLLAMA_IP`.

> [!IMPORTANT]
> Su **Raspberry Pi e PC poco performanti**, Ollama non va installato affatto su quella macchina — né in Docker né nativo: Gotenberg (Chromium headless) già assorbe RAM/CPU, e i modelli LLM competerebbero per le stesse risorse limitate. Va eseguito su un'altra macchina della LAN — vedi sezione "Deploy Ibrido" più sotto. Su hardware più potente puoi tenerlo sulla stessa macchina, ma **sempre installato nativamente, mai in Docker**.

---

## Architettura

```text
Browser (LAN)
     │
     ▼
Caddy :80          ← unica porta pubblicata sull'host, unico servizio di questo stack
     │
     ▼  rete Docker interna, nessuna porta pubblicata sull'host
SC-ARCHIVE
     ├──► Gotenberg :3000   (propria istanza/stack Docker indipendente — stesso host o LAN)
     └──► Ollama :11434     (nativo — stesso host o LAN)
```

| Servizio | Gestito da questo stack | Porta esposta |
| -------- | ------------------------ | ------------- |
| SC-ARCHIVE | Sì (`sc-archive`) | interna (via Caddy) |
| Caddy | Sì (`caddy`) | `80` → LAN |
| Gotenberg | **No** — stack Docker a sé | esterna, via `GOTENBERG_IP` |
| Ollama | **No** — sempre nativo | esterna, via `OLLAMA_IP` |

---

## Prerequisiti sull'host Docker

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

Assegnare IP fisso via riserva DHCP sul router, oppure localmente sull'host. Su **Raspberry Pi OS** (che usa `dhcpcd`):

```text
interface eth0
static ip_address=192.168.1.20/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1
```

```bash
sudo systemctl restart dhcpcd
```

Su altre distribuzioni (Ubuntu Server con `netplan`, Debian con `NetworkManager`, ecc.) usare lo strumento equivalente della distro — il concetto (IP fisso sull'host che serve lo stack) è lo stesso, cambia solo il meccanismo.

---

## Installazione

### 1. Clona il repository

```bash
git clone <repo-url> ~/sc-archive
cd ~/sc-archive
```

Vale sia su un PC x86_64 sia su un Raspberry Pi (ARM64) — nessun passaggio cambia in base all'architettura.

### 2. Configura le variabili d'ambiente

```bash
cp docker/.env.example .env
nano .env
```

Contenuto `.env`:

```env
# Password admin al primo avvio (cambiabile dalla UI Settings in seguito)
AEGIS_ADMIN_PASSWORD=changeme

# Gotenberg è sempre esterno a questo stack (propria istanza/stack Docker
# indipendente). Se già in ascolto su localhost:3000 sullo stesso host, il
# default (host.docker.internal:3000) basta e questa riga resta commentata.
# GOTENBERG_IP=http://192.168.1.X:3000

# IP della macchina in LAN che esegue Ollama (sempre esterno a questo stack)
OLLAMA_IP=http://192.168.1.X:11434
```

Sostituire `192.168.1.X` con l'IP effettivo della macchina che esegue Gotenberg/Ollama. Su Raspberry Pi o PC poco performanti sarà quasi sempre un'altra macchina della LAN (vedi il box in alto e la sezione "Deploy Ibrido"); su un host abbastanza potente possono anche girare entrambi sullo stesso host che ospita i container — in tal caso i default (`host.docker.internal`) bastano, nessuna variabile da impostare.

Se Gotenberg non è già attivo, avvialo come stack Docker indipendente:

```bash
docker run -d --name gotenberg --restart unless-stopped -p 3000:3000 gotenberg/gotenberg:8
```

> [!WARNING]
> Se `AEGIS_ADMIN_PASSWORD` non viene impostata, **non** viene usata nessuna password fissa: SC-ARCHIVE ne genera una casuale al primo avvio e la salva in `/home/aegis/.config/sc-archive/admin_password.txt` (nel volume `sc-archive-userdata`, persistente) — vedi sezione "Primo avvio" più sotto.

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

La prima build scarica il binary Tailwind corretto per l'architettura dell'host (x86_64 o ARM64), compila il CSS, installa le dipendenze Python. Durata stimata: pochi minuti su un PC x86_64, 5-10 minuti su Raspberry Pi 5.

`sc-archive` espone un healthcheck (`GET /login`): `caddy` attende che `sc-archive` sia healthy prima di partire — niente errori nei primissimi secondi dopo l'avvio. Gotenberg non fa parte di questo `docker compose ps` — è uno stack a sé, verificalo separatamente (vedi sezione "Gotenberg in rete" più sotto).

Verifica che tutti i servizi di questo stack siano attivi:

```bash
docker compose ps
```

Output atteso:

```hosts
NAME                    STATUS                    PORTS
md2fastpdf-caddy-1      Up                        0.0.0.0:80->80/tcp
md2fastpdf-sc-archive-1 Up (healthy)
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

> Alternativa: configurare `dnsmasq` o **Pi-hole** sul router (indipendentemente da cosa ospita SC-ARCHIVE) per risolvere `sc-archive.lan` automaticamente su tutti i dispositivi della LAN.

---

## Primo avvio — cosa succede

All'avvio del container `sc-archive`, l'entrypoint esegue automaticamente:

L'entrypoint parte sempre come root — non perché l'app giri da root, ma per poter sistemare i permessi sui volumi montati (Docker crea i named volume vuoti e di proprietà di root al primo utilizzo, e un volume ereditato da un deploy precedente a questa versione ha gli stessi permessi) prima di lanciare l'app vera e propria come utente non privilegiato `aegis` (via `gosu`, l'ultima riga di `entrypoint.sh`). Il processo `uvicorn` che serve le richieste non ha mai privilegi di root.

1. **Corregge i permessi** su `config/`, `blueprints/`, `.config/sc-archive/` e `sc-archive/` (proprietario `aegis:aegis`)

2. **Crea `config/settings.json`** con i valori Docker-appropriati:
   - `gotenberg_ip`: valore da `GOTENBERG_IP` nel `.env` (default `http://host.docker.internal:3000`)
   - `ollama_ip`: valore da `OLLAMA_IP` nel `.env` (default `http://host.docker.internal:11434`)
   - `workspace_base`: `/home/aegis/sc-archive`

3. **Genera la session key** in `/home/aegis/.config/sc-archive/session.key` (persiste nel volume `sc-archive-userdata`)

4. **Bootstrap admin**: se `users.json` è assente, crea l'utente `admin` con il gruppo `"admin"`. Password: quella da `AEGIS_ADMIN_PASSWORD` se impostata nel `.env`, altrimenti una password casuale generata al volo e salvata in `/home/aegis/.config/sc-archive/admin_password.txt` (persiste nel volume `sc-archive-userdata`) — recuperabile con:

     ```bash
     docker compose exec sc-archive cat /home/aegis/.config/sc-archive/admin_password.txt
     ```

5. **Passa il controllo a `uvicorn`** eseguito come `aegis` (`exec gosu aegis ...`), non più come root.

Aprire il browser su `http://sc-archive.lan` e accedere con `admin` / password scelta.

---

## Volumi — Dati persistenti

| Volume | Percorso nel container | Contenuto |
| ------ | ---------------------- | --------- |
| `sc-archive-config` | `/app/config` | `settings.json` |
| `sc-archive-userdata` | `/home/aegis/.config/sc-archive` | `users.json`, `groups.json`, `session.key`, `admin_password.txt` |
| `sc-archive-workspaces` | `/home/aegis/sc-archive` | Workspace file degli utenti |
| `sc-archive-blueprints` | `/app/blueprints` | Template della libreria Blueprint |

I dati sopravvivono a `docker compose down`. Per resettare completamente:

```bash
docker compose down -v   # rimuove anche i volumi
```

### Dove sono i file sul disco dell'host

I percorsi della tabella sopra sono **dentro il container**, non sull'host. Per trovare il percorso reale sul disco (es. per backup manuali, ispezione diretta, o recuperare i file senza passare da `docker compose exec`):

```bash
docker volume inspect md2fastpdf_sc-archive-workspaces
```

Il campo `Mountpoint` è il percorso reale — di norma qualcosa come `/var/lib/docker/volumes/md2fastpdf_sc-archive-workspaces/_data/`, navigabile solo con `sudo` (i volumi Docker sono di proprietà di root a livello host). Dentro trovi una cartella per ogni username SC-ARCHIVE (es. `admin/`) — **non** una cartella chiamata `aegis`: `aegis` è solo l'utente Linux dentro il container che possiede i file, non uno username dell'app.

Se il prefisso `md2fastpdf_` non corrisponde (dipende dal nome della cartella in cui hai clonato il repository, che diventa il nome del progetto Docker Compose), trova il nome esatto con:

```bash
docker volume ls | grep sc-archive
```

---

## Deploy Ibrido: Host Docker + Nodo GPU Esterno per Ollama

Per scenari event/convention o installazioni permanenti con Oracle attivo, il pattern raccomandato è a due nodi — **particolarmente importante su Raspberry Pi o PC poco performanti**, dove far girare anche Ollama sulla stessa macchina competerebbe per RAM/CPU con Gotenberg:

```text
Host Docker (Raspberry Pi 4/5, mini-PC, server...)
├── SC-ARCHIVE (Docker, questo stack)
├── Caddy (Docker, questo stack)
└── Gotenberg (Docker, stack a sé — stesso host o altra macchina)
        │
        └──► LAN ──► Nodo GPU (Ollama)
                      ├── PC Linux x86 con NVIDIA GPU
                      └── NVIDIA DGX Spark (ARM64 / Blackwell)
```

**Vantaggi**: l'host Docker gestisce i file e la generazione PDF senza carico GPU; il nodo Ollama serve l'Oracle con latenza minima anche sotto carico multi-utente. Su un host già potente (con GPU propria) il nodo Ollama può anche essere la stessa macchina — ma va sempre installato **nativo**, mai in Docker.

### NVIDIA DGX Spark come nodo Ollama

Il DGX Spark (GB10 Blackwell, 128 GB RAM unificata) è un host Ollama di prima classe. Configurazione su DGX OS (Ubuntu-based):

```bash
# Installa Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Scarica il modello
ollama pull qwen2.5-coder:latest
```

Per esporlo sulla LAN (binding, firewall, verifica) segui la checklist completa nella sezione "Ollama in rete" più sotto — si applica identica qui.

---

## Gotenberg — stack Docker indipendente

Gotenberg non fa parte di `docker-compose.yml`: è una sua istanza/stack Docker a sé, sullo stesso host o su un'altra macchina della LAN. Avvio minimo (stesso host):

```bash
docker run -d --name gotenberg --restart unless-stopped -p 3000:3000 gotenberg/gotenberg:8
```

- **Stesso host di SC-ARCHIVE**: nessuna variabile da impostare, il default in `docker-compose.yml` (`GOTENBERG_IP=http://host.docker.internal:3000`) raggiunge il container via il gateway Docker dell'host.
- **Altra macchina in LAN**: imposta `GOTENBERG_IP=http://<IP_LAN>:3000` nel `.env` — stessa firewall/binding da verificare di Ollama (porta raggiungibile dall'host che esegue SC-ARCHIVE, non solo da `localhost` della macchina Gotenberg).

Verifica diretta:

```bash
curl http://localhost:3000/health          # dallo stesso host di Gotenberg
curl http://<IP_LAN>:3000/health           # da un'altra macchina della LAN
```

Output atteso: `{"status":"up", ...}`.

---

## Ollama in rete — checklist completa

Raggiungere Ollama su un'altra macchina della LAN richiede **4 livelli indipendenti**, da verificare in ordine — un problema in uno non implica che gli altri siano a posto:

### 1. Trova l'IP reale della macchina che esegue Ollama

```bash
hostname -I
```

Se quella macchina ha anche Docker installato, **ignora gli IP dei bridge interni** (tipicamente `172.17.x.x`, `172.18.x.x`) — non sono raggiungibili dal resto della LAN. Quello che serve è l'IP della rete reale (di solito `192.168.x.x` o `10.x.x.x`).

### 2. Ollama deve ascoltare su tutte le interfacce, non solo localhost

```bash
ss -tlnp | grep 11434
```

Deve mostrare `0.0.0.0:11434` o `*:11434`. Se mostra `127.0.0.1:11434`, Ollama accetta connessioni solo dalla propria macchina — nessun'altra macchina della LAN può raggiungerlo, a prescindere da firewall o indirizzo configurato. Fix (systemd):

```bash
sudo systemctl edit ollama --force
```

Nel file che si apre:

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
```

```bash
sudo systemctl daemon-reload && sudo systemctl restart ollama
```

(Se Ollama gira senza systemd: `OLLAMA_HOST=0.0.0.0 ollama serve`.)

### 3. Firewall sulla macchina Ollama

```bash
sudo ufw status
sudo ufw allow 11434
```

### 4. Verifica dalla macchina che ospita SC-ARCHIVE (non da Ollama stesso)

```bash
ping -c 2 <IP_OLLAMA>                      # conferma che le due macchine si vedano in rete
curl http://<IP_OLLAMA>:11434/api/tags     # conferma che Ollama risponda
```

> [!TIP]
> Se `curl` restituisce **"could not resolve host"** con un IP letterale (non un hostname), il problema non è la rete né Ollama — è quasi sempre una variabile d'ambiente proxy (`http_proxy`/`https_proxy`) impostata sulla macchina da cui lanci `curl`, che intercetta la richiesta prima ancora di provare a contattare l'IP. Controlla con `echo $http_proxy $https_proxy` su quella macchina.

Una volta che tutti e 4 i punti sono a posto, imposta `OLLAMA_IP=http://<IP_OLLAMA>:11434` nel `.env` di SC-ARCHIVE (vedi step 2 dell'installazione).

### 5. Abilita il toggle nell'app — passo separato, facile da dimenticare

Anche con la rete perfettamente configurata, SC-ARCHIVE in Docker parte con il Neural Link **disattivato di default** (scelta conservativa in `docker/entrypoint.sh`), indipendentemente da cosa hai messo in `OLLAMA_IP` — sono due impostazioni scollegate. Vai su **Settings → SYSTEM_STATUS → Neural Link Protocol**, attivalo, salva.

Il pannello NEURAL_CORE della dashboard distingue i due problemi:

- `ONLINE // DISABLED_IN_SETTINGS` (ambra) → la rete funziona, manca solo il toggle acceso
- `OFFLINE` (rosso) → problema di rete reale, torna ai punti 1-4

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

Apre una shell come root (utile per ispezionare/riparare qualsiasi cosa). L'app in esecuzione (`uvicorn`, PID 1) gira invece come utente non privilegiato `aegis` — per una shell con gli stessi permessi dell'app: `docker compose exec --user aegis sc-archive bash`.

---

## Troubleshooting

### SC-ARCHIVE non si avvia

```bash
docker compose logs sc-archive
```

Cause comuni:

- `settings.json` corrotto nel volume → `docker compose exec sc-archive cat config/settings.json`
- Porta 80 già occupata sull'host → `sudo lsof -i :80`

### PDF non funziona

Gotenberg non raggiungibile (il container `sc-archive` non ha `curl`, usa `python3`). Verifica dal punto di vista del container SC-ARCHIVE (usa la stessa `GOTENBERG_IP` che l'app ha in `settings.json`, non un IP a mano):

```bash
docker compose exec sc-archive python3 -c "import os, urllib.request as u; print(u.urlopen(os.environ['GOTENBERG_IP'] + '/health').read().decode())"
```

Output atteso: `{"status":"up", ...}`. Se fallisce, verifica che Gotenberg sia effettivamente attivo (`docker ps | grep gotenberg` sulla macchina che lo esegue) — vedi sezione "Gotenberg — stack Docker indipendente" più sopra.

### Ollama non risponde (o il pannello mostra PROTOCOL_OFFLINE)

```bash
docker compose exec sc-archive python3 -c "import os, urllib.request as u; print(u.urlopen(os.environ['OLLAMA_IP'] + '/api/tags').read().decode())"
```

Se fallisce, segui la checklist completa nella sezione "Ollama in rete" più sopra (IP corretto, binding, firewall, proxy). Se invece risponde ma il pannello NEURAL_CORE mostra ancora qualcosa di diverso da `ONLINE`, controlla che il toggle **Neural Link Protocol** sia acceso in Settings — è un'impostazione separata dall'indirizzo, disattivata di default nei deploy Docker.

### Reset password admin

`--user aegis` mantiene la scrittura coerente con l'utente non privilegiato che esegue l'app (un `docker compose exec` senza `--user` gira come root e produrrebbe un `users.json` di proprietà di root — l'entrypoint lo corregge comunque al riavvio successivo, ma è più pulito evitarlo):

```bash
docker compose exec --user aegis sc-archive python3 -c "
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
