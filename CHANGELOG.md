# CHANGELOG: SC-ARCHIVE
Tutte le modifiche degne di nota a questo progetto saranno documentate in questo file.

## [3.9.5] - AEGIS OFFLINE READY (2026-03-22)
Migrazione totale dell'infrastruttura verso l'isolamento locale per garantire operatività senza connessione internet.

### Added
- **Aegis Local Isolation**: Tutte le dipendenze (HTMX, DaisyUI, Marked, Highlight.js, Mermaid, EasyMDE, FontAwesome) sono ora servite localmente da `static/js` e `static/css`.
- **Slim-Tech Editor Evolution**: Migrazione del nucleo di scrittura a **Inconsolata 300** (Narrow & Thin) per una densità d'informazione aeronautica.
- **FontAwesome Recovery**: Ripristinato il database glifi locale (`static/webfonts/`) per la navigazione offline 100%.

### Fixed
- **Aegis Visual Sync**: Risolta la divergenza cromatica tra editing e preview tramite mappatura CSS dedicata (Style Parity Protocol).
- **Aegis Horizon Cleanup**: Rimossa la barra di scorrimento orizzontale "fantasma" tramite `lineWrapping` e soppressione mirata CSS.
- **Aegis Core Restore**: Risolto il bug della toolbar tagliata e delle barre verticali parassite causate da overflow eccessivo.
- **Branding Refresh**: Rebranding del footer in "CORE SERVICES" per bilanciare la gerarchia visiva con l'header "AEGIS CLASS".
- **Telemetry Optimization**: Ridotto a 5 il numero di frammenti recenti caricati nella dashboard per un cockpit più asciutto.
- Ottimizzato il protocollo di rendering PDF per includere Highlight.js anche nei documenti esportati (CDN fallback per Gotenberg).
- Risolto il problema del "Shell Nesting" (duplicazione header/footer) tramite filtraggio `HX-Request` nella rotta dashboard.

## [3.9.4] - AEGIS MODULAR ARCH (2026-03-22)

### Added
- **Aegis Sky Palette**: Nuova gamma cromatica Sky/Azure per migliorare leggibilità e contrasto nei sistemi di cockpit editoriale.
- **Mermaid Sync (Deep Editor)**: Integrazione dinamica dei grafici nel preview di EasyMDE e Pure Editor con debouncing (250ms).
- **Aegis Lumina Protocol**: Addio ai neri assoluti per una migliore profondità degli spazi di lavoro (Slate-Space).

### Fixed
- Risolto il bug di invisibilità dei grafici in Side-by-Side tramite protocollo di inizializzazione forcing.
- Pipeline PDF stabilizzata con `waitDelay` ricalibrato a 5s per diagrammi complessi.

## [3.9.0] - AEGIS VISUALIZATION (2026-03-21)
- **Aegis Visualization**: Supporto nativo per diagrammi Mermaid (Flow, Seq, Gantt).
- **Async Export Protocol**: Sincronizzazione con Gotenberg (waitDelay 3s) per export PDF coerente.
- **Auto-Transform**: Protocollo JS per la conversione dinamica dei blocchi di codice Markdown in vettoriali.

## [3.5.0] - AEGIS DISCOVERY (2026-03-21)
Introduzione del motore di ricerca globale e supporto multiformato per l'Archivio Dati.

### Added
- **Global Search Engine**: Ricerca ricorsiva ad alta velocità per file `.md`, `.html` e `.pdf` nel Data Archive con HUD dedicato.
- **Multiformat Support**: Supporto nativo per la visualizzazione di file HTML (apertura scheda) e PDF (preview Aegis integrata).
- **Auto-Discovery**: Indicizzazione automatica dei contenuti testuali per ricerca contestuale.

### Fixed
- **UI Nesting Bug**: Risolto il bug di ricorsione nei componenti breadcrumb (glitch matrioska visuale).
- **Search Alignment**: Perfezionamento millimetrico del modulo di ricerca Aegis e centratura placeholder.
- **Storage Stats**: Risolto errore `TypeError` nel calcolo delle statistiche di storage dovuto a errata rimozione di codice durante il refactoring.

## [3.1.0] - AEGIS SECURITY HARDENING (2026-03-20)
Rafforzamento dei protocolli di sicurezza e stabilità del sistema "Aegis Class".

### Added
- **Sanitizzazione XSS (HTML Node)**: Integrazione di `bleach` nella pipeline di conversione PDF per bloccare l'iniezione di script malevoli via Markdown.

### Changed
- **System Stability**: Rimozione delle procedure di soppressione errori (`except: pass`) in favore della trasparenza dei guasti nel kernel dell'applicazione.

### Fixed
- **Compliance Protocol**: Allineamento completo alle `CODING GUIDELINES` del sistema SC-ARCHIVE.

## [3.0.0] - SC-ARCHIVE RELEASE (2026-03-18)
Identità finale "Spacecraft Documentation Management System".

### Added
- **Logo & Favicon**: Integrazione dell'icona **Holocron** (SVG vettoriale) con bagliore neon.
- **Micro-animazioni**: Radar di sistema (0.022Hz) nel pannello `SYSTEM_STATUS`.
- **Aegis Transitions**: Animazioni di `scan-in` e `soft-exit` per tutte le finestre modali.
- **UX Workflow**: Reindirizzamento automatico al File Browser dopo la selezione della directory radice.

### Changed
- **Branding**: Ridenominazione completa da `MD2FastPDF` a `SC-ARCHIVE`.
- **PDF Engine**: Passaggio definitivo a **Gotenberg** (Chromium) per rendering professionale.
- **HUD PDF**: Aggiunta di testata, piè di pagina e numerazione automatica.
- **View Mode**: Forza la visualizzazione PDF in "Fit Width" (`FitH`).

## [3.0.0] - SC-ARCHIVE RELEASE (2026-03-18)
Identità finale "Spacecraft Documentation Management System".

---

### [ARCHIVE_LINK] // LOG_STORAGE
Per i log storici delle versioni del Sistema precedenti alla v3.0.0:
🔍 [Visualizza l'Archivio Storico (v1.0.0-v2.1.0)](docs/archive/CHANGELOG_v1-2.md)

*Mantenuto dai protocolli Aegis Class System.*
