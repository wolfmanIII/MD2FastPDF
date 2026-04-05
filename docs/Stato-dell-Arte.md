# Stato del Progetto: SC-ARCHIVE

**Stato Attuale**: Op_Ready / Versione 5.11.0
**Ultimo Aggiornamento**: 5 Aprile 2026

---

## 1. Funzionalità Implementate (Aegis Stack)

### 1.1 Gestione File & Discovery

- Navigazione filesystem locale con breadcrumbs dinamici e root-selection modale.
- **UP_DIRECTORY**: navigazione rapida alla directory padre nel browser file.
- **Ricerca Globale Aegis**: motore di scansione ricorsiva per file `.md`, `.html` e `.pdf` con search bar DaisyUI integrata (`SCAN_QUERY //`).
- **Multiformat Viewer**: supporto PDF (Aegis Preview) e HTML (scheda esterna).
- **Operazioni File**: creazione, rinomina, eliminazione con conferma modale e feedback HTMX.
- **Bottoni azione sempre visibili**: tutti i controlli file (rename, delete, export Mermaid, neural scan) sempre visibili con tooltip DaisyUI.

### 1.2 Editor Markdown (Aegis Slim-Tech)

- **EasyMDE** con toolbar estesa: salvataggio, export PDF, export Mermaid singolo/bulk, commit snapshot, neural hint, configurazione Uplink.
- Evidenziatura sintassi in preview (Highlight.js), Mermaid.js per diagrammi interattivi.
- **Fullscreen Breakthrough**: bypass automatico dei filtri `backdrop-filter` genitori per fullscreen nativo.
- **Native Multi-Tab**: Ctrl+Click su qualsiasi link apre in nuova scheda.

### 1.2b Aegis Filetree [4.3] — COMPLETED

- **Sidebar albero directory**: colonna sinistra collassabile (260px) esclusiva della view editor.
- **Lazy expand**: cartelle caricano i figli via HTMX solo al click — nessun render ricorsivo totale.
- **Toggle `«`/`»`**: stato collasso persistito in `localStorage`.
- **Highlight file attivo**: documento aperto evidenziato con bordo sinistro cyan.
- **State persistence navigazione**: path espansi salvati in `localStorage` e ripristinati via `htmx:afterSettle` dopo ogni caricamento file.
- **Fullscreen safe**: sidebar nascosta automaticamente in fullscreen EasyMDE (CSS condizionale su `.aegis-fullscreen-active`).
- **Palette coerente**: dir `neon-text` + drop-shadow cyan, `.md` `neon-text`, `.pdf` icona `text-red-400`, `.html` icona `text-amber-400`.
- **Icone SVG outline**: `folder.html` (chiusa) / `folder-open.html` (aperta) — `fill="none"`, stroke puro, identici al file browser.

### 1.3 Esportazione PDF (Aegis Engine)

- Integrazione Gotenberg (Docker) per rendering Chromium professionale.
- **HUD_PRINT Toggle**: header/footer branded SC-ARCHIVE (modalità HUD) o solo numero di pagina (slim).
- **Global PDF Branding**: testata e piè di pagina configurabili da Uplink Config, persistiti localmente.
- Sanitizzazione XSS via `bleach` sulla pipeline di conversione.
- **Industrial PDF CSS**: stylesheet `static/css/pdf-industrial.css` caricato a module init — nessun CSS inline nel codice Python.

### 1.4 Aegis Render Engine (Mermaid Image Export)

- **PNG Export**: rendering del singolo blocco Mermaid in PNG via Gotenberg (screenshot headless).
- **ZIP Bulk Export**: tutti i blocchi Mermaid del documento in un archivio `.zip`.
- Accessibile dalla toolbar editor e dal bottone nella griglia file (per ogni `.md`).
- Modal lista blocchi con apertura PNG in nuova scheda.

### 1.5 Neural Interface — AEGIS ORACLE

- **Ghost-Text (Neural Hint)**: completamento predittivo on-demand (300 token), accettazione via TAB.
- **Mermaid Synthesis**: generazione diagrammi da linguaggio naturale via Ollama (Modello consigliato: `qwen2.5-coder:7b`).
- **Aegis Intelligence Scan (Hardened)**:
  _**Context Precision**: Sistema di isolamento `[CONTEXT_START]` per il Ghost-Text, eliminando la ripetizione del testo utente e garantendo la chiusura delle frasi tronche.
  _**Surgical Sanitization**: Filtro attivo su `div` allucinati dal modello per proteggere la stabilità del layout HUD.
  _**Protocol Feedback**: Notifiche visive immediate (`!! NEURAL_PROTOCOL_OFFLINE !!`) e banner informativi nei modali se il Neural Link è spento.
  _**Protocol Hard-Stop**: Isolamento totale del backend; se disattivato, il sistema non effettua probe o chiamate esterne.
- **Multi-endpoint probe**: rileva automaticamente Ollama su `localhost:11434` o `172.31.112.1:11434`. Persistenza via `settings.json`.
- **Resilienza ConnectTimeout**: errori di connessione gestiti come `OracleError` — mai propagati all'ASGI layer.

### 1.6 Dashboard & Telemetria

- **SYSTEM_STATUS**: CPU, memoria, root archivio, stato API gateway (refresh 30s).
- **GOTENBERG panel**: stato, endpoint, funzione (ONLINE / DEGRADED / OFFLINE).
- **OLLAMA panel**: stato, endpoint, modelli caricati separati per categoria (`CHAT_MODELS` / `EMBED_MODELS`).
- **RECENT_FRAGMENTS**: ultimi 5 file modificati con timestamp.
- **STORAGE_NODE**: dimensione archivio, conteggio file, percentuale utilizzo disco.
- Ordine pannelli: System → Backend Services → Recent/Storage.

### 1.7 Aegis Uplink Config

- **Centralized Persistence**: Gestione totale dei parametri operativi in `config/settings.json` (Ollama, Gotenberg, Modelli IA, Flags). Modulo: `config/settings.py`.
- **Reactive Refresh**: Aggiornamento automatico della Dashboard via HTMX al salvataggio della configurazione (`HX-Trigger: settings-updated`).
- **Industrial Form Standard**: Unificazione globale dello stile input/select via `base.html` (12px, borderless, mono, focus neon).
- **Conditional Logic**: Disattivazione visiva e funzionale dei campi dipendenti (Ollama/Models) quando il `Neural Link` è spento.
- **Data Loss Prevention**: Logica di merge per preservare i parametri salvati anche quando i campi sono inattivi nella UI.

### 1.8 UX, Sicurezza & CSP Compliance

- Transizioni `scan-in` / `soft-exit` su tutte le modali.
- Sanitizzazione path obbligatoria (prevenzione `../`), sanitizzazione Markdown (XSS via `bleach`).
- DaisyUI tooltip su tutti i controlli azione (z-index stratificato).
- **CSP Ready**: eliminati tutti gli attributi `style=` inline dai template e dagli snippet HTML generati dai route. Solo 2 eccezioni strutturali (valori dinamici Jinja2: `--w: {{ value }}%`).
- CSS estratti in file statici dedicati (`editor-aegis.css`, `pdf-industrial.css`, `pdf-preview.css`).

### 1.9 AEGIS IDENTITY — Autenticazione Multi-Utente [4.10] (v5.5.1)

- **Login Page**: pagina `templates/layouts/login.html` standalone con tema Aegis Industrial.
- **Session Auth**: `SessionMiddleware` (starlette/itsdangerous) con cookie firmato; `auth_middleware` verifica la sessione e blocca ogni path non-pubblico con redirect a `/login`.
- **HTMX-aware redirect**: header `HX-Redirect` per le richieste HTMX, `302` per le normali.
- **Per-User Workspace Isolation**: `ContextVar[Path]` (`_REQUEST_ROOT`) in `logic/files.py` — ogni request async riceve il root dell'utente autenticato senza refactoring delle firme.
- **UserStore + AuthService**: separazione SOLID — `UserStore` gestisce `config/users.json`, `AuthService` espone autenticazione, creazione utente, cambio password, aggiornamento root.
- **Password Hashing**: `bcrypt` (cost factor 12) per tutti gli hash.
- **Admin Bootstrap**: al primo avvio, se `users.json` è vuoto, viene creato `admin` con password `admin` (sovrascrivibile via `AEGIS_ADMIN_PASSWORD` env var).
- **OPERATOR_ACCESS_KEY**: sezione nella Settings modal (`POST /auth/password`) per cambio password autenticato.
- **Root Picker persistente**: la selezione root viene salvata per-utente in `users.json` via `POST /config/select-root`.
- **Navbar**: username corrente e pulsante `// LOGOUT` visibili in ogni pagina autenticata.
- **CLI create_user**: `bin/create_user.sh <username> <password>` per provisioning operatori via terminale.

### 1.10 AEGIS COMMS — Sistema di Messaggistica [5.0] (v5.6.0)

- **Struttura cartelle**: `comms/{inbound,outbound,staging}/` nella root utente. Tutti gli utenti (incluso admin): `~/sc-archive/{user}/comms/`. Creazione automatica alla registrazione. ✓
- **Formato**: file `.md` con frontmatter (id, from, to, subject, timestamp, read). Parsing `re` stdlib — zero dipendenze aggiuntive. ✓
- **Invio**: dual-write su `outbound/` sender + `inbound/` recipient. Cross-workspace write con path assoluti + security assertion su `Path.home()`. ✓
- **Broadcast GM**: admin trasmette a `ALL` — copia individuale in ogni `inbound/` (read/unread per-utente indipendente). ✓
- **Bozze**: `staging/` — editabili, promovibili a trasmissione. Draft pre-fill in compose modal. ✓
- **Unread badge**: navbar HTMX-polled ogni 30s. `hx-push-url="false"` per evitare URL pollution. Invisibile se count = 0. ✓
- **UI**: hub tabbato (`RECEPTION_ARRAY` / `OUTBOUND_LOG` / `STAGING_BUFFER`), compose modal con preview Markdown live, message reader con `render_md`. Tab ricaricano l'intero hub via `/comms?tab=X` per aggiornare lo stato attivo correttamente. ✓
- **Prose CSS**: regole `.prose` custom in `main.css` per rendering Markdown (liste, heading, codice, tabelle) — @tailwindcss/typography non disponibile nel CLI standalone Tailwind v4. ✓

### 1.11 AEGIS GROUPS & ADMIN PANEL [5.1] (v5.7.0)

- **GroupStore**: persistenza `~/.config/sc-archive/groups.json`. CRUD asincrono — crea, lista, elimina (bloccato se ha utenti). ✓
- **UserRecord.groups**: campo `list[str]` aggiunto con retrocompatibilità. ✓
- **Admin promozione via gruppo**: chiunque abbia `"admin"` in `groups` è admin. `require_admin` FastAPI dependency. ✓
- **Admin panel** (`/admin`): CRUD completo utenti e gruppi. Tab `CREW_REGISTRY` / `TEAM_INDEX` / `BLUEPRINT_ARCHIVE`. Tab ricaricano l'intero pannello via `/admin?tab=X` per aggiornare lo stato attivo. ✓
- **Messaggistica filtrata**: `CommsManager.allowed_recipients()` — destinatari = gruppo condiviso col sender **o** gruppo `"admin"`. ✓

### 1.12 AEGIS BLUEPRINT [4.7] (v5.8.0) — COMPLETED

- **Template library app-wide**: blueprint Markdown in `blueprints/{categoria}/` nella root progetto. ✓
- **Gallery modal**: bottone in toolbar editor (`BLUEPRINT_ARCHIVE`) apre modal con blueprint raggruppati per categoria. Click inserisce il contenuto in fondo al buffer editor (con separatore `---` se il file non è vuoto). ✓
- **Admin management**: tab `BLUEPRINT_ARCHIVE` nel pannello SYS_ADMIN — form crea/sovrascrive blueprint, lista con PURGE per eliminazione. ✓
- **5 template iniziali** in `blueprints/narrative/`: Session Log, NPC Profile, Planet Description, Ship Description, Location Description. ✓
- **Path sanitization**: `BlueprintManager._sanitize()` previene traversal fuori da `blueprints/`. ✓

### 1.13 AEGIS GROUP_SPACE (v5.9.0) — COMPLETED

- **Workspace condiviso per gruppo**: `~/sc-archive/{group_name}/` creato automaticamente alla creazione del gruppo. Boot migration per gruppi preesistenti. ✓
- **Modello permessi**: root del gruppo — admin R+W, membri R; `shared/` — membri R+W, admin R. Enforced a livello `logic/groupspace.py` (zero fiducia nel frontend). ✓
- **GROUP_SPACE hub**: link in navbar, lista gruppi accessibili all'utente corrente. ✓
- **Browser**: navigazione file nel workspace di gruppo con indicatore `READ_ONLY` / `READ_WRITE` sulla directory corrente. ✓
- **Editor**: visualizzazione e modifica file nel workspace di gruppo. Textarea `readonly` e toolbar ridotta (no save) se l'area è in sola lettura. ✓
- **CRUD file**: crea, elimina file — bloccato se l'utente non ha permessi di scrittura nella directory corrente. ✓
- **Path sanitization**: `GroupSpaceManager.sanitize()` previene traversal fuori da `{workspace_base}/{group_name}/`. ✓
- **Accesso revoca immediata**: accesso verificato a ogni request da `GroupSpaceAccess.has_access()` — la rimozione dal gruppo è effettiva alla prossima request. ✓

### 1.15 MODAL STANDARDIZATION + MIGRATION TOOL (v5.11.0) — COMPLETED

- **Standardizzazione modali**: tutte le 10 modali dell'applicazione refactorate allo stile `blueprint_modal.html` — shell `modal-box bg-zinc-900 border border-zinc-700 rounded-none p-0`, header con prefisso `//` in `neon-text`, close button ghost, footer con `ABORT //` + azione primaria. Modali oracle/mermaid usano `text-violet-400` per coerenza cromatica con il tema Oracle. ✓
- **Settings modal**: larghezza `70vw` via inline style — unico modo affidabile per bypassare il `max-width` hardcoded di DaisyUI `modal-box`. Layout flex colonna con area di scroll interna isolata. ✓
- **`bin/aegis-migrate.sh`**: script bash per export/import completo dei dati applicazione. Export crea `.tar.gz` con timestamp contenente settings, utenti, gruppi, blueprints e workspace. Import interattivo con rimappatura percorsi e aggiornamento automatico di `settings.json`. ✓

### 1.14 AEGIS TEST SUITE (v5.9.1) — COMPLETED

- **Suite pytest**: 170 test, 0 fallimenti. Eseguiti su entrambi i backend anyio (`asyncio` e `trio`). ✓
- **Unit test** (`tests/test_auth.py`, `test_comms.py`, `test_groupspace.py`, `test_blueprints.py`): 60 test su classi pure — nessun I/O, nessuna rete, nessun filesystem reale. ✓
- **Async I/O test** (`tests/test_*_async.py`): 110 test su operazioni filesystem async tramite fixture `tmp_path` + `monkeypatch`. ✓
- **Isolamento**: `patch_groupspace_base`, `patch_blueprints_root`, `patch_comms_base` — ogni test usa una directory isolata, nessuna scrittura sul filesystem reale. ✓
- **Copertura**: `blueprints.py` 100%, `comms.py` 93%, `groupspace.py` 92%. I moduli `conversion`, `oracle`, `render` richiedono servizi esterni (Gotenberg/Ollama) — esclusi dalla suite unit. ✓
- **Dev dependencies**: `pytest >=8.0`, `pytest-cov >=6.0`, `pytest-anyio` in `[tool.poetry.group.dev.dependencies]`. ✓

---

## 2. Infrastruttura Tecnica

| Componente | Tecnologia |
| --- | --- |
| Backend | FastAPI (Python 3.13) + anyio + httpx |
| Frontend | HTMX + Tailwind v4 (standalone CLI) + DaisyUI + Jinja2 |
| Editor | EasyMDE (CodeMirror 5) |
| PDF Engine | Gotenberg (Chromium via Docker) |
| AI Layer | Ollama locale (`qwen2.5-coder:7b`), GPU offload Pascal-class |
| Render Engine | Gotenberg screenshot headless per PNG Mermaid |
| Environment | Poetry + pyenv (Python 3.13) |

### Package Structure

```text
logic/          __init__.py + files.py, conversion.py, oracle.py, render.py, auth.py, comms.py, blueprints.py, groupspace.py, exceptions.py
routes/         __init__.py (build_breadcrumbs) + core, archive, editor, pdf, config, oracle, login, comms, admin, blueprint, groupspace, deps
config/         __init__.py + settings.py (SettingsManager) + settings.json
blueprints/     narrative/ (session-log, npc-profile, planet-description, ship-description, location-description)
~/.config/sc-archive/   users.json, groups.json, session.key
static/css/     output.css, editor-aegis.css, pdf-industrial.css, pdf-preview.css, main.css
bin/            launch.sh, create_user.sh, aegis-migrate.sh
```

---

## 3. Roadmap

| Fase | Codice | Stato |
| --- | --- | --- |
| [4.0] | AEGIS ORACLE | **COMPLETED** |
| [4.1] | AEGIS REFACTOR | **COMPLETED** |
| [4.2] | AEGIS RENDER | **COMPLETED** |
| [4.3] | AEGIS FILETREE | **COMPLETED** |
| [4.4] | AEGIS CENTRALIZED UPLINK | **COMPLETED** |
| [4.5] | AEGIS HARDENING | **COMPLETED** |
| [4.6] | AEGIS CHRONOS | **CANCELLED** |
| [4.7] | AEGIS BLUEPRINT | **COMPLETED** |
| [4.8] | AEGIS GUARD | **CANCELLED** |
| [4.9] | AEGIS STABILITY | **COMPLETED** |
| [4.10] | AEGIS IDENTITY | **COMPLETED** |
| [5.0] | AEGIS COMMS | **COMPLETED** |
| [5.1] | AEGIS GROUPS & ADMIN | **COMPLETED** |
| [5.2] | AEGIS GROUP_SPACE | **COMPLETED** |
| [5.3] | AEGIS TEST SUITE | **COMPLETED** |
| [5.4] | AEGIS REFACTOR STRUTTURALE | **COMPLETED** |

---

*SC-ARCHIVE Operational Log // Aegis Stack v5.11.0 — DEPLOYMENT_ACTIVE.*
