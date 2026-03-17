# Stato del Progetto: MD2FastPDF
**Stato Attuale**: Funzionale / Versione 1.0
**Ultimo Aggiornamento**: 17 Marzo 2026

## 1. Funzionalità Implementate

### 1.1 Gestione File
- Navigazione filesystem locale con breadcrumbs dinamici.
- Operazioni di lettura e scrittura asincrona di file Markdown.
- Sistema di icone SVG per la distinzione tra file e directory.
- Pulsante di eliminazione sicura (Purge) con interazione visiva.

### 1.2 Editor Markdown
- Integrazione di EasyMDE con supporto Side-by-Side.
- Syntax highlighting personalizzato via CodeMirror (tematizzato dark).
- Supporto per la modalità Fullscreen con gestione del contenitore genitore.
- Anteprima in tempo reale sincronizzata.

### 1.3 Esportazione PDF
- Integrazione con microservizio Gotenberg via Docker.
- Generazione asincrona di file PDF professionali.
- Anteprima PDF integrata nell'interfaccia tramite elemento `<object>`.
- Foglio di stile dedicato alla stampa (Print-Friendly) distinto dal tema dell'app.

## 2. Note di Design e UX
- **Stile Visivo**: Tema dark basato su Tailwind v4 con effetti di trasparenza (Backdrop Blur).
- **Iconografia**: Libreria di icone SVG modulari e riutilizzabili.
- **Interattività**: HTMX per aggiornamenti atomici del DOM senza ricaricamento pagina.
- **Tipografia**: Utilizzo di font Rajdhani per interfacce tecniche e Inter per i documenti finali.

## 3. Infrastruttura Tecnica
- **Linguaggio**: Python 3.12.
- **Framework**: FastAPI (Backend), HTMX (Frontend).
- **Ambiente**: Pipenv per la gestione delle dipendenze.
- **Render Engine**: Gotenberg (Chromium-based).

---
*Stato finale del progetto alla data odierna.*
