# AEGIS ROADMAP: Direttive 4.x // "Aegis Command Station"

Questo documento delinea la strategia di espansione per la stazione operativa **SC-ARCHIVE**.

---

### [4.0] - AEGIS ORACLE (Active Deployment // Phase 1) [COMPLETED]
**Obiettivo**: Dotare la stazione di uno strato di intelligenza neurale locale per massimizzare la velocità di produzione.
- **Modello Operativo Primario**: `qwen2.5-coder:7b` (via Ollama locale). Ottimizzato per generazione strutturata e aderenza sintattica a Markdown/Mermaid.
- **Specifiche Hardware Base**: Compatibilità certificata per Full GPU Offload su architettura Pascal (es. Nvidia GTX 1070 Ti 8GB VRAM) in ambiente WSL2 con 16GB RAM di sistema.
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

### [4.2] - AEGIS RENDER (Mermaid Image Export) [PRIORITY]
**Obiettivo**: Estrazione e export dei diagrammi Mermaid come immagini standalone dal documento.
- **SVG Export**: Rendering lato server del codice Mermaid in SVG tramite `mermaid-js` headless (via Gotenberg o Node subprocess).
- **PNG Rasterization**: Conversione SVG→PNG a risoluzione configurabile per embed in documenti tecnici.
- **Bulk Extract**: Estrazione di tutti i blocchi Mermaid presenti nel documento in un archivio `.zip`.
- **Inline Inject**: Opzione per sostituire il blocco ` ```mermaid ` nel buffer con il tag `![diagram](path)` dell'immagine generata.

---

### [4.3] - AEGIS CHRONOS (Versionamento Visivo)
**Obiettivo**: Integrazione profonda con i protocolli di controllo della versione.
- **Git Terminal UI**: Pannello dedicato per commit, push e sync Git direttamente dall'interfaccia.
- **Visual Diff Cockpit**: Confronto grafico tra buffer corrente e ultimo stato archiviato (Git Diff).

---

### [4.4] - AEGIS BLUEPRINT (Technical Templating)
**Obiettivo**: Standardizzazione della produzione documentale industriale.
- **Galeria Blueprint**: Inserimento istantaneo di template (Missions, Tech Specs, Logs).
- **Variable Injection**: Sostituzione dinamica di segnaposto nel Markdown prima dell'export PDF.

---

### [4.5] - AEGIS MULTI-LINK (Efficiency Multi-Tasking)
**Obiettivo**: Gestione simultanea di più flussi informativi.
- **Tabbed Workspace**: Interfaccia a schede HTMX per l'editing simultaneo di più documenti.
- **Split Pane Sync**: Trascinamento e sincronizzazione di sezioni tra diversi documenti aperti.

---

### [4.6] - AEGIS GUARD (Local Security Protocol)
**Obiettivo**: Blindatura dei dati locali e gestione dell'accesso in rete.
- **Buffer Encryption**: Cifratura simmetrica dei documenti sensibili a livello di filesystem.
- **Network Gateway UI**: Strumenti per la gestione della visibilità della stazione nella rete WiFi locale.

---

### [4.7] - AEGIS STABILITY (System Integrity)
**Obiettivo**: Rafforzamento della robustezza del codice e della diagnostica in tempo reale.
- **Centralized Exception Handling**: Implementazione di un gestore centralizzato delle eccezioni custom (`logic/exceptions.py`) per una telemetria ultra-precisa dei guasti direttamente nell'HUD operativo.

---

**(I flussi operativi futuri sono stati ricalibrati. Aegis Oracle promosso a priorità assoluta [4.0] del ciclo operativo corrente.)** 🚀🌑
