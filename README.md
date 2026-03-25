# SC-ARCHIVE // Spacecraft Documentation Management System
**Versione 4.2.0** // AEGIS PROTOCOL (Neural Interface)

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
- **Environment**: Pipenv / Poetry

## 🚀 Features
- **Aegis Slim-Tech Editor**: Interfaccia di scrittura compattata (Inconsolata 300) per una densità d'informazione aeronautica e zero distrazioni (no highlight sx).
- **DaisyUI Tooltips**: Tutti i comandi della stazione sono ora dotati di indicatori di funzione neon-styled per un'esperienza industriale moderna.
- **Aegis Oracle (Neural Synthesis)**:
    *   **Ghost-Text (On-Demand)**: Suggerimenti di completamento predittivo attivabili manualmente via pulsante `fa-magic`. Supporto per interruzione immediata via [ESC].
    *   **Neural Scan (Auto-Summary)**: Analisi neurale istantanea e debriefing tecnico dei documenti direttamente dal browser dell'archivio.
    *   **Mermaid Synthesis**: Conversione "Pensiero-Diagramma" via input naturale.
- **Aegis Uplink Config**: Pannello di configurazione globale per la gestione del link neurale e del branding PDF persistito localmente.
- **Global PDF Branding**: Esportazione PDF automatizzata con testata e piè di pagina SC-ARCHIVE (configurabile).
- **Global Discovery**: Search engine integrato per file `.md`, `.html`, e `.pdf`.
- **File Operations**: Gestione completa del buffer (Create, Rename, Delete) con navigazione `UP_DIRECTORY`.

## 📦 Protocollo di Installazione (Setup Manual)

La stazione **SC-ARCHIVE** richiede un ambiente Linux (Ubuntu 24.04 via WSL2 raccomandato) con i seguenti sottosistemi attivi:

### 1. Ambiente Python & Dipendenze
Il progetto utilizza `Pipenv` per la gestione dell'isolamento.
```bash
# Installa Pipenv se non presente
pip install pipenv

# Clona e installa le dipendenze Aegis
git clone <repository_url>
cd MD2FastPDF
pipenv install
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
