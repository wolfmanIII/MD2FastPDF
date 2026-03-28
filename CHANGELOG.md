# CHANGELOG: SC-ARCHIVE
Tutte le modifiche degne di nota a questo progetto saranno documentate in questo file.

## [5.0.0] - AEGIS PERSISTENCE & CENTRALIZED UPLINK (2026-03-28)
Centralizzazione totale della configurazione in `config/settings.json`, rinfresco industriale della UI e telemetria dashboard ripristinata.

### Added
- **Settings Persistence**: Introduzione di `logic/settings.py` e `config/settings.json`. Tutti i parametri (Ollama IP, Gotenberg IP, Modelli IA, Flags) sono ora persistenti tra i riavvii.
- **Dashboard Telemetry**: Ripristinata la rotta `/stats` in `routes/core.py`. La dashboard ora aggiorna CPU, RAM e stato root ogni 30s.
- **Reactive Refresh**: Al salvataggio dei settings, il pannello `services-status-container` della dashboard si aggiorna via HTMX (`HX-Trigger: settings-updated`).
- **Neural Filtering**: I modelli Ollama sono ora filtrati per escludere motori di embedding (`embed`, `bge`, `nomic`, ecc.) dai menu di selezione chat/sintesi.

### Changed
- **Aegis Industrial Style**: Standardizzazione globale in `base.html` per tutti i campi `input`, `select` e `textarea`.
  - Font: `Roboto Mono` 12px.
  - Padding: `0.5rem 0.75rem`.
  - Bordi: rimossi (`border: none`) in favore di background scuri integrati.
- **Settings Modal Layout**: Riorganizzazione Gestalt del modale. Tighten label-input spacing e aumento gap inter-blocco per eliminare ambiguità visiva.
- **Uplink logic**: Migrazione di tutte le rotte e servizi all'utilizzo del `SettingsManager` invece delle variabili d'ambiente.

---

## [4.8.0] - AEGIS FILETREE (2026-03-27)
Sidebar albero directory nell'editor con navigazione lazy, persistenza stato e palette colori coerente col file browser.

### Added
- **Sidebar albero directory**: colonna sinistra collassabile nell'editor (`#aegis-filetree`, larghezza 260px) con toggle `«`/`»` persistito in `localStorage`.
- **Lazy expand**: le cartelle caricano i figli via `GET /tree/expand?path=` solo al click — nessun render ricorsivo totale.
- **Highlight file attivo**: il documento aperto è evidenziato nell'albero con bordo sinistro cyan.
- **State persistence**: path espansi salvati in `localStorage['aegis-filetree-expanded']` e ripristinati dopo ogni navigazione HTMX via `htmx:afterSettle`.
- **`GET /tree?active=`** in `routes/archive.py`: root level + active_path per la sidebar.
- **`GET /tree/expand?path=&active=`** in `routes/archive.py`: figli di una cartella.
- **`templates/components/filetree_sidebar.html`**: header `ARCHIVE_TREE` + lazy load root.
- **`templates/components/filetree_node.html`**: nodi dir/file con routing corretto per `.md`, `.pdf`, `.html`, altri.
- **`templates/icons/folder-open.html`**: SVG outline open folder (stroke only, `fill="none"`) per la transizione icona.

### Changed
- **Icone cartella**: `fa-solid fa-folder-closed` → `fa-solid fa-folder-open` al toggle espansione (via swap JS su `.folder-icon-closed`/`.folder-icon-open`).
- **Palette filetree**: allineata al file browser — dir `neon-text` + drop-shadow cyan, `.md` `neon-text`, `.pdf` icona `text-red-400`, `.html` icona `text-amber-400`, altri `text-zinc-100`.
- **Fullscreen safe**: bottone toggle sidebar nascosto con `display: none !important` durante la modalità fullscreen EasyMDE (`aegis-fullscreen-active`).

### Fixed
- **Reset albero alla navigazione**: lo stato espanso viene salvato/ripristinato via `localStorage` — la navigazione tra file non azzera l'albero.
- **Toggle sidebar in fullscreen**: il bottone `#aegis-filetree-toggle-wrap` è escluso dalla viewport fullscreen tramite CSS condizionale.

---

## [4.7.4] - ORACLE TIMEOUT HARDENING (2026-03-26)
Fix timeout e messaggi di errore Oracle per distinguere server irraggiungibile da inferenza lenta.

### Fixed
- **Oracle timeout**: `httpx.AsyncClient` ora usa timeout granulari — `connect=5s`, `read=600s`, `write=30s`, `pool=5s`. In precedenza `timeout=120.0` impostava anche il read timeout a 120s, causando `NEURAL_CORE_UNREACHABLE` su GPU lente o documenti lunghi.
- **Errore fuorviante**: `httpx.TimeoutException` catturava anche `ReadTimeout` riportandolo come `NEURAL_CORE_UNREACHABLE`. Ora separato: `ConnectError`/`ConnectTimeout` → `NEURAL_CORE_UNREACHABLE`, tutti gli altri timeout → `NEURAL_INFERENCE_TIMEOUT`.

---

## [4.7.3] - DOCS & ROADMAP UPDATE (2026-03-26)
Aggiornamento documentazione al ciclo corrente e pianificazione AEGIS CHRONOS.

### Added
- **`docs/piano-aegis-chronos.md`**: Piano dettagliato per la fase [4.3] — versionamento narrativo Git opt-in con requisiti funzionali, architettura, fasi di sviluppo e vincoli espliciti.

### Changed
- **`docs/ROADMAP.md`**: [4.3] AEGIS CHRONOS ridefinito — scope ristretto a operazioni safe (no push/pull/merge), modulo opt-in solo se repo Git già presente, aggiunto link al piano dettagliato.
- **`docs/Stato-dell-Arte.md`**: Aggiornato dalla v4.0 alla v4.7.2 — documentate tutte le funzionalità implementate nei cicli 4.1–4.7 (Render Engine, Oracle resilience, Dashboard telemetry, Uplink Config, UX).

---

## [4.7.2] - DASHBOARD LAYOUT REFINEMENT (2026-03-26)
Riorganizzazione del cockpit dashboard e separazione dei modelli Ollama per categoria.

### Changed
- **Dashboard Panel Order**: Nuovo ordine — SYSTEM_STATUS + TERMINAL_MATRIX → GOTENBERG + OLLAMA → RECENT_FRAGMENTS + STORAGE_NODE.
- **Services Status — Two Panels**: GOTENBERG e OLLAMA ora sono `glass-panel` separati affiancati invece di un unico pannello diviso internamente.
- **Ollama Model Categorization**: I modelli Ollama sono ora classificati in `CHAT_MODELS` e `EMBED_MODELS` tramite keyword matching (`embed`, `bge`, `minilm`, `e5-`, `gte-`, `rerank`).
- **Stats Grid Cleanup**: `RECENT_FRAGMENTS` e `STORAGE_NODE` rimossi da `stats_grid.html` e gestiti direttamente da `dashboard.html` per controllo esplicito dell'ordine.

---

## [4.7.1] - ORACLE RESILIENCE PATCH (2026-03-26)
Hardening del layer neurale contro timeout di connessione e supporto multi-endpoint per ambienti multi-macchina.

### Added
- **Oracle Multi-Endpoint Probe**: `OracleClient.probe_url()` testa in sequenza `localhost:11434` e `172.31.112.1:11434` all'avvio e blocca l'URL sul primo endpoint attivo (timeout 2s per probe). Sovrascrivibile via `OLLAMA_URL`.

### Fixed
- **Oracle ConnectTimeout**: `generate_syntax()` e `summarize()` ora wrappano `httpx.ConnectTimeout`, `httpx.ConnectError` e `httpx.TimeoutException` in `OracleError("NEURAL_CORE_UNREACHABLE")` invece di propagare l'eccezione non gestita fino all'ASGI layer.

---

## [4.7.0] - AEGIS RENDER & COCKPIT REFINEMENT (2026-03-26)
Completamento del modulo di export Mermaid, ottimizzazione del cockpit editoriale e introduzione del pannello di telemetria backend.

### Added
- **Aegis Render Engine**: Nuovo modulo `logic/render.py` + `routes/render.py` per l'export dei diagrammi Mermaid via Gotenberg (screenshot headless Chromium).
  - `GET /render/mermaid/png?path=&index=N` — export PNG singolo per blocco.
  - `GET /render/mermaid/bulk?path=` — download ZIP di tutti i blocchi del documento.
  - Modal lista blocchi (`mermaid_list_modal.html`) con link apertura in nuova scheda.
- **Backend Services Status Panel**: Nuovo pannello dashboard (`components/services_status.html`) con sondaggio real-time di Gotenberg (`/health`) e Ollama (`/api/tags`). Auto-refresh ogni 30s via HTMX. Mostra modelli Ollama caricati.
- **Editor Toolbar — Render Actions**: Pulsanti `aegis-render` (lista blocchi) e `aegis-render-all` (ZIP bulk) integrati nella toolbar EasyMDE dopo Neural Hint.
- **Editor Toolbar — COMMIT_STABLE e PRINT_DOCUMENT**: Spostati dall'action bar breadcrumb alla toolbar EasyMDE per coerenza operativa.
- **File Grid — Export Mermaid**: Bottone export ZIP visibile direttamente nella griglia per ogni file `.md`.

### Fixed
- **File Grid Button Visibility**: Rimosso `opacity-0 group-hover:opacity-100` — tutti i pulsanti azione ora sempre visibili con intensità uniforme al bottone Delete.
- **Input/Textarea Background**: Risolto il layer conflict DaisyUI (`.input`, `.textarea` impostano `background-color` fuori `@layer`, battono le utility Tailwind) tramite `style` inline con `rgba(0,0,0,0.4)` su tutti i campi form: search bar, create modal, rename modal, oracle modal.
- **HTMX Target Inheritance**: `services-status-container` ora dichiara esplicitamente `hx-target="this"` per prevenire l'override del `hx-target` ereditato dal `body` (`#aegis-view-core`).

### Changed
- **Search Bar**: Migrata a `label.input input-bordered` DaisyUI con prefisso `SCAN_QUERY //` in neon cyan integrato — coerente con lo stile delle modali.
- **File Grid Buttons**: Aggiunto `btn-neon` (cyan) a tutti i pulsanti non-Delete e gap `gap-2` tra i bottoni. Aggiunto wrapper DaisyUI `tooltip tooltip-bottom` per ogni azione.
- **CSS — `.btn-neon`**: Aggiunta classe custom in `main.css` con `!important` per override DaisyUI su `btn-outline`.

## [4.6.2] - AEGIS_PROTOCOL (2026-03-26)
Consolidamento della stabilità dell'interfaccia e rilascio delle barriere fisiche di rendering.

### Added
- **Native Multi-Tab Sync**: Conversione universale dei trigger di navigazione in ancore `<a>` per supporto nativo browser.
- **Full-Grid Scan Overlay**: Schermo di caricamento neurale ad alta visibilità durante le scansioni dell'Oracle.
- **Wide-Format Intelligence HUD**: Modale di riepilogo espansa a 1200px per aderenza agli standard aeronautici.
- **Status Notifier 2.0**: Feedback di salvataggio potenziato con effetti pulse e glow neon Cyan.

### Fixed
- **Fullscreen Breakthrough**: Risolto il bug di "trapping" dei pannelli EasyMDE tramite disabilitazione automatica dei `backdrop-filter` genitori.
- **Z-Index Stratigraphy**: Stabilizzata la gerarchia dei layer; i tooltip ora dominano la visuale sopra l'editor e i breadcrumb.
- **Method Fallback**: Inserito supporto GET per le rotte Oracle per prevenire errori 405 durante la navigazione accidentale.

### Changed
- **Aegis Horizon Palette**: Aggiornamento cromatico verso Zinc-800 per l'editor e Slate Profondo per la preview.
- **Neural Capacity Boost**: Elevato il limite di predizione a 300 token con nuova logica di "Thought Completion".
- **Ghost-Text Visibility**: Suggerimenti IA ora visualizzati in Violetto ad alta opacità (0.8) per un contrasto ottimale.

## [4.2.0] - AEGIS PROTOCOL (2026-03-25)
Consolidamento dello strato neurale e perfezionamento dell'interfaccia industriale Aegis.

### Added
- **Manual Ghost-Text Unit**: Completamento predittivo manuale sincronizzato con priorità di input [TAB] (Single-Tab Acceptance).
- **Aegis Pulse Spinner**: Feedback visivo di uplink (`fa-circle-notch`) durante la generazione neurale per il monitoraggio della latenza.
- **Aegis Intelligence Scan**: Funzionalità di riepilogo automatico (Neural Summary) accessibile dal browser dei file.
- **Aegis Uplink Config**: Terminale di configurazione centralizzato per Branding PDF e protocolli Oracle.
- **Industrial Tooltips**: Integrazione sistematica dei tooltip DaisyUI su tutta la toolbar editoriale.
- **Documentation Expansion**: Integrata guida tecnica dettagliata per il setup industriale di Ollama su Ubuntu 24.04.

### Fixed
- **UI Ergonomics**: Ottimizzata la leggibilità delle modali neurali tramite l'adozione di `prose-lg` e ricalibrazione delle scale tipografiche (18px per i riepiloghi).
- **Editor Stability**: Risolto il bug dei "salti" di scrolling durante la generazione neurale tramite operazioni atomiche (`cm.operation`) di rendering del widget.
- **Icon Rendering conflict**: Risolta la collisione di pseudo-elementi tra DaisyUI e FontAwesome nella toolbar dell'editor.

## [4.1.0] - AEGIS REFACTOR (2026-03-25)
Protocollo di ristrutturazione architetturale completato. Allineamento totale ai principi SOLID.

### Changed
- **SOLID Filesystem Core**: Rifattorizzazione di `logic/files.py` in classi specializzate (`FileManager`, `DirectoryLister`, `Sanitizer`).
- **DIP Client Integration**: Implementati client dedicati e persistenti per Gotenberg e Oracle con gestione del ciclo di vita (FastAPI Lifespan).
- **Oracle Refactor**: Separazione del transport dalla logica di prompt engineering e transizione verso eccezioni strutturate.
- **Import Cleanup**: Eliminati gli import locali "pigri" nei router per una migliore telemetria degli errori in fase di startup.

### Fixed
- **Sanitization Warning**: Soppresso il warning `NoCssSanitizerWarning` tramite hardening del parser di stile in `bleach`.
- **Resource Leakage**: Risolto il potenziale leak di socket tramite pool client gestiti e chiusura automatica allo shutdown del kernel.

## [4.0.1] - AEGIS STABILITY PATCH (2026-03-25)
Correzioni UI e funzionalità operative post-BETA.

### Added
- **HUD_PRINT Toggle**: Generazione PDF con header/footer SC-ARCHIVE completo (HUD mode) oppure solo numero di pagina (default slim).
- **UP_DIRECTORY**: Riga di navigazione verso la directory superiore nel browser file, coerente con il Root Selector.
- **File Rename**: Funzionalità di rinomina file tramite modal HTMX con preservazione estensione automatica.

### Fixed
- **PDF Code Blocks**: Sostituito tema `atom-one-dark` con `default` di Highlight.js per leggibilità ottimale su sfondo bianco in stampa.
- **Search Icon Overflow**: L'icona di stato vuoto nella griglia risultati ora rispetta la classe dimensionale `w-12 h-12` passata via Jinja2 `with`.
- **Search Focus Style**: Campo di ricerca migrato a `input input-bordered` DaisyUI per uniformità con i controlli form delle modali (Neural Synthesis).

### Changed
- **Tailwind v4 Syntax**: Migrazione sistematica alla sintassi canonica v4 — `grow` (ex `flex-grow`), `(--var)` (ex `[var(--var)]`), `bg-linear-to-*` (ex `bg-gradient-to-*`), `z-n` (ex `z-[n]`).
- **CLAUDE.md**: Istruzioni agente consolidate con regole di stile, stack tecnologico e principi SOLID come riferimento operativo.

---

## [4.0.0-BETA] - AEGIS ORACLE (2026-03-25)
Integrazione dello strato di intelligenza neurale locale e normalizzazione industriale dell'interfaccia.

### Added
- **Neural Synthesis Unit**: Collegamento asincrono con `qwen2.5-coder` per la sintesi istantanea di diagrammi Mermaid da linguaggio naturale.
- **Neural Router**: Architettura backend dedicata (`logic/oracle.py`, `routes/oracle.py`) per il processamento SSE dei token AI.

### Fixed
- **UI Normalization (DaisyUI)**: Refactoring chirurgico delle modali (Oracle & Create) per aderenza totale agli standard `form-control` e `label` del framework.
- **Padding Protocol**: Risolto il bug dei testi "appiccicati" ai bordi tramite implementazione di un padding standardizzato di 24px (p-6) su tutti i campi di input.

### Note
- Lavoro di normalizzazione dei template identificato come **Parziale**. La migrazione verso lo standard `form-control` continuerà nelle release successive.

## [3.9.6] - AEGIS MODERNIZED STACK (2026-03-24)
Sincronizzazione della stazione con i protocolli Python 3.13 e migrazione dell'ecosistema dipendenze verso Poetry.

### Added
- **Python 3.13 Core**: Upgrade del nucleo di calcolo alla versione 3.13 per performance e stabilità superiori.
- **Poetry Migration**: Abbandono di Pipenv in favore di Poetry (v2.3.2) per una risoluzione dipendenze deterministica e ultra-veloce.
- **Aegis Signature Sync**: Aggiornate tutte le chiamate `TemplateResponse` (FastAPI/Starlette) per conformità con le nuove specifiche 0.40+.
- **Aegis Installation Guide**: Creata documentazione dedicata in `docs/installazione-pyenv-poetry.md`.
- **Tailwind CLI Spec**: Documentata formalmente la dipendenza dal compilatore standalone v4.2.1.

### Fixed
- **Type Safety**: Risolto l'errore `TypeError: unhashable type: dict` causato dalle divergenze di firma nelle nuove librerie.
- **Pipenv Removal**: Bonifica totale del workspace dai file legacy `Pipfile` e `Pipfile.lock`.

## [3.9.5] - AEGIS OFFLINE READY (2026-03-22)
Migrazione totale dell'infrastruttura verso l'isolamento locale per garantire operatività senza connessione internet.

### Added
- **Aegis Local Isolation**: Tutte le dipendenze (HTMX, DaisyUI, Marked, Highlight.js, Mermaid, EasyMDE, FontAwesome) sono ora servite localmente da `static/js` e `static/css`.
- **Slim-Tech Editor Evolution**: Migrazione del nucleo di scrittura a **Inconsolata 300** (Narrow & Thin) per una densità d'informazione aeronautica.
- **FontAwesome Recovery**: Ripristinato il database glifi locale (`static/webfonts/`) per la navigazione offline 100%.

### Fixed
- **Aegis Visual Sync**: Risolta la divergenza cromatica tra editing e preview tramite mappatura CSS dedicata (Style Parity Protocol).
- **Aegis Horizon Cleanup**: Rimossa la barra di scorrimento orizzontale "fantasma" tramite `lineWrapping` e soppressione mirata CSS.
- **Aegis Core Restore**: Risolto il bug della toolbar tagliata e delle barre verticali parassite causate da overflow eccessivo.
- **Branding Refresh**: Rebranding del footer in "CORE SERVICES" per bilanciare la gerarchia visiva con l'header "AEGIS CLASS".
- **Telemetry Optimization**: Ridotto a 5 il numero di frammenti recenti caricati nella dashboard per un cockpit più asciutto.
- Ottimizzato il protocollo di rendering PDF per includere Highlight.js anche nei documenti esportati (CDN fallback per Gotenberg).
- Risolto il problema del "Shell Nesting" (duplicazione header/footer) tramite filtraggio `HX-Request` nella rotta dashboard.

## [3.9.4] - AEGIS MODULAR ARCH (2026-03-22)

### Added
- **Aegis Sky Palette**: Nuova gamma cromatica Sky/Azure per migliorare leggibilità e contrasto nei sistemi di cockpit editoriale.
- **Mermaid Sync (Deep Editor)**: Integrazione dinamica dei grafici nel preview di EasyMDE e Pure Editor con debouncing (250ms).
- **Aegis Lumina Protocol**: Addio ai neri assoluti per una migliore profondità degli spazi di lavoro (Slate-Space).

### Fixed
- Risolto il bug di invisibilità dei grafici in Side-by-Side tramite protocollo di inizializzazione forcing.
- Pipeline PDF stabilizzata con `waitDelay` ricalibrato a 5s per diagrammi complessi.

## [3.9.0] - AEGIS VISUALIZATION (2026-03-21)
- **Aegis Visualization**: Supporto nativo per diagrammi Mermaid (Flow, Seq, Gantt).
- **Async Export Protocol**: Sincronizzazione con Gotenberg (waitDelay 3s) per export PDF coerente.
- **Auto-Transform**: Protocollo JS per la conversione dinamica dei blocchi di codice Markdown in vettoriali.

## [3.5.0] - AEGIS DISCOVERY (2026-03-21)
Introduzione del motore di ricerca globale e supporto multiformato per l'Archivio Dati.

### Added
- **Global Search Engine**: Ricerca ricorsiva ad alta velocità per file `.md`, `.html` e `.pdf` nel Data Archive con HUD dedicato.
- **Multiformat Support**: Supporto nativo per la visualizzazione di file HTML (apertura scheda) e PDF (preview Aegis integrata).
- **Auto-Discovery**: Indicizzazione automatica dei contenuti testuali per ricerca contestuale.

### Fixed
- **UI Nesting Bug**: Risolto il bug di ricorsione nei componenti breadcrumb (glitch matrioska visuale).
- **Search Alignment**: Perfezionamento millimetrico del modulo di ricerca Aegis e centratura placeholder.
- **Storage Stats**: Risolto errore `TypeError` nel calcolo delle statistiche di storage dovuto a errata rimozione di codice durante il refactoring.

## [3.1.0] - AEGIS SECURITY HARDENING (2026-03-20)
Rafforzamento dei protocolli di sicurezza e stabilità del sistema "Aegis Class".

### Added
- **Sanitizzazione XSS (HTML Node)**: Integrazione di `bleach` nella pipeline di conversione PDF per bloccare l'iniezione di script malevoli via Markdown.

### Changed
- **System Stability**: Rimozione delle procedure di soppressione errori (`except: pass`) in favore della trasparenza dei guasti nel kernel dell'applicazione.

### Fixed
- **Compliance Protocol**: Allineamento completo alle `CODING GUIDELINES` del sistema SC-ARCHIVE.

## [3.0.0] - SC-ARCHIVE RELEASE (2026-03-18)
Identità finale "Spacecraft Documentation Management System".

### Added
- **Logo & Favicon**: Integrazione dell'icona **Holocron** (SVG vettoriale) con bagliore neon.
- **Micro-animazioni**: Radar di sistema (0.022Hz) nel pannello `SYSTEM_STATUS`.
- **Aegis Transitions**: Animazioni di `scan-in` e `soft-exit` per tutte le finestre modali.
- **UX Workflow**: Reindirizzamento automatico al File Browser dopo la selezione della directory radice.

### Changed
- **Branding**: Ridenominazione completa da `MD2FastPDF` a `SC-ARCHIVE`.
- **PDF Engine**: Passaggio definitivo a **Gotenberg** (Chromium) per rendering professionale.
- **HUD PDF**: Aggiunta di testata, piè di pagina e numerazione automatica.
- **View Mode**: Forza la visualizzazione PDF in "Fit Width" (`FitH`).

## [3.0.0] - SC-ARCHIVE RELEASE (2026-03-18)
Identità finale "Spacecraft Documentation Management System".

---

### [ARCHIVE_LINK] // LOG_STORAGE
Per i log storici delle versioni del Sistema precedenti alla v3.0.0:
🔍 [Visualizza l'Archivio Storico (v1.0.0-v2.1.0)](docs/archive/CHANGELOG_v1-2.md)

*Mantenuto dai protocolli Aegis Class System.*
