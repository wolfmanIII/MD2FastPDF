# Guida: Esposizione SC-ARCHIVE su LAN via Caddy

**Obiettivo**: Rendere SC-ARCHIVE accessibile da qualsiasi dispositivo in rete locale tramite nome host personalizzato (`sc-archive.lan`), usando Caddy come reverse proxy.

---

## Scenari disponibili

| Scenario | SC-ARCHIVE gira su | Caddy gira su | Complessità |
| ---------- | -------------------- | --------------- | ------------- |
| **A** | WSL2 (Windows) | Raspberry Pi | Alta — portproxy necessario |
| **B** | Raspberry Pi | Raspberry Pi (stesso) | Bassa — tutto sul Pi |
| **C** | PC Linux | Raspberry Pi (o qualsiasi host) | Media — solo firewall |

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
