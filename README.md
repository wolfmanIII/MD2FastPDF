# SC-ARCHIVE // Spacecraft Documentation Management System

**Versione 5.26.0** // GOTENBERG SERVIZIO ESTERNO & RELAZIONI: CARTELLE COLLASSABILI

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

## 📚 Documentazione di Configurazione

Riferimento rapido a tutte le guide di setup — scegli il percorso in base a come vuoi installare SC-ARCHIVE:

## **Installazione locale (bare-metal, senza Docker)**

- [docs/installazione-pyenv-poetry.md](docs/installazione-pyenv-poetry.md) — pyenv + Poetry, ambiente Python
- [docs/ollama_ubuntu_24_04_guida.md](docs/ollama_ubuntu_24_04_guida.md) — installazione Ollama (Ubuntu 24.04)
- [docs/rete-lan-caddy.md](docs/rete-lan-caddy.md) — esporre SC-ARCHIVE su LAN con nome host personalizzato via Caddy (bare-metal, ibrido, o Docker — copre tutti gli scenari)

## **Deploy Docker**

- [docs/configurazione-docker.md](docs/configurazione-docker.md) — guida completa: build, volumi, permessi, Ollama in rete (checklist), aggiornamento, troubleshooting

## 🚀 Features

- **Pannello RELAZIONI a struttura cartelle, collassabili**: nell'editor, le relazioni tipizzate di un'entità sono raggruppate come nel pannello ARCHIVE_TREE (icona cartella aperta/chiusa, indentazione, colori coerenti) invece di un elenco a virgole. Gruppi chiusi di default, click sull'header per espandere/collassare. Tooltip fixed-position (immune al clipping dei contenitori scrollabili) sui nomi troncati. Entità duplicate tra gruppi forward/inverso deduplicate; fonti realmente `type: scene` separate dalle altre sotto "Riferimenti".
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
- **Aegis Graph View**: vista a grafo (`/graph`) dei collegamenti tra i documenti dell'archivio, su due livelli: menzioni informali (link Markdown standard nel corpo del testo) e relazioni tipizzate dichiarate nel frontmatter (colore/tratteggio per tipo, filtro con legenda e checkbox "Seleziona tutte"). Force-directed layout D3.js con pannello controlli live — dimensione nodi (default al minimo dello slider), spessore linee, forza di repulsione, distanza/forza collegamenti, dissolvenza testi su zoom — più ricerca, toggle "nascondi orfani", colorazione nodo per cartella, frecce direzionali e hover highlight su nodo + vicini diretti. Click su un nodo apre il documento nell'editor.
- **Relazioni tipizzate**: dichiara relazioni strutturate (`crew`, `member_of`, `located_in`, `hostile_to`, `owns`, `owes_debt_to`, `reports_to`, `allied_with`, `mentor_of`, `npcs`, `organizations`) nel frontmatter YAML di un file. Query dirette e inverse gratuite (dichiari da un lato solo, l'altro compare da solo), validazione di dominio non bloccante (un tipo inatteso finisce solo nel report diagnostico), indice live per root d'archivio, endpoint `/api/entities/{key}/relations` e `/api/diagnostics/relations`, sezione RELAZIONI nell'editor. Vedi `docs/guida-relazioni-tipizzate.md`.
- **Terminale Archivio** (`/archive-terminal`): chat in linguaggio naturale sopra `RelationIndex` via Ollama — traduce la domanda in una query strutturata, chiede di disambiguare se il nome corrisponde a più entità, ripiega su ricerca testuale se la traduzione non è valida. Mai testo generato liberamente sulla campagna. Vedi `docs/ANALISI-relazioni-query-nl.md`.
- **Rebranding**: nuovo logo esagonale (`static/logo.png`, trasparenza generata via flood-fill dai bordi) nell'header; favicon vettoriale semplificata (`favicon.svg`) per restare leggibile a 16px, con set completo `favicon.ico`/PNG multi-size e `apple-touch-icon` a piena risoluzione.
- **Editor in preview di default**: i documenti Markdown si aprono in modalità preview invece del buffer grezzo.
- **Badge archivio persistente**: nome della cartella archivio attiva visibile in ogni pagina (non solo in dashboard), con aggiornamento istantaneo al cambio directory.
- **Nav MODULES**: voci di navigazione secondarie (Archive, Graph, Library, Comms, Admin) raggruppate in un dropdown per una barra superiore meno affollata.
- **Neural Core Availability Gating**: i controlli AI nell'editor (Neural Scan, Mermaid Synthesis, Ghost-Text) e nelle viste elenco (Neural Scan) si disattivano con tooltip esplicito quando il Neural Link è spento nelle Impostazioni o Ollama non è raggiungibile — prima restavano sempre attivi e fallivano solo al click. Il pannello NEURAL_CORE della dashboard distingue "raggiungibile ma disattivato" (ambra) da un vero problema di rete (rosso).
- **Deploy Docker rafforzato**: container applicativo eseguito come utente non privilegiato (non più root), immagini pinnate per digest, healthcheck su tutti i servizi con avvio ordinato, verifica checksum del binario Tailwind, nessuna password admin di default prevedibile (generata casualmente se non impostata). Guida completa in [docs/configurazione-docker.md](docs/configurazione-docker.md).

## 🔐 Primo Accesso (Inizializzazione Operatore)

Al **primo avvio**, SC-ARCHIVE crea automaticamente l'utente `admin` e il workspace in `~/sc-archive/admin/`. Se non hai impostato `AEGIS_ADMIN_PASSWORD`, la password viene **generata casualmente** e salvata in `~/.config/sc-archive/admin_password.txt` (permessi `600`) — nessun default fisso e prevedibile come `admin`/`admin`. La stessa password viene anche stampata nei log all'avvio come conferma immediata, ma il file è il riferimento persistente (i log possono ruotare).

**Sequenza obbligatoria al primo accesso:**

1. Avvia la stazione: `./bin/launch.sh`
2. Recupera la password generata: `cat ~/.config/sc-archive/admin_password.txt`
3. Apri il browser su `http://localhost:8000` e accedi con `admin` / la password recuperata
4. Apri **Settings** (icona ingranaggio) → sezione **OPERATOR_ACCESS_KEY**
5. Inserisci la password generata in "Current Key" e la tua nuova password in "New Key"
6. Clicca **ROTATE_KEY** — da questo momento userai la nuova password

> [!TIP]
> Per scegliere tu la password di default **prima** del primo avvio (quando `~/.config/sc-archive/users.json` non esiste ancora), esporta la variabile d'ambiente prima di lanciare:
>
> ```bash
> export AEGIS_ADMIN_PASSWORD="la-tua-password"
> ./bin/launch.sh
> ```
>
> Se `~/.config/sc-archive/users.json` esiste già, questa variabile non ha effetto — usa Settings per cambiare la password.
>
> [!NOTE]
> Per resettare l'utente admin, cancella il record `"admin"` da `~/.config/sc-archive/users.json` — al prossimo avvio viene ricreato con `AEGIS_ADMIN_PASSWORD` se impostata, altrimenti con una nuova password casuale (di nuovo salvata in `~/.config/sc-archive/admin_password.txt`).
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

### 7. Kernel di Conversione PDF (Gotenberg) e Strato Neurale (Ollama)

**Gotenberg**: sempre esterno, come Ollama — questo progetto non lo installa né lo
containerizza mai, in nessuno scenario (bare-metal o Docker). Va eseguito a parte
(installazione nativa, systemd, o una propria istanza/stack Docker indipendente) e il suo
indirizzo va impostato in Settings (o `gotenberg_ip` in `config/settings.json`).
`bin/launch.sh` si limita a verificare ad ogni avvio che l'endpoint configurato risponda,
segnalando in console se non è raggiungibile — nessuna creazione automatica, vedi
[`bin/ensure_services.sh`](bin/ensure_services.sh).

- **Avvio rapido (Docker)**: `docker run -d --name gotenberg --restart unless-stopped -p 3000:3000 gotenberg/gotenberg:8`

**Ollama**: sempre nativo, mai in Docker — `bin/launch.sh` verifica anch'esso che l'endpoint
configurato (`ollama_ip`) risponda, stessa diagnostica di Gotenberg e stesso
[`bin/ensure_services.sh`](bin/ensure_services.sh), ma senza alcuna gestione/avvio automatico
(vedi [docs/configurazione-docker.md](docs/configurazione-docker.md) per il criterio: mai su
Raspberry Pi/PC poco performanti, sempre nativo su host capaci):

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
- `bin/ensure_services.sh`: Verifica che Gotenberg e Ollama (entrambi servizi esterni, indirizzi da Settings) siano raggiungibili — solo diagnostica, nessuna creazione/avvio.
- `bin/aegis-migrate.sh`: Export/import completo dei dati per migrazione tra macchine.
- `Dockerfile`: Build multi-stage (css-builder ARM64, deps-builder, runtime).
- `docker-compose.yml`: Stack sc-archive + caddy con named volumes. Gotenberg e Ollama restano sempre esterni (non containerizzati da questo progetto).
- `docker/entrypoint.sh`: Init settings Docker, session key, bootstrap admin; parte come root per sistemare i permessi sui volumi, poi passa il controllo a `uvicorn` come utente non privilegiato (`gosu aegis`).
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

## 🐳 Deploy con Docker

Stack SC-ARCHIVE + Caddy come reverse proxy, containerizzati. Gotenberg e Ollama restano sempre esterni a questo stack — Gotenberg nella propria istanza/stack Docker indipendente, Ollama sempre nativo — esattamente come nel setup bare-metal. Funziona su qualsiasi host Linux con Docker (PC x86_64, server, Raspberry Pi 4/5 ARM64): le immagini sono multi-arch, nessun passaggio è specifico per il Pi. Su Raspberry Pi o PC poco performanti è consigliato tenere Ollama su un'altra macchina in LAN — vedi la guida completa.

**Guida completa**: [docs/configurazione-docker.md](docs/configurazione-docker.md)

### Quick Start

```bash
# 1. Clona il repository
git clone <repo-url> ~/sc-archive && cd ~/sc-archive

# 2. Configura le variabili d'ambiente
cp docker/.env.example .env
nano .env

# 3. Build e avvio
docker compose up -d --build
```

**Come compilare `.env`:**

```env
# Opzionale — se ometti questa riga, SC-ARCHIVE genera una password casuale al primo
# avvio e la salva in /home/aegis/.config/sc-archive/admin_password.txt (l'app gira
# come utente non privilegiato 'aegis', non come root — vedi docs/configurazione-docker.md).
# Impostala solo se vuoi scegliere tu la password admin.
AEGIS_ADMIN_PASSWORD=la-tua-password

# Opzionale — IP/porta di Gotenberg, sempre esterno a questo stack (es. http://192.168.1.50:3000).
# Se ometti questa riga, il default è http://host.docker.internal:3000 — utile se Gotenberg
# gira nella propria istanza Docker sulla stessa macchina che ospita questo stack.
# GOTENBERG_IP=http://192.168.1.X:3000

# Opzionale — IP del PC in LAN che esegue Ollama (es. http://192.168.1.50:11434).
# Se ometti questa riga, il default è http://host.docker.internal:11434, cioè
# "l'host Docker stesso" — utile se Ollama gira nativamente sulla stessa macchina
# del Pi/server che ospita i container.
OLLAMA_IP=http://192.168.1.X:11434
```

Entrambe le variabili sono opzionali: se lasci `.env` vuoto o non lo crei affatto, il sistema parte comunque con i default sopra descritti — a patto che Gotenberg sia effettivamente raggiungibile a quell'indirizzo (vedi "Avvio rapido Gotenberg" più sotto).

Il sistema è raggiungibile su `http://sc-archive.lan` (aggiungi l'IP del Pi in `/etc/hosts` sui dispositivi LAN).

**Avvio rapido Gotenberg** (se non già attivo altrove): `docker run -d --name gotenberg --restart unless-stopped -p 3000:3000 gotenberg/gotenberg:8`

**Componenti di questo stack**:

| Container | Ruolo |
| ----------- | ------- |
| `sc-archive` | Applicazione FastAPI |
| `caddy` | Reverse proxy (porta 80 → LAN) |

Gotenberg e Ollama non fanno parte di questo `docker-compose.yml` — sempre esterni, vedi sopra.

**Dati persistenti** in tre named volumes Docker: `sc-archive-config`, `sc-archive-userdata`, `sc-archive-workspaces`.

---

## 🧪 Test Suite

```bash
# Esegui tutti i test
poetry run pytest

# Con report di copertura
poetry run pytest --cov=logic --cov-report=term-missing
```

456 test, 0 fallimenti. Copertura: `blueprints.py` 93%, `comms.py` 93%, `groupspace.py` 92%, `relations.py` 100%, `relations_index.py` 95%, `relations_service.py` 100%, `query_translation.py` 100%. `conversion` e `render` richiedono Gotenberg — non inclusi nella suite unit; `oracle.py` è parzialmente coperto (`translate_query()` via `httpx.MockTransport`), il resto richiede Ollama.

---
*Progettato per i narratori della stazione SC-ARCHIVE.*
