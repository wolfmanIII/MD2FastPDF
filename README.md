# SC-ARCHIVE // Spacecraft Documentation Management System

> [!NOTE]
> **MD2FastPDF** is the internal technical name for the project core and backend services. **SC-ARCHIVE** is the external station designation and branding.

**SC-ARCHIVE** is an "Aegis Class" documentation management system designed for operational speed and professional PDF generation via the **Gotenberg** infrastructure.

## 🛠 Tech Stack
- **Core**: Python 3.12 + FastAPI
- **Frontend**: HTMX + Tailwind CSS v4 + Jinja2
- **Editor**: EasyMDE (CodeMirror 5)
- **PDF Engine**: Gotenberg (Chromium via Docker)
- **Optimizer**: Aegis Table Fix (Recursive Python Suite)
- **Environment**: Pipenv

## 🚀 Features
- **Aegis Theme**: "Spacecraft" interface with Neon Cyan accents and Holocron system logo.
- **Global Discovery**: Integrated recursive search engine for `.md`, `.html`, and `.pdf` files.
- **Aegis Visualization**: Support for **Mermaid.js** diagrams (Flowcharts, Sequence, Gantt) in Markdown.
- **Multiformat Browser**: Native viewing for Markdown, HTML (External Tab), and PDF (Aegis Preview).
- **Terminal Matrix**: Integrated CPU/Memory monitoring and calibrated HUD radar (45s cycle).
- **Aegis Transitions**: Smooth `scan-in` and `soft-exit` animations for a "no-blink" experience.
- **PDF HUD**: Export with headers, footers, and automatic page numbering.
- **Root Selector**: Dynamic working directory selection with intelligent redirect.

## 📦 Installation
1. Ensure you have `pipenv` installed.
2. Clone the repository.
3. Install dependencies:
   ```bash
   pipenv install
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
