# Stato del Progetto: SC-ARCHIVE
**Stato Attuale**: Op_Ready / Versione 5.5.1 → 5.6.0 in pianificazione
**Ultimo Aggiornamento**: 29 Marzo 2026

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
    *   **Context Precision**: Sistema di isolamento `[CONTEXT_START]` per il Ghost-Text, eliminando la ripetizione del testo utente e garantendo la chiusura delle frasi tronche.
    *   **Surgical Sanitization**: Filtro attivo su `div` allucinati dal modello per proteggere la stabilità del layout HUD.
    *   **Protocol Feedback**: Notifiche visive immediate (`!! NEURAL_PROTOCOL_OFFLINE !!`) e banner informativi nei modali se il Neural Link è spento.
    *   **Protocol Hard-Stop**: Isolamento totale del backend; se disattivato, il sistema non effettua probe o chiamate esterne.
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
- **AuthError**: `logic/exceptions.py` — sottoclasse di `AegisError` con `status_code=401`.
- **UserStoreProtocol**: `Protocol` `@runtime_checkable` — `AuthService` dipende dall'astrazione, non dalla classe concreta (DIP). `UserStore.get()`, `save_user()`, `update_root()` completamente asincroni via `_aload()`.
- **Workspace Security**: `routes/config.py` — utenti non-admin confinati a `~/sc-archive/<username>`: `_user_allowed_base()` calcola il subtree consentito; `select_root` valida ogni selezione; `root_picker` blocca la navigazione al di sopra del workspace.

### 1.10 AEGIS COMMS — Sistema di Messaggistica [5.0] (PLANNED)
- **Struttura cartelle**: `comms/{inbound,outbound,staging}/` nella root utente. Admin: `~/comms/`. Utenti: `~/sc-archive/{user}/comms/`. Creazione automatica alla registrazione.
- **Formato**: file `.md` con frontmatter (id, from, to, subject, timestamp, read). Filename: `{timestamp}_{id8}_{slug}.md`. Parsing `re` stdlib — zero dipendenze aggiuntive.
- **Invio**: dual-write su `outbound/` sender + `inbound/` recipient. Cross-workspace write con path assoluti (bypass `PathSanitizer`) + security assertion su `Path.home()`.
- **Broadcast GM**: admin trasmette a `ALL` — copia individuale in ogni `inbound/` (read/unread per-utente indipendente).
- **Bozze**: `staging/` — editabili, promovibili a trasmissione. Draft pre-fill in compose modal.
- **Unread badge**: navbar HTMX-polled ogni 30s. Invisibile se count = 0.
- **UI**: hub tabbato (`RECEPTION_ARRAY` / `OUTBOUND_LOG` / `STAGING_BUFFER`), compose modal con recipient dropdown, message reader con Markdown renderizzato via filtro Jinja2 `render_md`.

### 1.8 UX, Sicurezza & CSP Compliance
- Transizioni `scan-in` / `soft-exit` su tutte le modali.
- Sanitizzazione path obbligatoria (prevenzione `../`), sanitizzazione Markdown (XSS via `bleach`).
- DaisyUI tooltip su tutti i controlli azione (z-index stratificato).
- **CSP Ready**: eliminati tutti gli attributi `style=` inline dai template e dagli snippet HTML generati dai route. Solo 2 eccezioni strutturali (valori dinamici Jinja2: `--w: {{ value }}%`).
- CSS estratti in file statici dedicati (`editor-aegis.css`, `pdf-industrial.css`, `pdf-preview.css`).

---

## 2. Infrastruttura Tecnica

| Componente | Tecnologia |
|---|---|
| Backend | FastAPI (Python 3.13) + anyio + httpx |
| Frontend | HTMX + Tailwind v4 (standalone CLI) + DaisyUI + Jinja2 |
| Editor | EasyMDE (CodeMirror 5) |
| PDF Engine | Gotenberg (Chromium via Docker) |
| AI Layer | Ollama locale (`qwen2.5-coder:7b`), GPU offload Pascal-class |
| Render Engine | Gotenberg screenshot headless per PNG Mermaid |
| Environment | Poetry + pyenv (Python 3.13) |

### Package Structure
```
logic/          __init__.py + files.py, conversion.py, oracle.py, render.py, templates.py, auth.py, exceptions.py
routes/         __init__.py (build_breadcrumbs) + core, archive, editor, pdf, config, oracle, auth, deps
config/         __init__.py + settings.py (SettingsManager) + settings.json + users.json
static/css/     output.css, editor-aegis.css, pdf-industrial.css, pdf-preview.css, main.css
bin/            launch.sh, create_user.sh
```

---

## 3. Roadmap Prossimi Cicli

| Fase | Codice | Stato | Obiettivo |
|---|---|---|---|
| [4.3] | AEGIS FILETREE | **COMPLETED** | Sidebar albero directory lazy nell'editor |
| [4.8] | AEGIS STABILITY | **COMPLETED** | Centralized Exception Handling (`AegisError`, `@app.exception_handler`) |
| [4.9] | AEGIS STABILITY+ | **COMPLETED** | Registrazione `@app.exception_handler(AegisError)` in `main.py` |
| [4.10] | AEGIS IDENTITY | **COMPLETED** | Multi-user auth, workspace isolation, login, logout, password change |
| [5.0] | AEGIS COMMS | **Planned — Next** | Messaggistica multi-utente, broadcast GM, draft, unread badge |
| [4.6] | AEGIS CHRONOS | Planned | Versionamento narrativo Git opt-in (diff, snapshot, inject) |
| [4.5] | AEGIS BLUEPRINT | Planned | Template gallery + Variable Injection |
| [4.7] | AEGIS GUARD | Planned | Buffer Encryption + Network Gateway UI |

---

*SC-ARCHIVE Operational Log // Aegis Stack v5.5.1 — DEPLOYMENT_ACTIVE.*
