# SC-ARCHIVE // Spacecraft Documentation Management System

**Versione 5.15.0** // AEGIS UX REFINEMENTS

> **Perché filesystem e niente database?** Non è una svista: è una scelta di design coerente col dominio. → [MANIFESTO.md](MANIFESTO.md)
>
> **Why filesystem and no database?** Not an oversight — a deliberate design choice fit to the domain. → [MANIFESTO.md](MANIFESTO.md)
>
> [!NOTE]
> **MD2FastPDF** is the internal technical name for the project core and backend services. **SC-ARCHIVE** is the external station designation and branding.

**SC-ARCHIVE** is an "Aegis Class" documentation management system designed for operational speed and professional PDF generation via the **Gotenberg** infrastructure.

## 🛠 Tech Stack

- **Core**: Python 3.13+ + FastAPI
- **Frontend**: HTMX + Tailwind CSS v4 Standalone CLI (v4.2.2) + Jinja2
- **Editor**: EasyMDE (CodeMirror 5)
- **PDF Engine**: Gotenberg (Chromium via Docker)
- **Neural Engine**: local Ollama (`qwen2.5-coder:7b`)
- **CSS Optimizer**: Tailwind CSS Standalone Compiler (v4.2.2)
- **Environment**: Poetry + pyenv

## 🚀 Features

- **File Metadata temporali**: Data di creazione e ultima modifica visibili sotto ogni file/directory nell'archive browser (`CRE DD/MM/YYYY HH:MM // MOD DD/MM/YYYY HH:MM`). Font mono, accent neon-cyan. Applicato anche ai risultati di ricerca.
- **Sidebar editor ridimensionabile**: Drag handle tra sidebar filetree e editor. Larghezza regolabile tra 120px e 600px, persistita in `localStorage`.
- **Aegis Group_Space**: Workspace filesystem condiviso per gruppo. Modello permessi asimmetrico (admin R+W su root, membri R+W su `shared/`). Browser, editor e CRUD file integrati nella navbar.
- **Aegis Blueprint Variable Injection**: Al click su un blueprint, rilevamento automatico dei placeholder `[UPPERCASE]` e form modale guidato per pre-compilarli prima dell'inserimento. Bypass diretto se nessun placeholder presente.
- **Aegis Blueprint**: Libreria template Markdown app-wide (`blueprints/`). Modal in toolbar editor per inserimento istantaneo in fondo al documento. Admin panel con gestione CRUD blueprint per categoria.
- **Aegis Groups & Admin Panel**: Sistema di gruppi utente con admin panel HTMX (`/admin`). CRUD utenti e gruppi. Chiunque abbia il gruppo `"admin"` ha privilegi admin. Messaggistica filtrata per gruppo condiviso — admin bypassa il filtro e può scrivere a tutti gli utenti senza restrizioni (ruolo GM/Referee).
- **Aegis COMMS**: Messaggistica filesystem-based multi-utente. Hub tabbato (RECEPTION_ARRAY / OUTBOUND_LOG / STAGING_BUFFER), compose modal con preview Markdown live, draft management, unread badge HTMX-polled ogni 30s.
- **Aegis Filetree**: Sidebar albero directory collassabile nell'editor con navigazione lazy, highlight del file attivo e persistenza stato in `localStorage`.
- **Aegis Slim-Tech Editor**: Interfaccia di scrittura compattata con supporto **Fullscreen Breakthrough** (bypass automatico dei filtri glass-panel).
- **Native Multi-Tab Navigation**: Pieno supporto per apertura in nuove schede (Ctrl+Click) su Dashboard, File Grid e Breadcrumbs.
- **DaisyUI Tooltips**: Indicatori di funzione ad alta priorità (`z-index: 500+`) coerenti con la stratigrafia industriale.
- **Aegis Render Engine**: Export PNG singolo e ZIP bulk dei diagrammi Mermaid direttamente da file `.md` o dalla toolbar dell'editor.
- **Backend Services Status**: Due pannelli dashboard separati per Gotenberg e Ollama con telemetria real-time (stato, endpoint, modelli chat/embedding).
- **Aegis Oracle (Precision v5.2.0)**:
  - **Context Isolation**: Utilizzo di delimitatori `[CONTEXT_START]` per il Ghost-Text, eliminando il fenomeno dell'"eco" e garantendo il completamento delle frasi.
    - **Broadcast Offline Protocol**: Il sistema comunica lo stato disattivato tramite alert pulsanti (`!! NEURAL_PROTOCOL_OFFLINE !!`) e banner informativi nel modale Mermaid.
    - **Hardened Scans**: Finestra di contesto a 16.384 token e temperatura 0.3 per riepiloghi tecnici ad alta precisione.
    - **Surgical Sanitization**: Sanitizzazione chirurgica delle allucinazioni HTML per preservare la struttura HUD.
- **Aegis Uplink Config (v5.0.0)**: Terminale di configurazione centralizzato per la gestione dei parametri operativi (Ollama, Gotenberg, Neural Models) con persistenza locale in `config/settings.json`.
- **Aegis Industrial UI**: Standardizzazione globale di tutti i campi input, select e textarea con estetica terminale pura, dimensioni ottimizzate (12px) e rimozione dei bordi framework.
- **Neural Model Intelligence**: Filtro automatico dei modelli Ollama per escludere i motori di embedding dai menu di chat e sintesi.
- **Dashboard Telemetry 2.0**: Monitoraggio real-time di CPU e Memoria via HTMX (`/stats`) e aggiornamento automatico dello stato servizi al salvataggio della configurazione.
- **Global PDF Branding**: Esportazione PDF automatizzata con testata e piè di pagina SC-ARCHIVE (configurabile via Uplink).
- **PDF Bookmark Injection**: outline PDF gerarchico iniettato automaticamente dopo la conversione Gotenberg — titoli `#`/`##`/`###` diventano bookmark navigabili nel pannello del lettore PDF. Localizzazione pagina + coordinata Y via `pypdf` visitor (CTM×TM). Best-effort scroll esatto (`Fit.xyz`); fallback a cima pagina se il testo non è estraibile.
- **Aegis Graph View**: vista a grafo (`/graph`) dei collegamenti Markdown (`[testo](path.md)`) tra i documenti dell'archivio. Force-directed layout D3.js con pannello controlli live — dimensione nodi, spessore linee, forza di repulsione, distanza/forza collegamenti, dissolvenza testi su zoom — più ricerca, toggle "nascondi orfani", colorazione nodo per cartella, frecce direzionali e hover highlight su nodo + vicini diretti. Click su un nodo apre il documento nell'editor.
- **Rebranding**: nuovo logo esagonale (`static/logo.png`, trasparenza generata via flood-fill dai bordi) nell'header; favicon vettoriale semplificata (`favicon.svg`) per restare leggibile a 16px, con set completo `favicon.ico`/PNG multi-size e `apple-touch-icon` a piena risoluzione.
- **Editor in preview di default**: i documenti Markdown si aprono in modalità preview invece del buffer grezzo.
- **Badge archivio persistente**: nome della cartella archivio attiva visibile in ogni pagina (non solo in dashboard), con aggiornamento istantaneo al cambio directory.
- **Nav MODULES**: voci di navigazione secondarie (Archive, Graph, Library, Comms, Admin) raggruppate in un dropdown per una barra superiore meno affollata.

## 🔐 Primo Accesso (Inizializzazione Operatore)

Al **primo avvio**, SC-ARCHIVE crea automaticamente l'utente `admin` con password di default `admin` e il workspace in `~/sc-archive/admin/`.

**Sequenza obbligatoria al primo accesso:**

1. Avvia la stazione: `./bin/launch.sh`
2. Apri il browser su `http://localhost:8000`
3. Effettua il login con `admin` / `admin`
4. Apri **Settings** (icona ingranaggio) → sezione **OPERATOR_ACCESS_KEY**
5. Inserisci `admin` in "Current Key" e la nuova password in "New Key"
6. Clicca **ROTATE_KEY** — da questo momento userai la nuova password

> [!TIP]
> Per scegliere una password di default diversa da `admin` **prima** del primo avvio (quando `~/.config/sc-archive/users.json` non esiste ancora), esporta la variabile d'ambiente prima di lanciare:
>
> ```bash
> export AEGIS_ADMIN_PASSWORD="la-tua-password"
> ./bin/launch.sh
> ```
>
> Se `~/.config/sc-archive/users.json` esiste già, questa variabile non ha effetto — usa Settings per cambiare la password.
>
> [!NOTE]
> Per resettare l'utente admin, cancella il record `"admin"` da `~/.config/sc-archive/users.json` — al prossimo avvio viene ricreato con `AEGIS_ADMIN_PASSWORD` (default: `admin`).
> In alternativa, usa direttamente `./bin/create_user.sh admin nuova_password` per sovrascrivere l'hash senza toccare il file.

**Workspace:** ogni utente ha una cartella dedicata in `~/sc-archive/<username>/` e non può uscire da quel subtree. Solo `admin` può selezionare qualsiasi cartella della home tramite il **Root Picker** nella dashboard — la scelta viene salvata e ripristinata ad ogni login.

---

## 📦 Protocollo di Installazione (Setup Manual)

La stazione **SC-ARCHIVE** richiede un ambiente Linux (Ubuntu 24.04 raccomandato). Seguire la sequenza completa su una macchina fresh. Per i dettagli su pyenv e Poetry, vedere [docs/installazione-pyenv-poetry.md](docs/installazione-pyenv-poetry.md).

### 1. Dipendenze di Build

```bash
sudo apt update && sudo apt install -y \
    build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev curl \
    git libncursesw5-dev xz-utils tk-dev libxml2-dev \
    libxmlsec1-dev libffi-dev liblzma-dev
```

### 2. Pyenv

```bash
curl https://pyenv.run | bash
```

Aggiungere al `~/.bashrc`:

```bash
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```

```bash
source ~/.bashrc
```

### 3. Python 3.13 (dalla directory del progetto)

```bash
pyenv install $(cat .python-version)
pyenv local $(cat .python-version)
```

### 4. Poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Se `~/.local/bin` non è nel PATH aggiungerlo al `~/.bashrc` e ricaricare.

### 5. Dipendenze Python

```bash
poetry config virtualenvs.in-project true
poetry install --with dev
```

### 6. Tailwind CSS v4 (Standalone CLI)

```bash
curl -fsSL https://github.com/tailwindlabs/tailwindcss/releases/download/v4.2.2/tailwindcss-linux-x64 \
    -o tailwindcss
chmod +x tailwindcss
```

### 7. Kernel di Conversione PDF (Gotenberg)

```bash
docker run -d -p 3000:3000 --restart unless-stopped gotenberg/gotenberg:8
```

### 8. Strato Neurale (Ollama)

- **Installazione**: `curl -fsSL https://ollama.com/install.sh | sh`
- **Modello Consigliato**: `ollama pull qwen2.5-coder:7b`
- **Guida Dettagliata (Ubuntu 24.04)**: [docs/ollama_ubuntu_24_04_guida.md](docs/ollama_ubuntu_24_04_guida.md)

## 🚀 Sequenza di Avvio (Boot Sequence)

Per inizializzare la stazione e attivare tutti i watcher (Tailwind & Uvicorn):

```bash
./bin/launch.sh
```

> [!NOTE]
> Al primo avvio, `bin/launch.sh` genera automaticamente una chiave crittografica casuale e la persiste in `~/.config/sc-archive/session.key` (via `openssl rand -hex 32`). Questa chiave viene usata come `AEGIS_SECRET_KEY` per firmare i cookie di sessione. Nei lanci successivi viene riusata — non verrà mai sovrascritta automaticamente.

## 📂 Struttura del Progetto

- `main.py`: Punto di convergenza dei router Aegis.
- `logic/`: Logica di business (files, conversion, oracle, render, auth, comms, blueprints, groupspace).
- `routes/`: APIRouter modules (core, archive, editor, pdf, config, oracle, comms, admin, blueprint, groupspace).
- `blueprints/`: Template Markdown app-wide organizzati per categoria (`narrative/`, ...).
- `config/`: Package Python — `settings.py` (SettingsManager) + `settings.json` (store persistente).
- `templates/components/`: Frammenti HTML/HTMX industriali.
- `templates/layouts/`: Layout base (`base.html`).
- `static/css/`: Design system Aegis — `output.css`, `editor-aegis.css`, `pdf-industrial.css`, `pdf-preview.css`.
- `tests/`: Suite pytest — unit test e async I/O test per il layer `logic/`.
- `docs/`: Database di documentazione operativa e tecnica.
- `bin/launch.sh`: Start script (Tailwind watcher + Uvicorn).
- `bin/aegis-migrate.sh`: Export/import completo dei dati per migrazione tra macchine.
- `Dockerfile`: Build multi-stage (css-builder ARM64, deps-builder, runtime).
- `docker-compose.yml`: Stack sc-archive + gotenberg + caddy con named volumes.
- `docker/entrypoint.sh`: Init settings Docker, session key, bootstrap admin.
- `docker/Caddyfile`: Reverse proxy `http://sc-archive.lan:80`.
- `docker/.env.example`: Template variabili d'ambiente Docker.

## 🚚 Migrazione tra Macchine

Lo script `bin/aegis-migrate.sh` esporta e reimporta tutti i dati applicazione in un unico archivio `.tar.gz`.

**Dati inclusi nell'export:**

- `config/settings.json` — configurazione runtime (endpoint, modelli, flags)
- `~/.config/sc-archive/users.json` — utenti registrati con hash password
- `~/.config/sc-archive/groups.json` — gruppi definiti
- Directory `blueprints/` — template Markdown
- Directory `workspace_base` — tutti i documenti dell'archivio

```bash
# Sulla macchina sorgente
./bin/aegis-migrate.sh export /tmp

# Copia l'archivio sulla macchina destinazione, poi:
./bin/aegis-migrate.sh import /tmp/aegis-export-*.tar.gz
```

L'import è interattivo: mostra il percorso originale di blueprints e workspace e chiede dove ripristinarli. Se il percorso workspace cambia, `settings.json` viene aggiornato automaticamente.

---

## 🐳 Deploy su Raspberry Pi (Docker)

Stack completo SC-ARCHIVE containerizzato per Raspberry Pi 4/5 (ARM64), con Caddy come reverse proxy e Gotenberg integrato.

**Guida completa**: [docs/docker-raspberry.md](docs/docker-raspberry.md)

### Quick Start

```bash
# 1. Clona il repository sul Pi
git clone <repo-url> ~/sc-archive && cd ~/sc-archive

# 2. Configura le variabili d'ambiente
cp docker/.env.example .env
nano .env   # imposta AEGIS_ADMIN_PASSWORD e OLLAMA_IP

# 3. Build e avvio
docker compose up -d --build
```

Il sistema è raggiungibile su `http://sc-archive.lan` (aggiungi l'IP del Pi in `/etc/hosts` sui dispositivi LAN).

**Componenti**:

| Container | Ruolo |
| ----------- | ------- |
| `sc-archive` | Applicazione FastAPI |
| `gotenberg` | PDF engine (Chromium headless) |
| `caddy` | Reverse proxy (porta 80 → LAN) |

**Dati persistenti** in tre named volumes Docker: `sc-archive-config`, `sc-archive-userdata`, `sc-archive-workspaces`.

---

## 🧪 Test Suite

```bash
# Esegui tutti i test
poetry run pytest

# Con report di copertura
poetry run pytest --cov=logic --cov-report=term-missing
```

170 test, 0 fallimenti. Copertura: `blueprints.py` 100%, `comms.py` 93%, `groupspace.py` 92%. I moduli `conversion`, `oracle`, `render` richiedono Gotenberg/Ollama — non inclusi nella suite unit.

---
*Progettato per i narratori della stazione SC-ARCHIVE.*
