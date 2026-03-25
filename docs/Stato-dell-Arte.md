# Stato del Progetto: SC-ARCHIVE
**Stato Attuale**: Op_Ready / Versione 4.0.0-BETA (Aegis Oracle Phase 1)
**Ultimo Aggiornamento**: 25 Marzo 2026 (Ciclo Oracle + Archive Ops)

## 1. Funzionalità Implementate (Aegis Stack)

### 1.1 Gestione File & Discovery
- Navigazione filesystem locale con breadcrumbs dinamici e root-selection modale.
- **UP_DIRECTORY**: Voce di navigazione rapida alla directory padre nel browser file.
- **Ricerca Globale Aegis**: Motore di scansione ricorsiva per file `.md`, `.html` e `.pdf`.
- **Aegis Visualization**: Integrazione **Mermaid.js** per diagrammi di flusso e schemi logici.
- **Multiformat Viewer**: Supporto integrato per PDF (Aegis Preview) e HTML (scheda esterna).
- Dashboard "Spacecraft" con monitoraggio CPU/Memoria e radar HUD (ciclo 30s).
- Terminal Matrix: Sistema di monitoraggio core integrato.
- **Rinomina File**: Operazione di rename in-place con modal dedicato, sanitizzazione path e preservazione estensione automatica.
- **Operazioni File**: Creazione, eliminazione e rinomina con conferma modale e feedback HTMX.

### 1.2 Editor Markdown (Aegis Slim-Tech)
- **Slim-Tech Aesthetic**: Inconsolata 300 per scrittura densa e sottile.
- Evidenziatura sintassi disattivata in editing (sx), mantenuta in preview (dx).
- **Ariel Monospace Feel**: UI ottimizzata per neutralità e performance.
- Integrazione logo Holocron e icone vettoriali HQ.

### 1.3 Esportazione PDF (Aegis Engine)
- Integrazione Gotenberg (Docker) per rendering Chromium professionale.
- **Aegis Security Layer**: Sanitizzazione XSS via `bleach` attiva sulla pipeline di conversione.
- **HUD_PRINT Toggle**: Modalità di stampa selezionabile — default solo numero di pagina nel footer; modalità HUD attiva header branded (`SC-ARCHIVE // filename / AEGIS // SECURED`) e footer operativo completo (`OS_CORE_v2.0`).
- Loader overlay con animazione al cambio modalità di stampa.
- Sintassi highlighting nei blocchi di codice: tema `default` (chiaro) di Highlight.js.
- Viewport predefinita in "Adatta alla Larghezza" (`FitH`).
- Rendering liste `ul/ol/li` corretto nel CSS industriale del PDF.

### 1.4 Neural Interface — AEGIS ORACLE (Phase 1)
- **Modello**: `qwen2.5-coder:7b` via Ollama locale (`http://172.31.112.1:11434`), configurabile via env.
- **Neural Completion**: Streaming SSE asincrono (`POST /api/oracle/complete`) con debounce 800ms nell'editor.
- **Mermaid Synthesis**: Generazione diagrammi Mermaid da testo naturale (`POST /api/oracle/mermaid`) con modal dedicato.
- **Auto-Summarization**: Riepilogo contestuale documenti (`POST /api/oracle/summarize`) con rendering HTMX nel HUD.

### 1.5 UX Fluidity & Safety
- Transizioni `scan-in` e `soft-exit` per tutte le componenti modali.
- Eliminazione totale del "blink" visivo durante caricamento HTMX.
- Pulsanti azioni file (rinomina, elimina) con componenti DaisyUI nativi per coerenza cross-browser.
- **System Stability**: Rimozione soppressioni di errore silenziose per conformità ai protocolli di bordo.

## 2. Infrastruttura Tecnica
- **Backend**: FastAPI (Python 3.13) + anyio + httpx.
- **Frontend**: HTMX, Tailwind v4 (sintassi canonica), DaisyUI, Font Awesome, EasyMDE.
- **Container**: Gotenberg (Chromium-based PDF Engine).
- **AI Layer**: Ollama (locale, GPU offload Pascal-class).
- **Environment**: Poetry + pyenv.
- **Agent Config**: `CLAUDE.md` con regole architetturali e stile codice.

## 3. Roadmap Prossimi Cicli
| Fase | Codice | Obiettivo |
|---|---|---|
| Prossima | [4.1] CHRONOS | Git Terminal UI + Visual Diff Cockpit |
| Pianificata | [4.2] BLUEPRINT | Template gallery + Variable Injection |
| Pianificata | [4.3] MULTI-LINK | Tabbed Workspace + Split Pane Sync |
| Pianificata | [4.4] GUARD | Buffer Encryption + Network Gateway UI |
| Pianificata | [4.5] STABILITY | Centralized Exception Handling (`logic/exceptions.py`) |

---
*SC-ARCHIVE Operational Log // Aegis Oracle Phase 1 — DEPLOYMENT_ACTIVE.*
