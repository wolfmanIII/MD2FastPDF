# Analisi Tecnica: MD2FastPDF
**Progetto**: Editor Markdown e Generatore PDF (FastAPI + HTMX)
**Data**: 17 Marzo 2026

## 1. Architettura di Sistema
L'applicazione segue un modello di sviluppo asincrono basato su FastAPI, orientato al basso consumo di risorse e alla modularità dei componenti.

### 1.1 Backend (Python / FastAPI)
- **FastAPI**: Utilizzato come framework web per la gestione delle rotte e della logica asincrona.
- **Asincronia**: Gestione nativa tramite `asyncio` per operazioni di I/O (Filesystem) e richieste HTTP (Gotenberg API).
- **Statelessness**: Lo stato della sessione (es. percorso corrente) è gestito sul client tramite parametri di query, eliminando la necessità di sessioni server-side.
- **Jinja2**: Motore di templating per il rendering server-side di frammenti HTML.

### 1.2 Frontend (HTMX / Tailwind)
- **HTMX**: Gestisce l'aggiornamento parziale del DOM tramite richieste AJAX/SSE, eliminando il caricamento completo della pagina.
- **Tailwind CSS v4**: Fornisce il sistema di styling atomico e il design responsive.
- **EasyMDE/CodeMirror**: Componente JavaScript per la gestione dell'editor Markdown con syntax highlighting.

### 1.3 Generazione PDF (Gotenberg)
- **Pipeline**: Il contenuto Markdown viene convertito in HTML via Jinja2 e inviato a un container Docker Gotenberg tramite richieste HTTP.
- **CSS Tipografico**: Durante la conversione viene iniettato un foglio di stile specifico per la stampa (font Inter, scala di grigi), separato dalla UI dell'applicazione.

## 2. Struttura dei Moduli Logici

### 2.1 Gestione Filesystem (`logic/files.py`)
- Filtra i file nascosti e di sistema.
- Implementa la sanitizzazione dei percorsi per prevenire attacchi di tipo *Directory Traversal*.
- Esegue operazioni CRUD in modalità asincrona tramite `anyio`.

### 2.2 Motore di Conversione (`logic/conversion.py`)
- Gestisce il workflow di trasformazione da Markdown a PDF.
- Implementa la logica di iniezione degli stili CSS print-ready.
- Interfaccia con l'API di Gotenberg utilizzando `httpx`.

### 2.3 Sistema di Icone (`templates/icons/`)
- Libreria di icone SVG gestite come componenti Jinja2 (`{% include %}`).
- Supporto per parametri dinamici (classi CSS, dimensioni).

## 3. Interfaccia Utente (UI)
- **Stile**: Dark mode con accenti ciano. Utilizza `backdrop-filter` per effetti di trasparenza (Blur).
- **Tipografia**: `Rajdhani` per intestazioni tecniche e `Roboto Mono` per i dati e l'editor.
- **Feedback**: Notifiche di salvataggio temporanee tramite script inline che rimuovono l'elemento dal DOM dopo un timeout predefinito.

## 4. Sicurezza e Distribuzione
- **Sanitizzazione**: Validation dei path rispetto a una `PROJECT_ROOT` fissa.
- **Pipenv**: Gestione deterministica dell'ambiente virtuale e delle dipendenze.
- **Docker**: Containerizzazione del microservizio di rendering PDF.

---
*Documento Tecnico Interno.*
