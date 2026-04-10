# AEGIS ROADMAP: Direttive 4.x // "Aegis Command Station"

Questo documento delinea la strategia di espansione per la stazione operativa **SC-ARCHIVE**.

---

### [4.0] - AEGIS ORACLE (Active Deployment // Phase 1) [COMPLETED]
**Obiettivo**: Dotare la stazione di uno strato di intelligenza neurale locale per massimizzare la velocità di produzione.
- **Modello Operativo Primario**: `qwen2.5-coder:7b` (via Ollama locale). Ottimizzato per generazione strutturata e aderenza sintattica a Markdown/Mermaid.
- **Specifiche Hardware Base**: Compatibilità certificata per Full GPU Offload su architettura Pascal (es. Nvidia GTX 1070 Ti 8GB VRAM) con 16GB RAM di sistema.
- **Neural Completion**: Autocompletamento tecnico in-editor.
  > *Nota Architetturale*: Implementare un *debounce* (es. 500-800ms) sul trigger JS per compensare il Time-To-First-Token su GPU prive di Tensor Cores, scongiurando il flood di richieste asincrone.
- **Mermaid Synthesis**: Traduzione istantanea asincrona di direttive testuali in grafici interattivi (~20-30 token/s su 1070 Ti).
- **Auto-Summarization**: Processamento in background e riepilogo contestuale dei documenti visualizzati nella Dashboard.

---

### [4.1] - AEGIS REFACTOR (SOLID Compliance & UI Refinement) [COMPLETED]
**Obiettivo**: Eliminare le violazioni SOLID e perfezionare l'ergonomia visiva della stazione per un workflow industriale fluido.
- **SRP Implementation**: Scomposizione di `logic/files.py` in kernel specializzati.
- **Persistent Clients**: Implementati client dedicati con lifecycle gestito per Gotenberg e Oracle.
- **DIP Architecture**: Transizione verso interfacce iniettabili e gestione centralizzata dei client HTTP.
- **Aegis UI Refinement**: Normalizzazione dei tooltip (DaisyUI), raggruppamento logico della toolbar editoriale e implementazione della **Configurazione Uplink** globale per preferenze persistite (PDF Branding, Neural Link).

---

### [4.2] - AEGIS RENDER (Mermaid Image Export) [COMPLETED]
**Obiettivo**: Estrazione e export dei diagrammi Mermaid come immagini standalone dal documento.
- **PNG Export**: Rendering lato server del codice Mermaid in PNG tramite Gotenberg (screenshot headless Chromium).
- **Bulk Extract**: Estrazione di tutti i blocchi Mermaid presenti nel documento in un archivio `.zip`.
- **Toolbar Integration**: Azioni `aegis-render` e `aegis-render-all` integrate nella toolbar EasyMDE.
- **File Grid Actions**: Bottoni export ZIP Mermaid visibili direttamente nella griglia file per ogni `.md`.

---

### [4.3] - AEGIS FILETREE (Sidebar Albero Directory nell'Editor) [COMPLETED]
**Obiettivo**: Sidebar collassabile nell'editor che mostra l'albero completo della root selezionata, con navigazione lazy e highlight del file attivo. Esclusiva della view editor — nessun impatto su dashboard o file browser.
- **Lazy expand**: le cartelle caricano i figli solo al click — nessun render ricorsivo totale. ✓
- **Navigazione**: click su `.md` carica il file nell'editor; altri formati si aprono in nuova scheda. ✓
- **Toggle collassabile**: stato persistito in `localStorage`, bottone `«` / `»`. ✓
- **Fullscreen safe**: la sidebar è sorella del container editor, non genitore — nessun conflitto con i fix fullscreen esistenti. ✓
- **Highlight file attivo**: il documento aperto è evidenziato nell'albero. ✓
- **State persistence navigazione**: path espansi ripristinati via `htmx:afterSettle`. ✓
- **Palette coerente**: icone e colori identici al file browser (neon-text, red-400, amber-400). Icone SVG outline con transizione chiusa/aperta. ✓

---

### [4.4] - AEGIS CENTRALIZED UPLINK (Centralized Settings & Industrial UI) [COMPLETED]
**Obiettivo**: Consolidamento della configurazione e standardizzazione estetica totale.
- **Settings Manager**: Transizione da variabili ENV a `config/settings.json` persistente. ✓
- **Industrial Form Standard**: Unificazione globale dello stile input/select via `base.html` (12px, borderless, mono). ✓
- **Neural Filtering**: Esclusione automatica modelli di embedding dai selettori operativi. ✓
- **Reactive Dashboard**: Refresh automatico telemetria e stato servizi via HTMX. ✓

---

### [4.5] - AEGIS HARDENING (SOLID & CSP Compliance) [COMPLETED]
**Obiettivo**: Conformità architetturale SOLID su tutto il codebase Python e CSP compliance per penetration test.
- **SOLID full-stack**: Protocol types, DI constructor, mutation hook registry, async I/O su tutti i moduli. ✓
- **CSP Ready**: eliminati tutti gli `style=` inline da template e route. `style-src 'self'` senza `unsafe-inline`. ✓
- **CSS extraction**: `editor-aegis.css`, `pdf-industrial.css`, `pdf-preview.css` come file statici dedicati. ✓
- **Package restructure**: `config/` promosso a package Python, `logic/__init__.py` aggiunto. ✓

---

### [4.6] - AEGIS CHRONOS (Versionamento Narrativo) [CANCELLED]
**Obiettivo originale**: Strato di versionamento leggero integrato nell'editor per archivi narrativi.
> **Rimosso dalla roadmap attiva.** Il versionamento è già gestito dall'utente via Git nel terminale. Integrare un frontend Git in SC-ARCHIVE aggiungerebbe complessità significativa (subprocess, gestione conflitti, credenziali remote) per funzionalità che un terminale gestisce meglio e con più controllo. SC-ARCHIVE non è un IDE.

---

### [4.7] - AEGIS BLUEPRINT (Technical Templating) [COMPLETED]
**Obiettivo**: Standardizzazione della produzione documentale industriale con libreria template app-wide.
- **Galleria Blueprint**: Modal in toolbar editor (`BLUEPRINT_ARCHIVE`) — blueprint raggruppati per categoria. Click inserisce il contenuto in fondo al buffer editor (separatore `---` se non vuoto). ✓
- **Admin management**: Tab `BLUEPRINT_ARCHIVE` nel pannello SYS_ADMIN — form crea/sovrascrive blueprint, lista con PURGE per eliminazione. ✓
- **5 template iniziali**: `blueprints/narrative/` — Session Log, NPC Profile, Planet Description, Ship Description, Location Description. ✓
- **Path sanitization**: `BlueprintManager._sanitize()` previene traversal fuori da `blueprints/`. ✓

---

### [4.8] - AEGIS GUARD (Local Security Protocol) [CANCELLED]
**Obiettivo originale**: Blindatura dei dati locali e gestione dell'accesso in rete.
> **Rimosso dalla roadmap attiva.** La cifratura at-rest è incompatibile con il workflow reale di SC-ARCHIVE: i file `.md` sono tracciati su repository Git remoti (GitHub), accessibili da editor esterni e potenzialmente condivisi con altri giocatori. Cifrare i file renderebbe i diff illeggibili, bloccherebbe qualsiasi editor esterno e trasformerebbe SC-ARCHIVE in un lock-in obbligatorio — contrario agli obiettivi del progetto. La Network Gateway UI è out-of-scope per un'applicazione applicativo-layer.

---

### [4.9] - AEGIS STABILITY (System Integrity) [COMPLETED]
**Obiettivo**: Rafforzamento della robustezza del codice e della diagnostica in tempo reale.
- **Centralized Exception Handling**: Gerarchia `AegisError` in `logic/exceptions.py` con `status_code` integrato. Business logic completamente disaccoppiata da FastAPI — nessun `HTTPException` nei moduli `logic/`. ✓
- **Global FastAPI Handler**: `@app.exception_handler(AegisError)` in `main.py` traduce ogni eccezione di dominio in `JSONResponse` con logging strutturato. ✓
- **Domain Exception Migration**: Tutti i `raise HTTPException` nei moduli `logic/` rimpiazzati con eccezioni tipizzate (`AccessDeniedError`, `NotFoundError`, `ConversionError`, `OracleError`, `RenderError`, ecc.). ✓

---

### [4.10] - AEGIS IDENTITY (Multi-User Auth & Workspace Isolation) [COMPLETED]
**Obiettivo**: Accesso autenticato stile JupyterHub — ogni utente ha la propria sessione e workspace isolato (cartella home).
- **Login page**: `templates/layouts/login.html` standalone con tema industriale Aegis. Redirect automatico se sessione non attiva. ✓
- **Session middleware**: `SessionMiddleware` (starlette/itsdangerous) — cookie firmato. `auth_middleware` HTTP middleware verifica la sessione e blocca ogni path non-pubblico. ✓
- **Password storage**: `~/.config/sc-archive/users.json` con hash `bcrypt` (cost 12). Nessuna dipendenza da database esterno. ✓
- **Per-user workspace**: ogni utente mappato a cartella dedicata (`~/sc-archive/<username>/`). `ContextVar[Path]` in `logic/files.py` — isolamento per-request senza refactoring delle firme. ✓
- **Session isolation**: `_REQUEST_ROOT` ContextVar keyed per async context — nessuna contaminazione tra sessioni concorrenti. ✓
- **AuthService + UserStore**: separazione SOLID — `UserStore` gestisce persistenza, `AuthService` espone API di business. ✓
- **Logout**: `POST /logout` con invalidazione cookie e redirect a `/login`. ✓
- **Admin bootstrap**: primo avvio crea `admin/admin` se `users.json` è vuoto. Sovrascrivibile via `AEGIS_ADMIN_PASSWORD` env var. ✓
- **OPERATOR_ACCESS_KEY**: cambio password autenticato dalla Settings modal (`POST /auth/password`). ✓
- **Root Picker persistente**: root selezionata salvata per-utente in `users.json`. ✓
- **Navbar**: username corrente + `// LOGOUT` in ogni pagina autenticata. ✓
- **CLI**: `bin/create_user.sh <username> <password>` per provisioning operatori. ✓

---

### [5.0] - AEGIS COMMS (Sistema di Messaggistica Multi-Utente) [COMPLETED]
**Obiettivo**: Canale di comunicazione sicuro tra utenti e admin (GM/Referee). Filesystem-based, nessun database.
- **Struttura cartelle**: `comms/{inbound,outbound,staging}/` nella root di ogni utente (`~/sc-archive/{user}/comms/`). Auto-creazione alla registrazione utente. ✓
- **Formato messaggi**: file `.md` con frontmatter (id, from, to, subject, timestamp, read). Parsing stdlib `re` — nessuna dipendenza aggiuntiva. ✓
- **Flusso invio**: dual-write — copia in `outbound/` del sender + copia in `inbound/` del recipient. Cross-workspace write con path assoluti validati. ✓
- **Broadcast GM**: admin bypassa il filtro gruppi e può trasmettere a tutti gli utenti. Una copia per utente in `inbound/` (tracking read/unread indipendente). ✓
- **Draft management**: bozze in `staging/` — editabili, promuovibili a trasmissione con un click. ✓
- **Unread badge**: contatore nella navbar, HTMX-polled ogni 30s (`GET /comms/unread-count`). ✓
- **UI**: hub tabbato (RECEPTION_ARRAY / OUTBOUND_LOG / STAGING_BUFFER), modale composizione con preview Markdown live, reader con `render_md`, azioni inline (PURGE / RESPOND). ✓
- **Documentazione**: `docs/aegis-comms.md`.

---

### [5.1] - AEGIS GROUPS & ADMIN PANEL [COMPLETED]
**Obiettivo**: Sistema di gruppi utente con admin panel HTMX e messaggistica ristretta per gruppo.
- **GroupStore**: persistenza `~/.config/sc-archive/groups.json`. CRUD asincrono. Blocca eliminazione se gruppo ha membri. ✓
- **UserRecord.groups**: campo `list[str]` con retrocompatibilità (`groups: []` per utenti senza campo). ✓
- **Admin promozione via gruppo**: chiunque abbia il gruppo `"admin"` ha privilegi admin — non hardcoded su username. `require_admin` FastAPI dependency. ✓
- **Admin panel** (`/admin`): CRUD completo utenti (crea, modifica gruppi, elimina) e gruppi (crea, elimina se vuoto). Tab CREW_REGISTRY / FACTION_INDEX. ✓
- **Nav link SYS_ADMIN**: visibile in `base.html` solo se `request.session["is_admin"]`. ✓
- **Messaggistica filtrata**: `CommsManager.allowed_recipients()` — admin vede tutti; utenti normali raggiungono chi condivide almeno un gruppo o ha gruppo `"admin"`. ✓
- **Documentazione**: `docs/groups-admin-panel.md`.

---

### [5.2] - AEGIS GROUP_SPACE (Workspace Condiviso per Gruppo) [COMPLETED]
**Obiettivo**: Filesystem condiviso per i membri di un gruppo con modello permessi asimmetrico.
- **Workspace per gruppo**: `~/sc-archive/{group_name}/` creato automaticamente alla creazione del gruppo. Boot migration per gruppi preesistenti. ✓
- **Modello permessi**: root del gruppo — admin R+W, membri R; `shared/` — membri R+W, admin R. Enforced in `logic/groupspace.py`. ✓
- **GROUP_SPACE hub**: link in navbar, lista gruppi accessibili all'utente corrente. ✓
- **Browser**: navigazione file nel workspace di gruppo con indicatore `READ_ONLY` / `READ_WRITE`. ✓
- **Editor**: visualizzazione e modifica file. Textarea `readonly` e toolbar ridotta (no save) se area in sola lettura. ✓
- **CRUD file**: crea, elimina file — bloccato se l'utente non ha permessi di scrittura nella directory corrente. ✓
- **Path sanitization**: `GroupSpaceManager.sanitize()` previene traversal fuori da `~/sc-archive/{group_name}/`. ✓
- **Accesso revoca immediata**: accesso verificato a ogni request da `GroupSpaceAccess.has_access()`. ✓

---

### [5.3] - AEGIS TEST SUITE [COMPLETED]
**Obiettivo**: Copertura pytest completa per il layer `logic/` con isolamento filesystem e compatibilità cross-backend anyio.
- **170 test, 0 fallimenti**. Eseguiti su entrambi i backend anyio (`asyncio` e `trio`). ✓
- **Unit test** (`test_auth.py`, `test_comms.py`, `test_groupspace.py`, `test_blueprints.py`): 60 test su classi pure — nessun I/O, nessuna rete. ✓
- **Async I/O test** (`test_*_async.py`): 110 test su operazioni filesystem tramite fixture `tmp_path` + `monkeypatch`. ✓
- **Isolamento**: `patch_groupspace_base`, `patch_blueprints_root`, `patch_comms_base` — ogni test usa directory isolata, nessuna scrittura sul filesystem reale. ✓
- **Copertura**: `blueprints.py` 100%, `comms.py` 93%, `groupspace.py` 92%. I moduli `conversion`, `oracle`, `render` richiedono servizi esterni — esclusi dalla suite unit. ✓

---

### [5.4] - AEGIS REFACTOR STRUTTURALE [COMPLETED]
**Obiettivo**: Riorganizzazione struttura progetto, completamento funzionalità blueprint, standardizzazione modali.
- **`logic/templates.py` → `config/templates.py`**: Configurazione Jinja2 spostata fuori dal layer business logic. ✓
- **`routes/auth.py` → `routes/login.py`**: Rinominato per evitare ambiguità con `logic/auth.py`. ✓
- **Blueprint edit da admin**: form crea/sovrascrive con select categoria + input nuova categoria + bottone EDIT per caricare blueprint esistente. ✓
- **Blueprint da groupspace editor**: bottone `BLUEPRINT_ARCHIVE` nella toolbar; `insertBlueprint()` usa `window.aegisEditor` o fallback textarea. ✓
- **Standardizzazione modali**: tutte le 10 modali refactorate allo stile `blueprint_modal.html` — shell uniforme, header `// TITLE`, footer `ABORT //` + azione primaria. ✓
- **`bin/aegis-migrate.sh`**: export/import completo (settings, users, groups, blueprints, workspace) in `.tar.gz` con rimappatura percorsi interattiva. ✓

---

### [5.5] - AEGIS BLUEPRINT VARIABLE INJECTION [PENDING]
**Obiettivo**: Pre-compilazione guidata dei placeholder nei blueprint prima dell'inserimento nell'editor.

I template attuali contengono placeholder nel formato `[NOME]`, `[ANNO.DIA]`, `[SISTEMA / PIANETA]`, ecc. Oggi vengono inseriti grezzi e compilati a mano dall'utente dopo l'inserimento.

**Specifiche**:
- **Rilevamento automatico**: al click su un blueprint nella gallery modal, scansionare il contenuto per pattern `[TESTO IN MAIUSCOLO / CON SPAZI]` (regex: `\[[A-Z0-9 _/\.]+\]`).
- **Form modale**: se presenti placeholder, mostrare un secondo modal con un campo input per ciascuno (label = nome del placeholder, es. "NUMERO", "ANNO.DIA").
- **Sostituzione**: al submit del form, sostituire tutti i placeholder con i valori inseriti, poi iniettare il testo risultante nell'editor (stessa logica di `insertBlueprint()`).
- **Bypass diretto**: se nessun placeholder rilevato, inserimento immediato senza step aggiuntivi (comportamento attuale preservato).
- **Placeholder duplicati**: se lo stesso placeholder appare più volte, un solo campo nel form — sostituzione globale.

**File coinvolti**:
- `templates/components/blueprint_modal.html` — logica JS di rilevamento + apertura form
- `templates/components/blueprint_variable_modal.html` — nuovo fragment modale con form dinamico
- `routes/blueprint.py` — eventuale endpoint `GET /blueprints/placeholders?path=` per estrazione server-side

---

**(I flussi operativi futuri sono stati ricalibrati. Aegis Oracle promosso a priorità assoluta [4.0] del ciclo operativo corrente.)**
