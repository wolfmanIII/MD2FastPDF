# SC-ARCHIVE // Spacecraft Documentation Management System
**Versione 5.5.2** // SECURITY HARDENING

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
- **Aegis Oracle (Precision v5.2.0)**:
    * **Context Isolation**: Utilizzo di delimitatori `[CONTEXT_START]` per il Ghost-Text, eliminando il fenomeno dell'"eco" e garantendo il completamento delle frasi.
    *   **Broadcast Offline Protocol**: Il sistema comunica lo stato disattivato tramite alert pulsanti (`!! NEURAL_PROTOCOL_OFFLINE !!`) e banner informativi nel modale Mermaid.
    *   **Hardened Scans**: Finestra di contesto a 16.384 token e temperatura 0.3 per riepiloghi tecnici ad alta precisione.
    *   **Surgical Sanitization**: Sanitizzazione chirurgica delle allucinazioni HTML per preservare la struttura HUD.
- **Aegis Uplink Config (v5.0.0)**: Terminale di configurazione centralizzato per la gestione dei parametri operativi (Ollama, Gotenberg, Neural Models) con persistenza locale in `config/settings.json`.
- **Aegis Industrial UI**: Standardizzazione globale di tutti i campi input, select e textarea con estetica terminale pura, dimensioni ottimizzate (12px) e rimozione dei bordi framework.
- **Neural Model Intelligence**: Filtro automatico dei modelli Ollama per escludere i motori di embedding dai menu di chat e sintesi.
- **Dashboard Telemetry 2.0**: Monitoraggio real-time di CPU e Memoria via HTMX (`/stats`) e aggiornamento automatico dello stato servizi al salvataggio della configurazione.
- **Global PDF Branding**: Esportazione PDF automatizzata con testata e piè di pagina SC-ARCHIVE (configurabile via Uplink).

## 🔐 Primo Accesso (Inizializzazione Operatore)

Al **primo avvio**, SC-ARCHIVE crea automaticamente l'utente `admin` con password di default `admin` e il workspace in `~/sc-archive/admin/`.

**Sequenza obbligatoria al primo accesso:**

1. Avvia la stazione: `./bin/launch.sh`
2. Apri il browser su `http://localhost:8000`
3. Effettua il login con `admin` / `admin`
4. Apri **Settings** (icona ingranaggio) → sezione **OPERATOR_ACCESS_KEY**
5. Inserisci `admin` in "Current Key" e la nuova password in "New Key"
6. Clicca **ROTATE_KEY** — da questo momento userai la nuova password

> [!TIP]
> Per scegliere una password di default diversa da `admin` **prima** del primo avvio (quando `config/users.json` non esiste ancora), esporta la variabile d'ambiente prima di lanciare:
> ```bash
> export AEGIS_ADMIN_PASSWORD="la-tua-password"
> ./bin/launch.sh
> ```
> Se `config/users.json` esiste già, questa variabile non ha effetto — usa Settings per cambiare la password.

**Workspace:** ogni utente ha una cartella dedicata in `~/sc-archive/<username>/`. Puoi puntare a qualsiasi altra cartella tramite il **Root Picker** nella dashboard — la scelta viene salvata e ripristinata ad ogni login.

---

## 📦 Protocollo di Installazione (Setup Manual)

La stazione **SC-ARCHIVE** richiede un ambiente Linux (Ubuntu 24.04 raccomandato) con i seguenti sottosistemi attivi:

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
- `logic/`: Logica di business (File management, Conversion, Oracle, Render).
- `routes/`: APIRouter modules (core, archive, editor, pdf, config, oracle).
- `config/`: Package Python — `settings.py` (SettingsManager) + `settings.json` (store persistente).
- `templates/components/`: Frammenti HTML/HTMX industriali.
- `templates/layouts/`: Layout base (`base.html`).
- `static/css/`: Design system Aegis — `output.css`, `editor-aegis.css`, `pdf-industrial.css`, `pdf-preview.css`.
- `docs/`: Database di documentazione operativa e tecnica.

---
*Progettato per i narratori della stazione SC-ARCHIVE.*
