# SC-ARCHIVE // Spacecraft Documentation Management System
**Versione 4.8.0** // AEGIS FILETREE

> [!NOTE]
> **MD2FastPDF** is the internal technical name for the project core and backend services. **SC-ARCHIVE** is the external station designation and branding.

**SC-ARCHIVE** is an "Aegis Class" documentation management system designed for operational speed and professional PDF generation via the **Gotenberg** infrastructure.

## 🛠 Tech Stack
- **Core**: Python 3.13+ + FastAPI
- **Frontend**: HTMX + Tailwind CSS v4 Standalone CLI (v4.2.1) + Jinja2
- **Editor**: EasyMDE (CodeMirror 5)
- **PDF Engine**: Gotenberg (Chromium via Docker)
- **Neural Engine**: local Ollama (`qwen2.5-coder:7b`)
- **CSS Optimizer**: Tailwind CSS Standalone Compiler (v4.2.1)
- **Environment**: Poetry + pyenv

## 🚀 Features
- **Aegis Filetree**: Sidebar albero directory collassabile nell'editor con navigazione lazy, highlight del file attivo e persistenza stato in `localStorage`.
- **Aegis Slim-Tech Editor**: Interfaccia di scrittura compattata con supporto **Fullscreen Breakthrough** (bypass automatico dei filtri glass-panel).
- **Native Multi-Tab Navigation**: Pieno supporto per apertura in nuove schede (Ctrl+Click) su Dashboard, File Grid e Breadcrumbs.
- **DaisyUI Tooltips**: Indicatori di funzione ad alta priorità (`z-index: 500+`) coerenti con la stratigrafia industriale.
- **Aegis Render Engine**: Export PNG singolo e ZIP bulk dei diagrammi Mermaid direttamente da file `.md` o dalla toolbar dell'editor.
- **Backend Services Status**: Due pannelli dashboard separati per Gotenberg e Ollama con telemetria real-time (stato, endpoint, modelli chat/embedding).
- **Aegis Oracle (Neural Synthesis)**:
    *   **Ghost-Text (On-Demand)**: Suggerimenti di completamento predittivo (300 tokens) con logica di conclusione frase e supporto per accettazione via [TAB].
    *   **Neural Scan (Auto-Summary)**: Analisi neurale istantanea con Wide-HUD (1200px) e Scan-Overlay protettivo.
    *   **Mermaid Synthesis**: Conversione "Pensiero-Diagramma" via input naturale.
- **Aegis Uplink Config**: Pannello di configurazione globale per la gestione del link neurale e del branding PDF persistito localmente.
- **Global PDF Branding**: Esportazione PDF automatizzata con testata e piè di pagina SC-ARCHIVE (configurabile).
- **Global Discovery**: Search engine integrato per file `.md`, `.html`, e `.pdf`.
- **File Operations**: Gestione completa del buffer (Create, Rename, Delete) con navigazione `UP_DIRECTORY`.

## 📦 Protocollo di Installazione (Setup Manual)

La stazione **SC-ARCHIVE** richiede un ambiente Linux (Ubuntu 24.04 via WSL2 raccomandato) con i seguenti sottosistemi attivi:

### 1. Ambiente Python & Dipendenze
Il progetto utilizza `pyenv` per la gestione delle versioni e `Poetry` per le dipendenze deterministiche.
```bash
# Seleziona la versione corretta via pyenv (scansiona .python-version)
pyenv install $(cat .python-version)
pyenv local $(cat .python-version)

# Installa le dipendenze Aegis via Poetry
poetry install
poetry shell
```

### 2. Kernel di Conversione PDF (Gotenberg)
La generazione PDF è delegata a un'istanza Docker di **Gotenberg**. È mandatorio che il servizio sia attivo sulla porta `3000`.
```bash
# Avvio del motore di conversione
docker run -d -p 3000:3000 gotenberg/gotenberg:8
```

### 3. Strato Neurale (Ollama)
L'intelligenza **Aegis Oracle** richiede Ollama in esecuzione.
- **Installazione**: `curl -fsSL https://ollama.com/install.sh | sh`
- **Modello Consigliato**: `ollama pull qwen2.5-coder:7b`
- **Guida Dettagliata (Ubuntu 24.04)**: Consulta il manuale dedicato [ollama_ubuntu_24_04_guida.md](docs/ollama_ubuntu_24_04_guida.md).

### 4. Compilatore CSS (Tailwind v4)
Il progetto utilizza il binario standalone di Tailwind CSS v4 per la compilazione JIT degli asset. Assicurati che il file `./tailwindcss` sia eseguibile:
```bash
chmod +x tailwindcss
```

## 🚀 Sequenza di Avvio (Boot Sequence)

Per inizializzare la stazione e attivare tutti i watcher (Tailwind & Uvicorn):
```bash
./bin/launch.sh
```

## 📂 Struttura del Progetto
- `main.py`: Punto di convergenza dei router Aegis.
- `logic/`: Logica di business (File management, Conversion, Oracle).
- `templates/components/`: Frammenti HTML/HTMX industriali.
- `static/css/`: Sorgenti e output del design system Aegis.
- `docs/`: Database di documentazione operativa e tecnica.

---
*Progettato per i narratori della stazione SC-ARCHIVE.*
