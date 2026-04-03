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
- **Palette coerente**: icone e colori identici al file browser (neon-text, red-400, amber-400). ✓
- **Piano dettagliato**: `docs/piano-aegis-filetree.md`.

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

### [5.0] - AEGIS COMMS (Sistema di Messaggistica Multi-Utente) [COMPLETED]
**Obiettivo**: Canale di comunicazione sicuro tra utenti e admin (GM/Referee). Filesystem-based, nessun database.
- **Struttura cartelle**: `comms/{inbound,outbound,staging}/` nella root di ogni utente (admin: `~/comms/`, utenti: `~/sc-archive/{user}/comms/`). Auto-creazione alla registrazione utente. ✓
- **Formato messaggi**: file `.md` con frontmatter (id, from, to, subject, timestamp, read). Parsing stdlib `re` — nessuna dipendenza aggiuntiva. ✓
- **Flusso invio**: dual-write — copia in `outbound/` del sender + copia in `inbound/` del recipient. Cross-workspace write con path assoluti validati. ✓
- **Broadcast GM**: admin può trasmettere a tutti gli operatori raggiungibili (`to: ALL`). Una copia per utente in `inbound/` (tracking read/unread indipendente). ✓
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
- **Messaggistica filtrata**: `CommsManager.allowed_recipients()` — destinatari raggiungibili = gruppo condiviso col sender **o** gruppo `"admin"`. ✓
- **Documentazione**: `docs/groups-admin-panel.md`.

---

### [4.6] - AEGIS CHRONOS (Versionamento Narrativo) [PLANNED]
**Obiettivo**: Strato di versionamento leggero e non invasivo per archivi narrativi (scenari RPG, documentazione tecnica). Modulo **opt-in**: attivo solo se la root selezionata contiene già un repo Git. Non crea repo, non tocca remoti, non esegue mai operazioni distruttive.
- **Detect automatico**: `git rev-parse --git-dir` sulla root — se assente, pannello in stato `GIT_REPO_NOT_DETECTED` con istruzioni init.
- **Branch indicator**: visualizzazione del branch corrente nell'editor e nella dashboard.
- **Snapshot manuale**: bottone `COMMIT_SNAPSHOT` in toolbar — esegue `git add <file> && git commit` sul solo file aperto.
- **Auto-snapshot**: configurabile da Uplink Config (ogni N salvataggi o X minuti), disabilitato di default.
- **File history**: lista commit che toccano il documento aperto (`git log --oneline -- <file>`).
- **Diff viewer a due colonne**: versione storica (sx) vs versione corrente (dx), con highlighting righe modificate.
- **Inject nel buffer**: bottone per appendere un blocco della versione storica al buffer dell'editor corrente.
- **Pull safe**: `git pull --ff-only` — rifiutato se la storia è divergente, nessun merge automatico.
- **Push safe**: `git push` standard — rifiutato se il remote è ahead, mai `--force`. Credenziali delegate al SO.
- **Piano dettagliato**: `docs/piano-aegis-chronos.md`.

---

### [4.7] - AEGIS BLUEPRINT (Technical Templating) [PLANNED]
**Obiettivo**: Standardizzazione della produzione documentale industriale.
- **Galleria Blueprint**: Inserimento istantaneo di template (Missions, Tech Specs, Logs).
- **Variable Injection**: Sostituzione dinamica di segnaposto nel Markdown prima dell'export PDF.

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
- **Password storage**: `config/users.json` con hash `bcrypt` (cost 12). Nessuna dipendenza da database esterno. ✓
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

**(I flussi operativi futuri sono stati ricalibrati. Aegis Oracle promosso a priorità assoluta [4.0] del ciclo operativo corrente.)** 🚀🌑
