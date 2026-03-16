# Documento di Specifica Tecnica: MD2FastPDF
**Versione**: 2.0 (Post-NiceGUI Analysis)
**Ruolo**: Senior Linux Software Engineer / Architect

## 1. Obiettivo del Progetto
Realizzare un editor Markdown "Industrial" ottimizzato per ambiente Linux. L'applicazione deve permettere la gestione di documentazione complessa in formato Markdown, fornendo un'anteprima in tempo reale e una conversione PDF professionale tramite template predefiniti.

## 2. Requisiti Funzionali Core
### 2.1 Gestione Filesystem
- **Esplorazione**: Navigazione ricorsiva in una directory radice (`project_root`).
- **Operazioni File**: Creazione, lettura, aggiornamento e cancellazione (CRUD) di file `.md`.
- **Breadcrumbs**: Sistema di navigazione dinamico basato sul percorso relativo alla root.
- **Ricerca**: Ricerca full-text ricorsiva all'interno dei file markdown con estratto della riga colpita.

### 2.2 Editing Markdown
- **Editor**: Integrazione di un editor professionale (es. EasyMDE) con supporto syntax highlighting.
- **Preview**: Anteprima in tempo reale (Side-by-Side).
- **Mermaid**: Supporto nativo per diagrammi Mermaid all'interno dei file markdown.

### 2.3 Conversione PDF
- **Motore di Conversione**: Integrazione con Gotenberg (via Docker) per rendering Chromium-based.
- **Template System**: Supporto per template HTML/CSS multipli (Clean, Industrial).
- **Anteprima PDF**: Visualizzazione del PDF generato in un tab separato senza download forzato.

## 3. Requisiti Architetturali (Critici)
### 3.1 Isolamento Multi-Tab (Sandboxing)
- **Indipendenza Totale**: Ogni scheda del browser deve operare in modo completamente indipendente.
- **Stato Isolato**: Variabili come la cartella corrente (`current_dir`), il file aperto (`current_file`) e la query di ricerca devono essere confinate alla sessione specifica del client/tab.
- **Prevenzione Collisioni**: L'apertura di un file nel Tab A non deve influenzare la vista o lo stato del Tab B.

### 3.2 Gestione dello Stato (Stateless Backend)
- **Session Isolation**: Utilizzo di cookie o parametri di query per mantenere lo stato del client (es. `current_path`) senza affidarsi a variabili globali server-side.
- **Atomic Rendering**: HTMX deve sostituire frammenti di DOM in modo atomico.

### 3.3 Robustezza JS/DOM
- **Progressive Enhancement**: JS utilizzato solo dove strettamente necessario (es. inizializzazione editor Markdown).
- **Graceful Degradation**: L'interfaccia deve rimanere funzionale anche in caso di errori di script minori.

## 4. Estetica e UI/UX
- **Tema**: "Industrial/Sci-Fi". Palette scura (Slate/Zinc), font monospace per codici, accenti neon (Indigo/Violet).
- **Interattività**: Micro-animazioni, feedback visivi immediati al salvataggio (Toast notifications).
- **Responsive**: Layout adattabile, con modalità fullscreen per l'editor.

## 5. Stack Tecnologico Consigliato
Sulla base delle limitazioni riscontrate con stack a bassa astrazione dello stato (NiceGUI), si consiglia:
- **Backend**: FastAPI (Python 3.12+).
- **Frontend**: HTMX (aggiornamenti parziali) + Jinja2 (templating).
- **Styling**: Tailwind (v4) + typography plugin.
- **PDF Engine**: Gotenberg (Docker).

## 6. Vincoli di Sicurezza
- **Path Sanitization**: Impedire navigation attacks (`../`) fuori dalla `project_root`.
- **Sanitizzazione Markdown**: Prevenire XSS nell'anteprima HTML dei file markdown.
