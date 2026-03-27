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

### [4.4] - AEGIS CHRONOS (Versionamento Narrativo) [PLANNED — NEXT]
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

### [4.5] - AEGIS BLUEPRINT (Technical Templating)
**Obiettivo**: Standardizzazione della produzione documentale industriale.
- **Galeria Blueprint**: Inserimento istantaneo di template (Missions, Tech Specs, Logs).
- **Variable Injection**: Sostituzione dinamica di segnaposto nel Markdown prima dell'export PDF.

---

### [4.6] - AEGIS MULTI-LINK (Efficiency Multi-Tasking)
**Obiettivo**: Gestione simultanea di più flussi informativi.
- **Tabbed Workspace**: Interfaccia a schede HTMX per l'editing simultaneo di più documenti.
- **Split Pane Sync**: Trascinamento e sincronizzazione di sezioni tra diversi documenti aperti.

---

### [4.7] - AEGIS GUARD (Local Security Protocol)
**Obiettivo**: Blindatura dei dati locali e gestione dell'accesso in rete.
- **Buffer Encryption**: Cifratura simmetrica dei documenti sensibili a livello di filesystem.
- **Network Gateway UI**: Strumenti per la gestione della visibilità della stazione nella rete WiFi locale.

---

### [4.8] - AEGIS STABILITY (System Integrity)
**Obiettivo**: Rafforzamento della robustezza del codice e della diagnostica in tempo reale.
- **Centralized Exception Handling**: Implementazione di un gestore centralizzato delle eccezioni custom (`logic/exceptions.py`) per una telemetria ultra-precisa dei guasti direttamente nell'HUD operativo.

---

**(I flussi operativi futuri sono stati ricalibrati. Aegis Oracle promosso a priorità assoluta [4.0] del ciclo operativo corrente.)** 🚀🌑
