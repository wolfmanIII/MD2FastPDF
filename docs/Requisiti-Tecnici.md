# Documento di Specifica Tecnica: SC-ARCHIVE
**Versione**: 3.0 (Spacecraft Archive Edition)
**Ruolo**: Senior Linux Software Engineer / Architect

## 1. Obiettivo del Progetto
Realizzare un sistema di gestione documentale "Spacecraft" (`SC-ARCHIVE`) ottimizzato per ambiente Linux. L'applicazione deve permettere la gestione di documentazione critica in formato Markdown, fornendo un'anteprima HUD e una conversione PDF di classe Aegis tramite Gotenberg.

## 2. Requisiti Funzionali Core
### 2.1 Gestione Filesystem
- **Esplorazione**: Navigazione ricorsiva in una directory radice (`project_root`).
- **Operazioni File**: CRUD completo di file `.md`.
- **Breadcrumbs**: Sistema di navigazione dinamico in scala di grigi/ciano.
- **Root Selection**: Scelta dinamica della directory di lavoro tramite modale dedicata.

### 2.2 Editing Markdown
- **Editor**: Integrazione EasyMDE (CodeMirror) con supporto Fullscreen.
- **Preview**: Anteprima in tempo reale (Side-by-Side).
- **Branding**: Integrazione logo Holocron e icone industriali.

### 2.3 Conversione PDF (Aegis Engine)
- **Motore**: Gotenberg (Chromium) in container Docker.
- **Paginazione**: Inserimento automatico di numeri di pagina e footer HUD.
- **Viewport**: Visualizzazione predefinita in modalità "Adatta alla Larghezza".

## 3. Requisiti Architetturali (Critici)
### 3.1 Isolamento Multi-Tab (Sandboxing)
- **Indipendenza**: Ogni scheda del browser deve operare in modo completamente indipendente via URL params.
- **Statelessness**: Nessun affidamento a variabili globali server-side per lo stato del file aperto.

### 3.2 UI/UX Fluidity
- **Aegis Transitions**: Animazioni di entrata/uscita per le componenti modali.
- **Radar HUD**: Micro-animazione di scansione a bassa frequenza (45s cycle).

## 4. Estetica e UI/UX
- **Tema**: "Spacecraft/Aegis". Palette Slate/Zinc, font Rajdhani e Roboto Mono.
- **Feedback**: Transizioni fluide HTMX per eliminare il "blink" di sistema.

## 5. Stack Tecnologico
- **Backend**: FastAPI (Python 3.12+).
- **Frontend**: HTMX + Tailwind v4 + Jinja2.
- **PDF Engine**: Gotenberg (Docker).

## 6. Vincoli di Sicurezza
- **Path Sanitization**: Protezione contro Directory Traversal.
- **Sanitizzazione Markdown**: Prevenzione XSS nell'anteprima.

---
*Specifiche di Sistema SC-ARCHIVE.*
