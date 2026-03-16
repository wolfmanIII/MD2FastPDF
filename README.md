# MD2FastPDF // Industrial Markdown Editor

**MD2FastPDF** è un editor Markdown minimalista e potente, progettato per la rapidità operativa e la generazione di PDF professionali tramite l'infrastruttura **Gotenberg**.

## 🛠 Tech Stack
- **Core**: Python 3.12 + FastAPI
- **Frontend**: HTMX + Tailwind CSS v4 + Jinja2
- **Editor**: EasyMDE (CodeMirror)
- **PDF Engine**: Gotenberg (via Docker)
- **Environment**: Pipenv

## 🚀 Caratteristiche
- **Tema Industrial**: Interfaccia dark con accenti violetti, ottimizzata per lunghe sessioni di scrittura.
- **File Explorer**: Navigazione rapida del filesystem locale direttamente dalla dashboard.
- **Side-by-Side Preview**: Anteprima in tempo reale sincronizzata.
- **Salvataggio Atomico**: Implementazione HTMX per salvataggi veloci e non invasivi.
- **Asincronia**: I/O gestito interamente in modo asincrono (`anyio`) per massima reattività.

## 📦 Installazione
1. Assicurati di avere `pipenv` installato.
2. Clona il repository.
3. Installa le dipendenze:
   ```bash
   pipenv install
   ```
4. Avvia l'infrastruttura Gotenberg (richiede Docker):
   ```bash
   docker run -d -p 3000:3000 gotenberg/gotenberg:8
   ```
5. Avvia l'applicazione:
   ```bash
   ./dev.sh
   ```

## 📂 Struttura del Progetto
- `main.py`: Entry point dell'applicazione FastAPI.
- `logic/`: Logica di business (gestione file, conversione).
- `templates/`: Fragment HTMX e layout Jinja2.
- `static/`: Asset CSS e configurazioni Tailwind.

---
*Progettato per i narratori di mondi digitali.*
