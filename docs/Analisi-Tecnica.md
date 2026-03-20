# Analisi Tecnica: SC-ARCHIVE
**Progetto**: Space Craft Archive Management System (FastAPI + HTMX)
**Nome Tecnico Interno**: MD2FastPDF
**Data**: 20 Marzo 2026

## 1. Architettura di Sistema
L'applicazione segue un modello di sviluppo asincrono basato su FastAPI, orientato al basso consumo di risorse e alla modularità dei componenti, con un'estetica "Spacecraft Computer".

### 1.1 Backend (Python / FastAPI)
- **FastAPI**: Cuore del sistema per la gestione delle rotte e della logica asincrona.
- **Asincronia**: Gestione nativa tramite `asyncio` per operazioni di I/O (Filesystem) e richieste HTTP (Gotenberg API).
- **Statelessness**: Lo stato della sessione è gestito sul client tramite parametri di query.
- **Jinja2**: Motore di templating per il rendering server-side.

### 1.2 Frontend (HTMX / Tailwind)
- **HTMX**: Gestisce l'aggiornamento parziale del DOM con transizioni fluide ("Aegis Transitions").
- **Tailwind CSS v4**: Sistema di styling atomico e design "Glassmorphism" industriale.
- **EasyMDE/CodeMirror**: Editor Markdown di bordo con supporto Fullscreen e Side-by-Side.

### 1.3 Generazione PDF (Gotenberg)
- **Pipeline**: MD -> HTML -> PDF via Gotenberg (Chromium Engine).
- **HUD Tipografico**: Iniezione di testate e piè di pagina con paginazione dinamica (`{{pageNumber}}` / `{{totalPages}}`).
- **View Mode**: Forza la visualizzazione in "Fit Width" (`#view=FitH`) per coerenza con i monitor di bordo.

## 2. Struttura dei Moduli Logici

### 2.1 Gestione Filesystem (`logic/files.py`)
- Filtra file nascosti e system-dirs (`.git`, `node_modules`, etc.).
- Sanitizzazione dei percorsi (Anti-Traversal).
- Operazioni CRUD asincrone tramite `anyio`.

### 2.2 Motore di Conversione (`logic/conversion.py`)
- Gestisce il workflow di trasformazione verso Gotenberg.
- **Sanitizzazione XSS**: Integra la libreria `bleach` per pulire l'HTML generato dal Markdown prima dell'invio a Gotenberg, prevenendo l'esecuzione di script malevoli nel PDF.
- Implementa lo stile "Aegis Print" (Inter, scala di grigi, 1cm margin).

### 2.3 Sistema di Icone (`templates/icons/`)
- Componenti SVG Jinja2. Include l'icona **Holocron** come simbolo di sistema.

## 3. Interfaccia Utente (UI)
- **Micro-animazioni**: Radar di sistema calibtrato a 45s per effetto atmosferico.
- **Modali Aegis**: Transizioni di `scan-in` e `soft-exit` per eliminare i flash visivi.
- **Branding**: Integrazione del logo Holocron vettoriale.

## 4. Sicurezza e Distribuzione
- **Sanitizzazione Path**: Validation dei path rispetto alla `PROJECT_ROOT` per prevenire Directory Traversal.
- **Sanitizzazione Markdown**: Prevenzione XSS tramite `bleach` durante la pipeline di conversione.
- **Error Handling**: Politica "Zero Suppression" (rimozione di `except: pass`) per garantire la visibilità dei guasti di sistema.
- **Docker**: Containerizzazione obbligatoria per Gotenberg.

---
*Documento Tecnico Aegis Class System.*
