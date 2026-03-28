# Stato del Progetto: SC-ARCHIVE
**Stato Attuale**: Op_Ready / Versione 5.3.0
**Ultimo Aggiornamento**: 28 Marzo 2026

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
logic/          __init__.py + files.py, conversion.py, oracle.py, render.py, templates.py
routes/         __init__.py (build_breadcrumbs) + core, archive, editor, pdf, config, oracle
config/         __init__.py + settings.py (SettingsManager) + settings.json
static/css/     output.css, editor-aegis.css, pdf-industrial.css, pdf-preview.css, main.css
```

---

## 3. Roadmap Prossimi Cicli

| Fase | Codice | Stato | Obiettivo |
|---|---|---|---|
| [4.3] | AEGIS FILETREE | **COMPLETED** | Sidebar albero directory lazy nell'editor |
| [4.4] | AEGIS CHRONOS | Planned | Versionamento narrativo Git opt-in (diff, snapshot, inject) |
| [4.5] | AEGIS BLUEPRINT | Planned | Template gallery + Variable Injection |
| [4.6] | AEGIS MULTI-LINK | Planned | Tabbed Workspace + Split Pane |
| [4.7] | AEGIS GUARD | Planned | Buffer Encryption + Network Gateway UI |
| [4.8] | AEGIS STABILITY | Planned | Centralized Exception Handling |

---

*SC-ARCHIVE Operational Log // Aegis Stack v5.3.0 — DEPLOYMENT_ACTIVE.*
