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

## 📦 Installation
1. Ensure you have `pyenv` and `poetry` installed.
2. Clone the repository.
3. Install dependencies:
   ```bash
   poetry install
   ```
4. Start the Gotenberg infrastructure (requires Docker):
   ```bash
   docker run -d -p 3000:3000 gotenberg/gotenberg:8
   ```
5. Run the application:
   ```bash
   ./bin/launch.sh
   ```

## 📂 Project Structure
- `main.py`: FastAPI application entry point.
- `logic/`: Business logic (file management, conversion).
- `templates/`: HTMX fragments and Jinja2 layouts.
- `static/`: CSS assets and Tailwind configurations.

---
*Designed for the narrators of the SC-ARCHIVE station.*
