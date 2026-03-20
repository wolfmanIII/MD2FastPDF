# CHANGELOG: SC-ARCHIVE
Tutte le modifiche degne di nota a questo progetto saranno documentate in questo file.

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

## [2.1.0] - AEGIS PROTOCOL STABILIZATION
Miglioramento dell'affidabilità dell'interfaccia.

### Added
- **EasyMDE Fullscreen**: Supporto completo per la modalità a schermo intero con fix dello Z-index (99999).
- **Z-Index Breakout**: Protocollo per forzare la visibilità dell'editor sopra ogni pannello laterale.
- **Font Correction**: Ripristino delle icone della toolbar (EasyMDE) tramite CDN affidabile.

### Fixed
- **Double Scroll**: Rimosso il conflitto tra le scrollbar dell'editor e del browser.
- **Path Sanitization**: Blindato il sistema contro attacchi di tipo Directory Traversal.

## [1.0.0] - INITIAL DEPLOYMENT (MD2FastPDF)
Rilascio della struttura base del progetto.

### Added
- **FastAPI / HTMX**: Architettura asincrona e stateless.
- **Dashboard**: Monitoraggio risorse (CPU/Memory) e file recenti.
- **Markdown Editor**: Integrazione base di EasyMDE.
- **PDF Preview**: Generazione PDF basilare (ex-WeasyPrint).

---
*Mantenuto dai protocolli Aegis Class System.*
