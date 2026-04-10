# Analisi Tecnica: SC-ARCHIVE

- **Progetto**: Space Craft Archive Management System (FastAPI + HTMX)
- **Nome Tecnico Interno**: MD2FastPDF
- **Data**: 10 Aprile 2026
- **Versione**: 5.12.0

## 1. Architettura di Sistema

L'applicazione segue un modello asincrono basato su FastAPI con isolamento per-request tramite `ContextVar`. Ogni utente autenticato opera su un workspace filesystem dedicato; lo stato di sessione è gestito server-side tramite cookie firmato (`SessionMiddleware`).

### 1.1 Persistenza e Configurazione (`config/settings.py`)

- **JSON Store**: `config/settings.json` sorgente unica di verità per parametri operativi.
- **SettingsManager**: `get()`, `set()` async, `batch_update()` (singola scrittura disco), `_save_sync()` solo per startup.
- **Dynamic Uplink**: coordinate dei servizi (Ollama, Gotenberg), modelli IA e flag persistiti — modificabili a runtime senza restart.
- **Aggiornamento Reattivo**: trigger HTMX (`settings-updated`) per sincronizzazione dashboard post-modifica.

### 1.2 Backend (Python / FastAPI)

- **FastAPI**: routing, middleware stack, dependency injection via `Depends`.
- **Middleware stack** (outer → inner): `SessionMiddleware` → `auth_middleware` (custom HTTP middleware).
  - `auth_middleware`: verifica sessione, blocca path non pubblici, binda `_REQUEST_ROOT` ContextVar per la request corrente. HTMX-aware: emette `HX-Redirect` per richieste headless.
- **Asincronia**: `asyncio` + `anyio` per I/O filesystem; `httpx.AsyncClient` per Gotenberg e Ollama.
- **Jinja2**: rendering server-side con filtro custom `parent_path`.
- **SOLID Compliance**: Protocol-based abstractions in `conversion.py`; mutation hook registry in `files.py`; DI via constructor in `oracle.py` e `GotenbergClient`; `UserStoreProtocol` + `SyncUserStoreProtocol` (ISP split) runtime-checkable in `auth.py`.

### 1.3 Frontend (HTMX / Tailwind)

- **HTMX**: aggiornamento parziale del DOM. Ogni risposta è un fragment Jinja2 se `HX-Request` è presente, full-page altrimenti.
- **Tailwind CSS v4**: design "Glassmorphism" industriale con palette Slate/Zinc e accento Neon Cyan (`#7dd3fc`).
- **EasyMDE/CodeMirror**: editor Markdown con Fullscreen, Side-by-Side, toolbar estesa.
- **CSP Ready**: nessun attributo `style=` inline nei template (eccetto 2 valori CSS dinamici Jinja2). CSS estratti in file statici dedicati.

### 1.4 Generazione PDF (Gotenberg)

- **Pipeline**: MD → HTML (sanitizzato via `bleach`) → PDF via Gotenberg (Chromium Engine).
- **Protocol classes**: `PageScaffolding` (Protocol), `DetailedScaffolding`, `MinimalScaffolding`, `MarkdownRenderer`, `PdfHtmlBuilder` — tutti iniettabili in `GotenbergClient`.
- **Industrial CSS**: `static/css/pdf-industrial.css` caricato una volta a module init — zero CSS inline nel codice Python.
- **HUD Tipografico**: testate e piè di pagina con paginazione dinamica (`{{pageNumber}}` / `{{totalPages}}`).
- **Nota**: header/footer inviati a Gotenberg contengono `style=` inline strutturali — Gotenberg opera in sandbox senza accesso ai file statici dell'app.

### 1.5 Autenticazione e Workspace Isolation (`logic/auth.py`)

- **SessionMiddleware**: cookie firmato con `AEGIS_SECRET_KEY` (24h TTL). Outer layer nel middleware stack. `AEGIS_SECRET_KEY` è **obbligatorio**: `bin/launch.sh` lo genera e persiste in `~/.config/sc-archive/session.key` via `openssl rand -hex 32` (eseguito solo al primo avvio).
- **auth_middleware**: HTTP middleware inner — legge `request.session["username"]`, recupera root utente da `UserStore`, binda `PathSanitizer._REQUEST_ROOT` via `ContextVar`. Cattura solo `AegisError` — errori di programmazione non vengono inghiottiti.
- **UserStore**: persistenza `~/.config/sc-archive/users.json`. Hashing `bcrypt` (cost 12). API async-first; sync variants solo per bootstrap. Metodi aggiunti: `list_users()`, `update_groups()`, `delete_user()`. Migrazione automatica a module-load: `_migrate_legacy_users()` sposta `config/users.json` → `~/.config/sc-archive/users.json` con merge (record legacy vincono su bootstrap placeholder).
- **GroupStore**: persistenza `~/.config/sc-archive/groups.json`. CRUD gruppi asincrono. `delete_group()` riceve `UserStore` come parametro (DIP) — blocca se il gruppo ha utenti assegnati.
- **AuthService**: business logic (authenticate, create_user, change_password, update_user_root, get_user, update_user_groups, delete_user, list_users). Dipende da `UserStoreProtocol` (async) + `SyncUserStoreProtocol` (bootstrap/CLI) + `SyncGroupStoreProtocol` — ISP split per non esporre path sync agli consumer async. Side-effect di creazione utente delegati a hook registry (`register_user_creation_hook`, `register_user_creation_sync_hook`) — nessuna dipendenza diretta su CommsManager (SRP).
- **UserRecord**: campi `__slots__` — `username`, `password_hash`, `root`, `groups: list[str]`. Retrocompatibilità: utenti senza `groups` in JSON letti con `groups=[]`.
- **Per-user workspace**: tutti gli utenti → `Path.home() / "sc-archive" / username`. Calcolato a runtime — nessun path hardcoded, funziona cross-PC. Root persistita per-utente in `users.json`.
- **Admin bootstrap**: primo avvio crea `admin` con `groups=["admin"]` se `users.json` è vuoto. Crea il gruppo `"admin"` in `GroupStore`. Sovrascrivibile via `AEGIS_ADMIN_PASSWORD`.
- **require_admin** (`routes/deps.py`): FastAPI dependency — verifica `"admin" in record.groups`, altrimenti HTTP 403. `POST /login` setta `request.session["is_admin"]`.
- **ContextVar isolation**: `_REQUEST_ROOT` in `logic/files.py` — nessuna contaminazione tra sessioni concorrenti in asyncio.

---

## 2. Struttura dei Package

### 2.1 `logic/` — Business Logic

| Modulo | Classi principali | Responsabilità |
| -------- | ------------------- | ---------------- |
| `files.py` | `PathSanitizer`, `FileManager`, `DirectoryLister`, `StorageCache` | Filesystem I/O, path security, cache stats |
| `conversion.py` | `GotenbergClient`, `MarkdownRenderer`, `PdfHtmlBuilder`, `DetailedScaffolding`, `MinimalScaffolding` | Pipeline MD→PDF via Gotenberg |
| `oracle.py` | `OracleClient`, `PromptTemplates` | Integrazione Ollama (completion, synthesis, summarize) |
| `render.py` | funzioni `render_mermaid_png`, `render_mermaid_zip` | Export PNG/ZIP Mermaid via Gotenberg screenshot |
| `auth.py` | `AuthService`, `UserStore`, `GroupStore`, `UserRecord`, `UserStoreProtocol`, `SyncUserStoreProtocol`, `GroupStoreProtocol`, `SyncGroupStoreProtocol` | Multi-user auth, workspace isolation, group management, user creation hook registry, legacy migration |
| `comms.py` | `FrontmatterParser`, `MessageRecord`, `CommsManager` | Messaggistica filesystem-based, dual-write, draft, filtraggio gruppi |
| `blueprints.py` | `BlueprintManager` | Libreria template Markdown app-wide in `blueprints/`; path sanitization propria |
| `groupspace.py` | `GroupSpaceAccess`, `GroupSpaceManager` | Workspace condivisi per gruppo; modello permessi (root: admin R+W / membri R; shared/: membri R+W / admin R) |
| `templates.py` | `templates` (Jinja2Templates) | Configurazione motore template + filtri custom (`render_md`, `parent_path`) |
| `exceptions.py` | `AegisError` e sottoclassi | Gerarchia eccezioni dominio (zero `HTTPException` in `logic/`) |

**Gerarchia eccezioni** (`logic/exceptions.py`):

```text
AegisError
  ├── AccessDeniedError      (403)
  ├── NotFoundError          (404)
  ├── InvalidPathError       (400)
  ├── InvalidFileTypeError   (400)
  ├── FileConflictError      (400)
  ├── FilenameRequiredError  (400)
  ├── AuthError              (401)
  ├── ConversionError        (502)
  ├── OracleError            (502)
  ├── RenderError            (502)
  ├── CommsError             (400)
  └── GroupError             (400)
```

`@app.exception_handler(AegisError)` in `main.py` traduce ogni eccezione in `JSONResponse` con logging strutturato.

### 2.2 `routes/` — API Routers

| Modulo | Prefix | Responsabilità |
| -------- | -------- | ---------------- |
| `core.py` | `/` | Dashboard, stats, services health |
| `auth.py` | `/` | Login, logout, cambio password |
| `archive.py` | `/` | File CRUD, search, tree navigation |
| `editor.py` | `/` | Editor view, save |
| `pdf.py` | `/` | PDF conversion, preview, download |
| `config.py` | `/` | Root picker, workspace selection |
| `oracle.py` | `/api/oracle` | Completion SSE, Mermaid synthesis, summarize |
| `render.py` | `/render` | Mermaid PNG/ZIP export |
| `settings.py` | `/` | Settings UI, model management |
| `comms.py` | `/comms` | Hub messaggistica, compose, send, draft, unread badge |
| `admin.py` | `/admin` | Admin panel — CRUD utenti, gruppi, blueprint (require_admin) |
| `blueprint.py` | `/blueprints` | Gallery template (tutti gli utenti), CRUD admin-only |
| `groupspace.py` | `/group-space` | Hub gruppi, browser, editor, save, create, delete per workspace condivisi |
| `deps.py` | — | `get_current_user`, `require_admin` dependencies condivise |
| `__init__.py` | — | `build_breadcrumbs()` utility condivisa |

### 2.3 `config/` — Configuration Package

- `settings.py`: `SettingsManager` + istanza globale `settings`.
- `settings.json`: store persistente (Ollama IP, Gotenberg IP, modelli, flags).
- `~/.config/sc-archive/users.json`: credenziali utenti + workspace root + gruppi per-utente.
- `~/.config/sc-archive/groups.json`: registry gruppi disponibili (`group_name → {}`). Gestito da `GroupStore`.
- `~/sc-archive/{group_name}/`: workspace filesystem per ogni gruppo. Creato automaticamente da `GroupStore.create_group()`. Contiene `shared/` (R+W membri) e root (R+W admin, R membri).
- `blueprints/{category}/`: template Markdown app-wide. `BlueprintManager` usa root propria separata dal workspace utente.

### 2.4 `static/css/` — Design System

| File | Scopo |
| ------ | ------- |
| `output.css` | Tailwind v4 compiled output |
| `editor-aegis.css` | Stili EasyMDE, fullscreen fix, layout editor, filetree sidebar |
| `pdf-industrial.css` | Stylesheet documento PDF (inviato a Gotenberg) |
| `pdf-preview.css` | Tooltip override, iframe, overflow viewer PDF |
| `main.css` | Utility classes globali, variabili CSS custom |

### 2.5 `templates/`

```text
layouts/
  base.html       — scaffold HTML completo (nav, sidebar, modal container, toast container)
  login.html      — pagina login standalone
shell.html        — wrapper minimo per component_template pattern
components/       — 40 fragment Jinja2 HTMX (incl. 8 comms, 5 admin, 2 blueprint, 4 groupspace)
icons/            — SVG inline components
```

---

## 3. Sicurezza

| Livello | Meccanismo |
| --------- | ----------- |
| Autenticazione | SessionMiddleware + bcrypt (cost 12) |
| Autorizzazione | `auth_middleware` per path non-pubblici; `require_admin` dependency per `/admin` |
| Admin promozione | Chiunque abbia `"admin"` in `UserRecord.groups` è admin — non hardcoded su username |
| Workspace isolation | `ContextVar[Path]` per-request — impossibile accedere al workspace di un altro utente |
| Path traversal | `PathSanitizer.resolve_and_sanitize()` — blocca `../`, path nascosti, symlink escape |
| COMMS cross-write | Path assoluti costruiti da `Path.home() / "sc-archive" / username`; security assertion: path deve essere sotto `Path.home()` |
| GROUP_SPACE isolation | `GroupSpaceManager._sanitize()` — ogni path risolto contro `{workspace_base}/{group_name}/`; traversal bloccato |
| GROUP_SPACE permessi | `GroupSpaceAccess.can_write()` — admin: R+W in root, R in `shared/`; membri: R in root, R+W in `shared/` |
| XSS | `bleach.Cleaner` whitelist su ogni pipeline MD→HTML e corpo messaggio COMMS |
| CSP | Zero `style=` inline (eccetto 2 valori dinamici Jinja2) — `style-src 'self'` applicabile |

---

## 4. Lifespan e Servizi Esterni

`main.py` usa un async context manager `@asynccontextmanager` come `lifespan`:

- **Startup**: bootstrap admin, registrazione mutation hook cache, probe Ollama, provisioning workspace gruppi esistenti (`GroupStore.provision_group_dirs_sync` per ogni gruppo in `groups.json`).
- **Shutdown**: `gotenberg.shutdown()`, `oracle.shutdown()` — chiusura `httpx.AsyncClient`.

| Servizio | Protocollo | Uso |
| ---------- | ----------- | ----- |
| Gotenberg | HTTP POST multipart | PDF rendering, Mermaid PNG/ZIP |
| Ollama | HTTP POST JSON / SSE | Completion, Mermaid synthesis, summarize |
| Tailwind CLI | Processo esterno | Compilazione CSS (solo development) |

---

## 5. Pattern Architetturali Chiave

- **Fragment-first HTMX**: ogni route rileva `HX-Request` e restituisce fragment o full-page. Modale pattern: `hx-target="#modal-container"`. Tab/panel: `hx-target="#aegis-view-core"`.
- **ContextVar per request isolation**: `_REQUEST_ROOT` in `logic/files.py` — bindata da `auth_middleware` prima che la route venga eseguita. Nessun parametro `root` propagato esplicitamente.
- **Protocol-based DI**: `RendererProtocol`, `HtmlBuilderProtocol`, `PageScaffolding`, `UserStoreProtocol` — tutte le dipendenze critiche sono Protocol, non classi concrete.
- **Mutation hook registry**: `StorageCache` si invalida via hook registrato da `main.py` — nessuna dipendenza inversa da `files.py` verso la cache.
- **Atomic file write**: write su `.tmp` → `rename()` — nessuna lettura parziale possibile.

---

## 6. Test Suite (v5.9.1)

### 6.1 Struttura

```text
tests/
  conftest.py              — fixture condivise (tmp_workspace, patch_*_base)
  test_auth.py             — UserRecord, UserStore._build_record
  test_blueprints.py       — BlueprintManager._sanitize, _display_name, group_by_category
  test_groupspace.py       — GroupSpaceAccess, GroupSpaceManager.sanitize
  test_comms.py            — FrontmatterParser, MessageRecord, CommsManager (metodi puri)
  test_blueprints_async.py — BlueprintManager async I/O (list, read, write, delete)
  test_groupspace_async.py — GroupSpaceManager async I/O (list_contents, read/write/create/delete_file)
  test_comms_async.py      — CommsManager async I/O (send, mark_read, delete, draft, promote)
```

### 6.2 Strategia di Isolamento

- **Fixture `patch_*_base`**: `monkeypatch.setattr` sostituisce il modulo-level `_workspace_base()` (o `BLUEPRINTS_ROOT`) con un `tmp_path` isolato per test. Nessun side-effect sul filesystem reale.
- **Backend anyio**: ogni test `@pytest.mark.anyio` viene eseguito due volte — con `asyncio` e con `trio` — garantendo compatibilità cross-backend dell'I/O asincrono.
- **Test puri vs async**: classi e metodi statici testati senza I/O (rapidi, deterministici); operazioni async testate con filesystem reale in-memory via `tmp_path`.

### 6.3 Copertura

| Modulo | Copertura | Note |
| --- | --- | --- |
| `blueprints.py` | 100% | Incluse list, read, write, delete |
| `comms.py` | 93% | Escluse righe IOError/OSError impossibili da triggerare |
| `groupspace.py` | 92% | Escluse righe settings-fallback e branch IOError |
| `auth.py` | 38% | Solo `UserRecord` e `UserStore._build_record` — `AuthService` richiede bcrypt/filesystem reale |
| `conversion.py` | 0% | Richiede Gotenberg attivo |
| `oracle.py` | 0% | Richiede Ollama attivo |
| `render.py` | 0% | Richiede Gotenberg attivo |

### 6.4 Esecuzione

```bash
poetry run pytest                                        # suite completa
poetry run pytest --cov=logic --cov-report=term-missing # con coverage
poetry run pytest tests/test_comms_async.py -v          # singolo file
```

---

Documento Tecnico Aegis Class System // v5.12.0
