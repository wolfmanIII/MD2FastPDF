# Analisi Tecnica: SC-ARCHIVE
**Progetto**: Space Craft Archive Management System (FastAPI + HTMX)
**Nome Tecnico Interno**: MD2FastPDF
**Data**: 28 Marzo 2026

## 1. Architettura di Sistema
L'applicazione segue un modello di sviluppo asincrono basato su FastAPI, orientato al basso consumo di risorse e alla modularità dei componenti, con un'estetica "Spacecraft Computer".

### 1.1 Persistenza e Configurazione (`config/settings.py`)
- **JSON Store**: `config/settings.json` come sorgente unica di verità. Il modulo `config/settings.py` (package Python `config/`) è co-locato con il suo store.
- **SettingsManager**: classe con `get()`, `set()` async, `batch_update()` (singola scrittura disco), `_save_sync()` solo per startup.
- **Dynamic Uplink**: coordinate dei servizi (Ollama, Gotenberg) e preferenze IA caricate all'avvio e modificabili a runtime.
- **Aggiornamento Reattivo**: trigger HTMX (`settings-updated`) per sincronizzazione dashboard post-modifica.

### 1.2 Backend (Python / FastAPI)
- **FastAPI**: cuore del sistema per la gestione delle rotte e della logica asincrona.
- **Asincronia**: `asyncio` + `anyio` per I/O filesystem e richieste HTTP (Gotenberg, Ollama).
- **Statelessness**: stato sessione gestito sul client tramite parametri di query.
- **Jinja2**: motore di templating per il rendering server-side.
- **SOLID Compliance**: Protocol-based abstractions in `conversion.py`; mutation hook registry in `files.py`; dependency injection via constructor in `oracle.py` e `GotenbergClient`.

### 1.3 Frontend (HTMX / Tailwind)
- **HTMX**: aggiornamento parziale del DOM con transizioni fluide ("Aegis Transitions").
- **Tailwind CSS v4**: sistema di styling atomico e design "Glassmorphism" industriale.
- **EasyMDE/CodeMirror**: editor Markdown con Fullscreen e Side-by-Side.
- **CSP Ready**: nessun attributo `style=` inline nei template (eccetto 2 valori CSS dinamici Jinja2). CSS estratti in file statici dedicati.

### 1.4 Generazione PDF (Gotenberg)
- **Pipeline**: MD → HTML → PDF via Gotenberg (Chromium Engine).
- **Protocol classes**: `PageScaffolding` (Protocol), `DetailedScaffolding`, `MinimalScaffolding`, `MarkdownRenderer`, `PdfHtmlBuilder` — tutti iniettabili in `GotenbergClient`.
- **Industrial CSS**: `static/css/pdf-industrial.css` caricato una volta a module init — nessun CSS inline nel codice Python.
- **HUD Tipografico**: testate e piè di pagina con paginazione dinamica (`{{pageNumber}}` / `{{totalPages}}`).
- **Nota**: header/footer HTML inviati a Gotenberg contengono `style=` inline strutturali — Gotenberg opera in sandbox isolata senza accesso ai file statici dell'app.

## 2. Struttura dei Package

### 2.1 `logic/` — Business Logic
- `files.py`: `FileManager`, `DirectoryLister`, `PathSanitizer`, `StorageCache`. Mutation hook registry per invertire dipendenza verso cache. `os.scandir` offloaded via `anyio.to_thread.run_sync`.
- `conversion.py`: `GotenbergClient` con DI; Protocol types per scaffolding, renderer, builder; CSS caricato da file statico.
- `oracle.py`: `OracleClient` con DI (`SettingsManager`); `_EMBEDDING_KEYWORDS` frozenset; `service_status()`, `list_models()`.
- `render.py`: export PNG/ZIP Mermaid via Gotenberg.
- `templates.py`: helper Jinja2.

### 2.2 `routes/` — API Routers
- `__init__.py`: `build_breadcrumbs(path)` utility condivisa.
- `core.py`: dashboard, stats, services status (delega a `gotenberg.health_check()` e `oracle.service_status()`).
- `archive.py`, `editor.py`, `pdf.py`, `oracle.py`, `settings.py`, `config.py`.

### 2.3 `config/` — Configuration Package
- `settings.py`: `SettingsManager` + istanza globale `settings`.
- `settings.json`: store persistente.

### 2.4 `static/css/` — Design System
- `output.css`: Tailwind compiled output.
- `editor-aegis.css`: stili EasyMDE, fullscreen fix, layout editor.
- `pdf-industrial.css`: stylesheet documento PDF (Gotenberg).
- `pdf-preview.css`: tooltip override, iframe, overflow per il viewer PDF.
- `main.css`: utility classes globali (`.aegis-input-bg`, `.btn-violet`, `.btn-neon`, ecc.).

### 2.5 Sistema di Icone (`templates/icons/`)
- Componenti SVG Jinja2. Include l'icona **Holocron** come simbolo di sistema.

## 3. Interfaccia Utente (UI)
- **Micro-animazioni**: Radar di sistema calibrato a 45s per effetto atmosferico.
- **Modali Aegis**: transizioni `scan-in` e `soft-exit` per eliminare i flash visivi.
- **Branding**: integrazione del logo Holocron vettoriale.

## 4. Sicurezza e Distribuzione
- **Sanitizzazione Path**: validazione dei path rispetto alla `PROJECT_ROOT` (Anti-Traversal).
- **Sanitizzazione Markdown**: prevenzione XSS tramite `bleach` nella pipeline di conversione.
- **CSP Compliance**: eliminazione totale degli attributi `style=` inline da template e route. `Content-Security-Policy: style-src 'self'` applicabile senza `unsafe-inline`.
- **Error Handling**: politica "Zero Suppression" (nessun `except: pass`) per visibilità dei guasti.
- **Docker**: containerizzazione obbligatoria per Gotenberg.

---
*Documento Tecnico Aegis Class System // v5.3.0.*
