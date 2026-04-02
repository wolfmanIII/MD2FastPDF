# Piano di Implementazione: AEGIS ORACLE (Intelligenza Neurale Locale)

Il protocollo AEGIS ORACLE dota SC-ARCHIVE di uno strato di intelligenza neurale indipendente tramite `Ollama` e il modello `qwen2.5-coder:7b`. L'architettura è progettata per minimizzare la latenza e integrarsi nativamente con il pattern asincrono di FastAPI e il rendering parziale HTMX.

## 1. Strato Logico: Connessione Ollama (Backend)
Verrà creato un nuovo modulo (`logic/oracle.py`) per interfacciarsi con l'API REST locale di Ollama.

### [NEW] `logic/oracle.py`
- Utilizza `httpx.AsyncClient` persistente (come Gotenberg) per comunicare con `http://172.31.112.1:11434`.
- **`generate_completion(prompt, stream=True)`**: Chiama `/api/generate` per l'inserimento ghost/autocompletamento in streaming.
- **`generate_mermaid(text)`**: Converte direttive testuali in pura sintassi Mermaid (istruendo il system prompt a evitare convenevoli come "Certo, ecco il codice...").
- **`summarize_document(content)`**: Estrae e condensa i punti chiave di un documento in Markdown sintetico.

## 2. Router API: Esposizione Funzionalità
Verrà aggiunto un router dedicato per gestire le chiamate dell'editor e dell'HUD senza impattare le rotte core.

### [NEW] `routes/oracle.py`
- Sotto-rotte esposte:
  - `POST /api/oracle/complete` (StreamingResponse compatibile con SSE).
  - `POST /api/oracle/mermaid` (JSON request/response).
  - `POST /api/oracle/summarize` (HTML response renderizzata via Jinja2 per inserimento HTMX diretto).
  
### [MODIFY] `main.py`
- Inserimento del nuovo router: `app.include_router(oracle.router)`.

## 3. Frontend: HTMX & UI dell'Editor
Integrazione dei comandi all'interno dell'interfaccia utente, mantenendo l'estetica "Aegis Slim-Tech".

### [MODIFY] `templates/editor.html`
- **Neural Completion**: Integrazione di uno script JS (Vanilla) che gestisce la digitazione nell'editor `EasyMDE/CodeMirror`. Verrà introdotto un **debounce di 800ms**. Se l'operatore si ferma per 800ms, parte la richista asincrona a `/api/oracle/complete` e viene mostrato il "ghost text" trasparente. Se l'utente preme `Tab`, il testo viene inglobato.
- **Mermaid Synthesis**: Aggiunta di un'icona (Holocron-style) nella toolbar dell'editor che lancia una modale per inserire la testualità.

### [NEW] `templates/components/oracle_mermaid_modal.html`
- Frammento HTML per inserimento testo "Descrivi diagramma logico...", con input inviato ad `/api/oracle/mermaid`. Al completamento, il JS inserisce ` ```mermaid ... ``` ` nell'editor.

### [NEW] `templates/components/oracle_summary_hud.html`
- Pannello richiamato asincronamente dall'Archivio principale. Un bottone via `htmx` spara `hx-post="/api/oracle/summarize"` e rimpiazza un placeholder con la lista dei concetti chiave.

## Piano di Verifica
**Verifica Manuale (Operatore):**
1. Eseguire l'infrastruttura (`Ollama` localmente con modello scaricato + `./bin/launch.sh`).
2. *Autocompletamento*: Digitare un paragrafo e fermarsi. Verificare l'apparizione del testo suggerenziale senza freezare CodeMirror, misurando il Time-To-First-Token (~500ms).
3. *Mermaid*: Dettare "Un flusso che va dal server al client per scaricare PDF" e forzare l'incollatura corretta del blocco generato nel documento (e sua rendering).
4. *Summarize*: Selezionare un documento di almeno 2000 parole e visualizzare l'estratto.
