# Guida: Esposizione SC-ARCHIVE su LAN via Caddy

**Obiettivo**: Rendere SC-ARCHIVE accessibile da qualsiasi dispositivo in rete locale tramite nome host personalizzato (`sc-archive.lan`), usando Caddy come reverse proxy.

---

## Scenari disponibili

| Scenario | SC-ARCHIVE | Gotenberg | Ollama | Caddy | Note |
| -------- | ---------- | --------- | ------ | ----- | ---- |
| **A** | WSL2 (Windows) | stessa macchina, esterno | PC Windows / LAN | Raspberry Pi | Alta — portproxy necessario |
| **B** | Raspberry Pi (bare-metal) | altra macchina, esterno | PC Linux / LAN | Raspberry Pi (stesso) | Bassa — tutto sul Pi |
| **C** | PC Linux (bare-metal) | stessa macchina, esterno | stesso PC | Raspberry Pi (o qualsiasi host) | Media — solo firewall |
| **D** | PC Linux (Docker, questo stack) | stesso PC, stack Docker a sé | stesso PC (nativo, GPU diretta) | incluso in questo stack | Raccomandato per eventi |

---

## Scenario D — PC Linux Docker (Raccomandato per Eventi)

Pattern ottimale per convention ed eventi da tavolo. Un solo PC Linux esegue SC-ARCHIVE+Caddy
in un unico stack Docker (`docker-compose.yml`); Gotenberg gira nella propria istanza/stack
Docker indipendente (stesso PC — un `docker run` separato, non lo stesso `docker-compose.yml`);
Ollama nativo con accesso diretto alla GPU.

```text
Browser (LAN)
     │
     ▼
Caddy :80          ← unica porta pubblicata sull'host, unico servizio di questo stack
     │
     ▼  rete Docker interna, nessuna porta pubblicata sull'host
SC-ARCHIVE
     ├──► Gotenberg :3000   (stack Docker a sé, stesso host — via host.docker.internal)
     └──► Ollama :11434     (nativo sull'host, via host.docker.internal — richiede OLLAMA_HOST=0.0.0.0, GPU diretta)
```

Solo Caddy è raggiungibile dalla LAN. SC-ARCHIVE non pubblica porte sull'host
(`docker-compose.yml`: nessun `ports:` su `sc-archive`) — raggiunge sia Gotenberg
(container a sé, stesso host) sia Ollama (nativo, stesso host) via
`host.docker.internal` (`extra_hosts: host-gateway`), stesso meccanismo per entrambi.
Gotenberg e Ollama non si parlano tra loro: sono entrambi chiamati da SC-ARCHIVE.

Il meccanismo funziona identico per entrambi, ma con una premessa diversa: `docker run
-p 3000:3000` di Gotenberg pubblica di default su tutte le interfacce dell'host, quindi
`host.docker.internal` lo raggiunge senza altra configurazione. Ollama invece ascolta di
default solo su `127.0.0.1` — un container non lo raggiungerebbe via `host.docker.internal`
(il traffico non passa per il loopback) senza il binding `OLLAMA_HOST=0.0.0.0` impostato in
D.1. Verificato empiricamente: `ss -tlnp | grep 11434` deve mostrare `*:11434`, non
`127.0.0.1:11434`.

**Perché Ollama fuori da Docker**: i container non accedono alla GPU host senza configurazione NVIDIA Container Toolkit. Ollama nativo usa la GPU direttamente senza overhead — più semplice e più veloce.

### D.1 Installazione Ollama nativo

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5-coder:latest
```

Ollama in modalità default ascolta su `localhost:11434`. Poiché SC-ARCHIVE gira in un container Docker, deve raggiungere Ollama sull'host. Configurare il binding:

```bash
sudo systemctl edit ollama --force
```

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
```

```bash
sudo systemctl daemon-reload && sudo systemctl restart ollama
```

### D.2 Setup Docker stack

```bash
git clone <repo-url> ~/sc-archive && cd ~/sc-archive
cp docker/.env.example .env
nano .env
```

Contenuto `.env`:

```env
AEGIS_ADMIN_PASSWORD=changeme
# GOTENBERG_IP/OLLAMA_IP non necessarie se entrambi girano sullo stesso PC — i default
# puntano a host.docker.internal:3000 / host.docker.internal:11434. Decommentare solo
# se uno dei due è su un host remoto:
# GOTENBERG_IP=http://192.168.1.X:3000
# OLLAMA_IP=http://192.168.1.X:11434
```

Avvia Gotenberg (stack Docker a sé, non parte di questo `docker-compose.yml`) se non già attivo:

```bash
docker run -d --name gotenberg --restart unless-stopped -p 3000:3000 gotenberg/gotenberg:8
```

```bash
docker compose up -d --build
```

Caddy è incluso in questo stack — nessuna installazione separata necessaria.

### D.3 DNS per i client dell'evento

Su ogni tablet/laptop dei giocatori, aggiungere in `/etc/hosts` (Linux/macOS) o `C:\Windows\System32\drivers\etc\hosts` (Windows):

```text
<IP_LAN_PC>    sc-archive.lan
```

> Alternativa zero-config: configurare il router dell'evento per risolvere `sc-archive.lan` via DNS locale — elimina la necessità di toccare ogni dispositivo.

### D.4 Verifica stack completo

Il container `sc-archive` non ha `curl` — verifica con `python3` (già nell'immagine),
leggendo l'indirizzo effettivo dalle variabili d'ambiente invece di scriverlo a mano:

```bash
# Gotenberg
docker compose exec sc-archive python3 -c "import os, urllib.request as u; print(u.urlopen(os.environ['GOTENBERG_IP'] + '/health').read().decode())"

# Ollama
docker compose exec sc-archive python3 -c "import os, urllib.request as u; print(u.urlopen(os.environ['OLLAMA_IP'] + '/api/tags').read().decode())"
```

---

## Prerequisiti comuni — Installazione Caddy

Eseguire sul dispositivo che ospiterà Caddy (Raspberry Pi per scenari A e C; stesso Pi per scenario B):

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
  | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
  | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install caddy
```

---

## Scenario A — Caddy (RPi) → WSL2 (Windows)

```text
Browser (LAN) → Raspberry Pi :80 (Caddy) → PC Windows :8000 (portproxy) → WSL2 :8000 (SC-ARCHIVE)
```

| Dispositivo  | IP           | Ruolo                  |
|--------------|--------------|------------------------|
| PC Windows   | 192.168.1.11 | Host WSL2 + SC-ARCHIVE |
| Raspberry Pi | 192.168.1.20 | Reverse proxy Caddy    |

### A.1 WSL2 — Portproxy su Windows

WSL2 ha un IP interno che cambia ad ogni riavvio. Windows deve esporre la porta 8000 su tutti gli indirizzi.

```powershell
# Recupera IP WSL2
$wslIp = (wsl hostname -I).Trim()

# Aggiungi portproxy
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=$wslIp

# Apri porta nel firewall Windows
netsh advfirewall firewall add rule name="WSL2 SC-ARCHIVE" dir=in action=allow protocol=TCP localport=8000
```

### A.2 Automazione portproxy all'avvio (Task Scheduler)

Crea `C:\Scripts\wsl2-portproxy.ps1`:

```powershell
$wslIp = (wsl hostname -I).Trim()
netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=$wslIp
```

Registra il task (PowerShell come amministratore):

```powershell
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -NonInteractive -File C:\Scripts\wsl2-portproxy.ps1"
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
Register-ScheduledTask -TaskName "WSL2 PortProxy SC-ARCHIVE" -Action $action -Trigger $trigger -Principal $principal
```

Verifica:

```powershell
netsh interface portproxy show all
Get-ScheduledTask -TaskName "WSL2 PortProxy SC-ARCHIVE"
```

### A.3 Caddyfile (Raspberry Pi)

```bash
sudo nano /etc/caddy/Caddyfile
```

```caddy
http://sc-archive.lan:80 {
    reverse_proxy 192.168.1.11:8000
}
```

```bash
sudo systemctl reload caddy
```

---

## Scenario B — SC-ARCHIVE su Raspberry Pi

```text
Browser (LAN) → Raspberry Pi :80 (Caddy) → localhost :8000 (SC-ARCHIVE)
```

| Dispositivo  | IP           | Ruolo                          |
|--------------|--------------|--------------------------------|
| Raspberry Pi | 192.168.1.20 | SC-ARCHIVE + Caddy (stesso Pi) |

SC-ARCHIVE e Caddy girano sullo stesso dispositivo. Nessun portproxy, nessuna rete interna.

> **Servizi esterni**: Gotenberg e Ollama **non** girano sul Pi — devono essere su un altro host in LAN (es. PC Linux). Configurare i relativi IP in `config/settings.json` o dalla UI Settings:
>
> - `gotenberg_ip` → `http://192.168.1.X:3000`
> - `ollama_ip` → `http://192.168.1.X:11434`

### B.1 IP statico sul Pi

Assegnare IP fisso via riserva DHCP sul router (consigliato) oppure in `/etc/dhcpcd.conf`:

```text
interface eth0
static ip_address=192.168.1.20/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1
```

```bash
sudo systemctl restart dhcpcd
```

### B.2 SC-ARCHIVE — avvio come servizio systemd utente

Crea `~/.config/systemd/user/sc-archive.service`:

```ini
[Unit]
Description=SC-ARCHIVE FastAPI
After=network.target

[Service]
WorkingDirectory=/path/to/MD2FastPDF
ExecStart=/bin/bash bin/launch.sh
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now sc-archive.service
```

SC-ARCHIVE ascolta su `localhost:8000` — non esposto direttamente alla LAN.

### B.3 Caddyfile (stesso Pi)

```bash
sudo nano /etc/caddy/Caddyfile
```

```caddy
http://sc-archive.lan:80 {
    reverse_proxy localhost:8000
}
```

```bash
sudo systemctl reload caddy
```

---

## Scenario C — SC-ARCHIVE su PC Linux → Caddy (RPi)

```text
Browser (LAN) → Raspberry Pi :80 (Caddy) → PC Linux :8000 (SC-ARCHIVE)
```

| Dispositivo  | IP           | Ruolo               |
|--------------|--------------|---------------------|
| PC Linux     | 192.168.1.15 | SC-ARCHIVE          |
| Raspberry Pi | 192.168.1.20 | Reverse proxy Caddy |

### C.1 SC-ARCHIVE — bind su tutte le interfacce

Per default `bin/launch.sh` avvia Uvicorn su `127.0.0.1`. Cambiare il bind per accettare connessioni dal Pi:

```bash
# In bin/launch.sh, sostituire l'host uvicorn:
uvicorn main:app --host 0.0.0.0 --port 8000
```

> **Attenzione:** `0.0.0.0` espone SC-ARCHIVE direttamente sulla LAN — chiunque in rete può raggiungere la porta 8000 senza passare per Caddy. Proteggere con firewall (vedi C.2) oppure mantenere `127.0.0.1` e usare un tunnel SSH (vedi C.3).

### C.2 Firewall sul PC Linux

Permettere il traffico solo dal Pi (consigliato):

```bash
sudo ufw allow from 192.168.1.20 to any port 8000
sudo ufw deny 8000
sudo ufw reload
```

Oppure apri a tutta la LAN (meno sicuro):

```bash
sudo ufw allow 8000
```

### C.3 Alternativa sicura — tunnel SSH (nessun bind 0.0.0.0)

Il Pi crea un tunnel SSH verso il PC Linux. SC-ARCHIVE resta su `127.0.0.1` e nessuna porta è esposta.

Sul PC Linux, abilitare l'utente SSH per il Pi:

```bash
# Copia la chiave pubblica del Pi sul PC Linux
ssh-copy-id utente@192.168.1.15
```

Sul Raspberry Pi, aggiungere a `/etc/caddy/Caddyfile` (vedi C.4) e creare il tunnel all'avvio:

```bash
# /etc/systemd/system/sc-archive-tunnel.service
[Unit]
Description=SSH tunnel SC-ARCHIVE
After=network.target

[Service]
ExecStart=ssh -N -L 8001:localhost:8000 utente@192.168.1.15 -o StrictHostKeyChecking=no -o ServerAliveInterval=30
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now sc-archive-tunnel.service
```

Il Caddyfile punterà a `localhost:8001` (porta locale del tunnel sul Pi).

### C.4 Caddyfile (Raspberry Pi)

Senza tunnel (bind `0.0.0.0`):

```caddy
http://sc-archive.lan:80 {
    reverse_proxy 192.168.1.15:8000
}
```

Con tunnel SSH:

```caddy
http://sc-archive.lan:80 {
    reverse_proxy localhost:8001
}
```

```bash
sudo systemctl reload caddy
```

---

## DNS — File hosts sui client

Su ogni dispositivo della LAN che deve raggiungere `sc-archive.lan`, aggiungere una voce `hosts` che punti all'IP del Pi (o del dispositivo che ospita Caddy).

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

> Alternativa: configurare il router per risolvere `sc-archive.lan → 192.168.1.20` via DNS locale (dnsmasq, Pi-hole, Unbound) — elimina la necessità di modificare ogni dispositivo.

---

## Log dei servizi

### SC-ARCHIVE (systemd utente — Linux / WSL2)

```bash
journalctl --user -u sc-archive.service -f        # real-time
journalctl --user -u sc-archive.service -n 100    # ultime 100 righe
```

### Gotenberg e Ollama — verifica bootstrap (`bin/ensure_services.sh`)

`bin/ensure_services.sh` gira dentro `bin/launch.sh`, quindi il suo output
(esito del check di raggiungibilità di Gotenberg e Ollama) finisce nel journal
del *servizio*, non nell'output di `systemctl status` — quel comando mostra
solo le ultime righe di log in coda, non l'intera sequenza di avvio:

```bash
journalctl --user -u sc-archive.service -n 50 --no-pager   # ultime righe di boot, incluso l'esito dei check Gotenberg/Ollama
journalctl --user -u sc-archive.service -f                 # segui il boot in tempo reale
journalctl --user -u sc-archive.service -b                 # solo dal boot corrente della macchina
```

Cosa cercare nell'output: righe `[gotenberg] istanza attiva su ...` /
`[ollama] istanza attiva su ...` (tutto ok), oppure `[gotenberg] ATTENZIONE:
nessuna istanza raggiungibile su ...` / `[ollama] ATTENZIONE: ...` — l'URL
configurato (`gotenberg_ip`/`ollama_ip`, da Settings o
`config/settings.json`) non risponde. Entrambi sono servizi esterni: lo
script si limita a controllarli, non li crea né li avvia mai.

### Caddy

```bash
sudo journalctl -u caddy -f
sudo journalctl -u caddy -n 100
```

### Tunnel SSH (scenario C)

```bash
sudo journalctl -u sc-archive-tunnel.service -f
```

---

## Verifica

```bash
ping sc-archive.lan
# deve rispondere con 192.168.1.20
```

Apri browser: `http://sc-archive.lan` — SC-ARCHIVE deve essere raggiungibile.

Verifica che Caddy stia proxiando correttamente:

```bash
curl -v http://sc-archive.lan/login
```

---

## Note

- **Chrome blocca `.local`**: usa `.lan` come TLD per i domini LAN.
- **IP WSL2 volatile** (solo scenario A): il Task Scheduler risolve il problema ad ogni riavvio.
- **Scenario B su Pi 4/5**: prestazioni sufficienti per uso personale; Pi 3 può soffrire con PDF pesanti (Gotenberg).
- **HTTPS**: quando si aggiunge un dominio pubblico, Caddy gestisce Let's Encrypt automaticamente. Sostituire `http://sc-archive.lan` con il dominio reale nel Caddyfile.
- **Basic Auth a livello Caddy**: aggiungibile con `basicauth` nel Caddyfile come secondo layer di protezione oltre al login SC-ARCHIVE.

---

*Documentazione operativa SC-ARCHIVE // Aegis Network Protocol.*
