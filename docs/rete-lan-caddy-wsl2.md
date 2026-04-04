# Guida: Esposizione SC-ARCHIVE su LAN via Caddy + WSL2

**Obiettivo**: Rendere SC-ARCHIVE accessibile da qualsiasi dispositivo in rete locale tramite un nome host personalizzato (`sc-archive.lan`), usando Caddy come reverse proxy su Raspberry Pi.

---

## Infrastruttura

```
Browser (LAN) → Raspberry Pi :80 (Caddy) → PC Windows :8000 (portproxy) → WSL2 :8000 (SC-ARCHIVE)
```

| Dispositivo    | IP            | Ruolo                        |
|----------------|---------------|------------------------------|
| PC Windows     | 192.168.1.11  | Host WSL2 + SC-ARCHIVE       |
| Raspberry Pi   | 192.168.1.20  | Reverse proxy Caddy          |

---

## 1. WSL2 — Portproxy su Windows

WSL2 ha un IP interno che cambia ad ogni riavvio. Windows deve esporre la porta 8000 su tutti gli indirizzi.

### 1.1 Aggiungere il portproxy (PowerShell come amministratore)

```powershell
# Recupera IP WSL2
$wslIp = (wsl hostname -I).Trim()

# Aggiungi portproxy
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=$wslIp

# Apri porta nel firewall Windows
netsh advfirewall firewall add rule name="WSL2 SC-ARCHIVE" dir=in action=allow protocol=TCP localport=8000
```

### 1.2 Automazione all'avvio (Task Scheduler)

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

Verifica del portproxy:

```powershell
netsh interface portproxy show all
```

Verifica se il task é attivo:

```powershell
Get-ScheduledTask -TaskName "WSL2 PortProxy SC-ARCHIVE"
```

---

## 2. Raspberry Pi — Installazione Caddy

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install caddy
```

---

## 3. Raspberry Pi — Configurazione Caddyfile

```bash
sudo nano /etc/caddy/Caddyfile
```

Contenuto (sostituisce tutto):

```
http://sc-archive.lan:80 {
    reverse_proxy 192.168.1.11:8000
}
```

Ricarica Caddy:

```bash
sudo systemctl reload caddy
sudo systemctl status caddy
```

---

## 4. PC Windows — File hosts

Apri Blocco Note **come amministratore** e modifica:

```
C:\Windows\System32\drivers\etc\hosts
```

Aggiungi in fondo:

```
192.168.1.20    sc-archive.lan
```

> **Attenzione**: l'IP deve essere quello del **Raspberry Pi**, non del PC Windows.

Svuota la cache DNS:

```powershell
ipconfig /flushdns
```

---

## 5. Log del servizio

### SC-ARCHIVE (WSL2 — systemd utente)

```bash
# Segui i log in tempo reale
journalctl --user -u sc-archive.service -f

# Ultime 100 righe
journalctl --user -u sc-archive.service -n 100

# Tutto lo storico
journalctl --user -u sc-archive.service
```

### Caddy (Raspberry Pi)

```bash
# Segui i log in tempo reale
sudo journalctl -u caddy -f

# Ultime 100 righe
sudo journalctl -u caddy -n 100
```

---

## 6. Verifica

```powershell
ping sc-archive.lan
# deve rispondere con 192.168.1.20
```

Apri il browser: `http://sc-archive.lan` — SC-ARCHIVE deve essere raggiungibile.

---

## Note

- **Chrome blocca `.local`**: usa `.lan` come TLD per i domini LAN locali.
- **IP WSL2 volatile**: il Task Scheduler risolve il problema ad ogni riavvio di Windows.
- **HTTPS**: quando si aggiunge un dominio pubblico, Caddy gestisce Let's Encrypt automaticamente. Aggiornare il Caddyfile sostituendo `http://sc-archive.lan` con il dominio reale.
- **Basic Auth**: può essere aggiunta a livello Caddy (`basicauth`) o direttamente nell'app FastAPI.

---

*Documentazione operativa SC-ARCHIVE // Aegis Network Protocol.*
