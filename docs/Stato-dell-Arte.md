# Stato del Progetto: MD2FastPDF
**Stato Attuale**: Funzionale / Versione 1.1 (Aegis Protocol)
**Ultimo Aggiornamento**: 18 Marzo 2026

## 1. Funzionalità Implementate

### 1.1 Gestione File & Dashboard
- Navigazione filesystem locale con breadcrumbs dinamici.
- Dashboard telemetrica con monitoraggio CPU/Memoria e log frammenti recenti.
- Operazioni di creazione e scrittura asincrona.
- Sistema di eliminazione sicura (Purge) con modale.

### 1.2 Editor Markdown (Aegis Edition)
- **Stabilità Visiva**: Colori del tema scuro caricati globalmente per eliminare il "flash bianco" iniziale.
- **Toolbar Corretta**: Integrazione Font Awesome 4.7.0 per il ripristino delle icone.
- **Layout Flessibile**: Rimosse le costrizioni di altezza fissa; l'editor ora segue lo scrolling naturale della pagina, evitando doppie barre di scroll.
- **Wrap del Testo**: Attivato `lineWrapping` per mantenere il testo confinato nel pannello.
- **Fullscreen Fix**: Gestione dinamica dei filtri CSS per supportare la modalità a schermo intero senza clipping.

### 1.3 Esportazione PDF
- Integrazione con microservizio Gotenberg.
- Generazione asincrona e anteprima integrata.
- CSS dedicato alla stampa (Inter, grayscale) indipendente dal tema dell'app.

## 2. Bug Noti & Criticità (Da Risolvere)
- [!] **Espansione Layout**: Navigando dalla Dashboard direttamente ad un file nell'Editor, il contenitore tende ad allargarsi orizzontalmente oltre i limiti previsti. Necessita di un ricalcolo delle dimensioni post-swap HTMX.

## 3. Infrastruttura Tecnica
- **Backend**: FastAPI (Python 3.12).
- **Frontend**: HTMX, Tailwind v4, DaisyUI, Font Awesome.
- **Container**: Gotenberg (Chromium-based PDF Engine).

---
*Fine sessione. Sistema stabilizzato, ma con bug di layout navigazione attivo.*
