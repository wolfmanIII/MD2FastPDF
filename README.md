# SC-ARCHIVE // Spacecraft Documentation Management System
**Versione 4.0.0-BETA** // AEGIS ORACLE (Neural Patch)

> [!NOTE]
> **MD2FastPDF** is the internal technical name for the project core and backend services. **SC-ARCHIVE** is the external station designation and branding.

**SC-ARCHIVE** is an "Aegis Class" documentation management system designed for operational speed and professional PDF generation via the **Gotenberg** infrastructure.

## 🛠 Tech Stack
- **Core**: Python 3.13+ + FastAPI
- **Frontend**: HTMX + Tailwind CSS v4 Standalone CLI (v4.2.1) + Jinja2
- **Editor**: EasyMDE (CodeMirror 5)
- **PDF Engine**: Gotenberg (Chromium via Docker)
- **CSS Optimizer**: Tailwind CSS Standalone Compiler (v4.2.1)
- **Environment**: Poetry (with pyenv)

## 🚀 Features
- **Aegis Slim-Tech Editor**: Interfaccia di scrittura compattata (Inconsolata 300) per una densità d'informazione aeronautica e zero distrazioni (no highlight sx).
- **Global Discovery**: Integrated recursive search engine for `.md`, `.html`, and `.pdf` files.
- **Aegis Visualization**: Support for **Mermaid.js** diagrams (Flowcharts, Sequence, Gantt) in Markdown.
- **Neural Synthesis // AEGIS ORACLE**: Integrated AI layer (Local Ollama) for instant Mermaid diagram generation and automated document analysis.
- **HUD_PRINT Toggle**: PDF export in slim mode (page number only) or full HUD mode (SC-ARCHIVE header/footer).
- **File Operations**: Create, rename, and delete files directly from the archive browser.
- **UP_DIRECTORY Navigation**: One-click parent directory access in the file browser.
- **Aegis UI Normalization**: Standardized form controls based on DaisyUI architecture for surgical layout precision.
- **Root Selector**: Dynamic working directory selection with intelligent redirect.

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
