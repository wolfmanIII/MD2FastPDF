# CHANGELOG: SC-ARCHIVE

Tutte le modifiche degne di nota a questo progetto saranno documentate in questo file.

## [5.23.0] - RELAZIONI TIPIZZATE FASE 2 & GRAPH REFINEMENTS (2026-07-26)

Fase 2 delle Relazioni Tipizzate completa (archi tipizzati nel grafo, validazione di
dominio), vocabolario esteso con due relazioni grounded nell'archivio scene reale, il
documento di analisi per la Fase 3 (query NL via Ollama) aperto con 8 issue granulari
di implementazione, e diversi affinamenti/fix alla vista a grafo emersi usandola sui
dati reali della campagna.

### Added

- **Archi tipizzati nella vista a grafo** (RF-8, issue #7): ogni relazione dichiarata nel frontmatter appare come arco colorato e tratteggiato per tipo, con filtro e legenda dedicati nel pannello CONTROLS. Nuovo checkbox **"Seleziona tutte"** per mostrare/nascondere tutte le relazioni tipizzate in un clic (stato indeterminato quando la selezione è parziale).
- **Validazione di dominio delle relazioni** (RF-9, issue #8): `RelationDef.domain`/`range` passano da singolo tipo a tupla di tipi ammessi (derivati dall'uso reale osservato nell'archivio, non progettati a tavolino — es. `owns` ammette `npc→ship|location|drone|item`, `owes_debt_to` ammette `npc|organization` su entrambi i lati). Nuova `DomainViolation`, diagnostica e mai bloccante (coerente con `dangling`/`key_collisions`): un tipo mancante non è mai una violazione, solo un conflitto reale tra due tipi noti lo è.
- **Due nuove relazioni nel vocabolario**, entrambe grounded nell'archivio scene reale (34 file): `npcs` (quali NPC compaiono in una scena, issue #11) e `organizations` (quali organizzazioni/fazioni sono coinvolte, issue #12 — inverso `scenes_org` per evitare la collisione con l'inverso di `npcs`, `VOCABULARY_BY_INVERSE` essendo una mappa 1:1).
- **Archi "deboli" per le menzioni nel corpo del testo** (issue #10): gli archi già estratti da `logic/graph.py` (link Markdown standard `[testo](file.md)`, non `[[wikilink]]` — verificato che quella sintassi non è mai usata per riferimenti a entità nell'archivio reale) sono ora visivamente distinti dagli archi tipizzati nella vista a grafo.
- **Documento di analisi dedicato a RF-11** (`docs/ANALISI-relazioni-query-nl.md`, issue #9): query in linguaggio naturale via Ollama sul `RelationIndex`, con gestione dell'ambiguità (richiesta di disambiguazione), fallback a ricerca testuale quando la traduzione non è valida, e un nuovo slot di modello dedicato `neural_query`. Il piano di implementazione è tracciato in 8 issue granulari (#13-#20).

### Fixed

- **Duplicazione dei nodi nella vista a grafo** tornando indietro col browser dopo aver aperto l'editor da un nodo: HTMX ripristina lo snapshot in cache della pagina grafo e ri-esegue lo script di inizializzazione sopra il DOM esistente, lasciando una simulazione D3 orfana con un gruppo di zoom che non riceve più aggiornamenti (i nodi apparivano "fissi" durante il pan). `init()` ora ferma la simulazione precedente e pulisce l'SVG prima di ricostruire il grafo, rendendola sicura da rieseguire in qualunque condizione.
- **Visibilità degli archi di menzione**: due iterazioni successive dopo feedback sull'uso reale — la dimenticanza iniziale (opacità 0.35, colore zinc-600) risultava "oscurata"; portata a colore zinc-300, spessore pieno, opacità 0.85, distinguendosi dagli archi tipizzati solo per colore/tratteggio.

### Changed

- **Dimensione nodi** della vista a grafo impostata di default al minimo dello slider (0.5×) invece che al centro (1.0×).
- `logic/oracle.py`: estratto `_is_embedding_model()`/`_is_chat_model()` per eliminare la duplicazione del filtro sui modelli di embedding nella classificazione dei modelli Ollama.

## [5.22.0] - DOCKER HARDENING & NEURAL AVAILABILITY GATING (2026-07-25)

Deploy Docker verificato end-to-end e messo in sicurezza (utente non privilegiato, immagini
pinnate, healthcheck), password admin non più prevedibile, e i controlli AI in editor e viste
elenco ora riflettono davvero se il Neural Core è disponibile invece di fallire silenziosamente.

### Added

- **Neural Core Availability Gating**: i pulsanti AI nell'editor (Neural Scan, Mermaid Synthesis, Ghost-Text) e nelle viste elenco (Neural Scan) si disattivano con tooltip "Neural Core disabled or not reachable" quando il toggle è spento o Ollama non risponde — prima restavano sempre attivi e fallivano solo al click. `OracleClient.is_available()` (`logic/oracle.py`) — enabled AND reachable — con cache di 10s per non bloccare il rendering di editor/liste su un probe live a ogni apertura file o cambio cartella.
- **`OracleClient.service_status()`** distingue ora "raggiungibile ma disattivato nelle Impostazioni" (`ONLINE // DISABLED_IN_SETTINGS`, ambra nel pannello dashboard) da un vero problema di rete (`OFFLINE`, rosso) — prima il probe veniva saltato del tutto quando il toggle era spento, rendendo i due casi indistinguibili a vista.
- **`bin/ensure_services.sh`**: bootstrap automatico di Gotenberg e Ollama per lo sviluppo locale — usa un'istanza già attiva (nativa, systemd, o container manuale) se raggiungibile, altrimenti crea un container di progetto dedicato (`md2fastpdf-gotenberg`/`md2fastpdf-ollama`), senza mai toccare installazioni esistenti dell'utente.
- **Container Docker come utente non privilegiato**: `uvicorn` (PID 1) gira ora come utente dedicato `aegis`, non più root. `entrypoint.sh` parte come root solo per sistemare i permessi sui volumi montati (necessario per volumi appena creati o ereditati da un deploy con l'immagine precedente), poi passa il controllo via `gosu` — verificato end-to-end, incluso lo scenario di migrazione da un volume con dati preesistenti di proprietà di root.
- **Immagini Docker pinnate per digest** (multi-arch, arm64 incluso): `debian:bookworm-slim`, `python:3.13-slim`, `gotenberg/gotenberg:8`, `caddy:alpine` — build riproducibili, niente più versioni diverse silenziosamente tirate giù in rebuild a distanza di tempo.
- **Healthcheck su `sc-archive` e `gotenberg`** in `docker-compose.yml`, con `depends_on: condition: service_healthy` — `sc-archive` attende che Gotenberg sia pronto, `caddy` attende che `sc-archive` lo sia, eliminando errori di conversione PDF nei primissimi secondi dopo l'avvio.
- **Verifica checksum del binario Tailwind** (`sha256sum -c`) nello stage `css-builder` del Dockerfile, invece di eseguirlo non verificato dopo il solo download HTTPS.
- **`docs/configurazione-docker.md`** (rinominata da `docker-raspberry.md`): generalizzata a qualsiasi host Docker, non solo Raspberry Pi — nuova checklist completa "Ollama in rete" (IP corretto, binding, firewall, tranello proxy/"could not resolve host") e sezione su come risalire dal nome di un volume Docker al percorso reale su disco.
- **README**: nuova sezione "Documentazione di Configurazione" con link diretti a tutte le guide di setup, sia bare-metal che Docker.

### Fixed

- **Password admin debole di default**: `bootstrap_admin()` non ricade più su `"admin"` se `AEGIS_ADMIN_PASSWORD` non è impostata — genera una password casuale (`secrets.token_urlsafe`) e la salva in `~/.config/sc-archive/admin_password.txt` (permessi `600`), non solo nei log. Rimosso anche il fallback debole equivalente in `docker-compose.yml`.
- **Persistenza della libreria Blueprint in Docker**: `blueprints/` non veniva copiato nell'immagine né montato come volume — ogni `docker compose up -d --build` cancellava i blueprint creati dagli utenti. Aggiunto volume dedicato, popolato dai template di default al primo avvio.
- **Modale di creazione file in Group Space**: non si chiudeva mai dopo una creazione riuscita — mancava l'`hx-on::after-request` presente invece nel modale equivalente dell'Archive principale.
- **Testo poco leggibile** in editor, modali e pannelli: ~25 punti in 20 template usavano grigio scuro (`zinc-500/600/700`) per messaggi di stato, stati vuoti ed etichette di campo, portati a `zinc-100/200/300`.
- **Due bug preesistenti nel build Docker**, mai emersi perché l'immagine non era mai stata buildata realmente in locale: mancava `ca-certificates` nello stage `css-builder` (curl falliva su HTTPS scaricando Tailwind) e veniva copiato solo `main.css` invece di tutta `static/css/` (mancava `daisyui.min.css`, importato da `main.css`).
- **`ensure_services.sh`**: fallimento immediato con messaggio chiaro se `docker run`/`start` fallisce, invece di attendere ~20s per poi segnalarlo in modo generico.

## [5.21.0] - RELAZIONI TIPIZZATE (2026-07-25)

Fase 1 (MVP) completa: relazioni strutturate nel frontmatter YAML, query dirette/inverse,
indice live per-root, endpoint HTTP, pannello RELAZIONI nell'editor.

### Added

- **`logic/relations.py`**: vocabolario dichiarativo (`VOCABULARY`) di 9 tipi di relazione riconosciuti nel frontmatter — 5 iniziali (`crew`, `member_of`, `located_in`, `hostile_to`, `owns`) più 4 emersi da un'analisi del materiale di campagna reale (`owes_debt_to`, `reports_to`, `allied_with`, `mentor_of`). Ogni `RelationDef` ha un'etichetta diretta e una inversa distinte per il pannello UI. `FrontmatterRelationParser` estrae gli archi da un file, ignorando silenziosamente le chiavi fuori vocabolario — nessun errore, retrocompatibile con frontmatter già in uso. `canonical_key`/`strip_wikilink` normalizzano i riferimenti (case-insensitive, spazi multipli collassati, `[[wikilink]]` tollerati ma non richiesti).
- **`logic/relations_index.py`**: `RelationIndex` + `RelationIndexBuilder` — costruzione a due passaggi (popola prima le entità, poi risolve gli archi, perché un file può referenziarne un altro non ancora letto), query dirette e inverse (`related`/`relations_of` — la query inversa non richiede alcuna dichiarazione sul lato target), `diagnostics()` (riferimenti dangling, collisioni di chiave tra file con lo stesso nome, warning di parsing), `reindex_file()` incrementale (nessuna scansione completa dell'archivio a ogni modifica).
- **`logic/relations_service.py`**: `RelationGraphService` — un `RelationIndex` live per root archivio attiva, mai un singleton globale condiviso (la root è per-utente, un cache unico mescolerebbe archivi diversi).
- **`routes/relations.py`**: `GET /api/entities/{key}/relations[/{relation}]`, `GET /api/diagnostics/relations`, `POST /api/index/reindex`, `GET /relations/panel` (fragment HTML server-renderizzato per l'editor).
- **Sezione RELAZIONI nell'editor**: sidebar destra lazy-loaded via HTMX (stesso pattern del filetree), mostra le relazioni dichiarate e quelle inverse con etichetta leggibile in italiano.
- Reindex incrementale agganciato a salvataggio, rinomina e cancellazione file — mai una scansione completa dell'archivio in risposta a una singola modifica.
- **`docs/guida-relazioni-tipizzate.md`**: guida utente in italiano semplice su come scrivere il frontmatter delle relazioni, senza gergo tecnico.

### Fixed

- **Rendering del frontmatter**: il blocco YAML non compare più come markdown letterale (un `<hr>` seguito da intestazioni spezzate) né nella preview dell'editor, né nel PDF esportato, né nei bookmark PDF generati dai titoli — tutti e tre i punti ora rimuovono il blocco prima di interpretare il testo come Markdown.
- **Evidenziazione sintattica dell'editor**: CodeMirror non interpreta più la riga di chiusura del blocco frontmatter come sottolineatura di un titolo Setext, né lascia testo semplice del blocco nel colore di default.
- **Bug preesistente in `renderAegisVisuals`**: la funzione era definita in uno script posizionato dopo il contenuto della pagina — al reload completo (non via navigazione HTMX) lanciava `ReferenceError`, che a sua volta interrompeva la riscrittura dei percorsi relativi (immagini, link `.md`) nella preview dell'editor.
- **URL-encoding dei percorsi file**: caratteri speciali (`&`, spazi...) nel nome di file o cartelle spezzavano la query string in tutti i link `hx-get`/`href` dell'app (file browser, editor, filetree, group-space, export Mermaid).
- **Etichette inverse**: il pannello RELAZIONI mostrava la stessa etichetta in entrambe le direzioni (es. "Equipaggio" anche sul file bersaglio); ogni relazione ha ora un'etichetta propria per il verso inverso ("Equipaggio di", "Subordinati", "Posseduto da"...).

## [5.20.0] - AEGIS GRAPH VIEW & REBRANDING (2026-07-11)

Vista a grafo per l'archivio, nuovo logo/favicon, header rinnovato.

### Added

- **`logic/graph.py` — `ArchiveGraphBuilder`**: classe SRP che deriva un grafo nodi/archi dai link Markdown (`[testo](path.md)`) trovati nell'archivio dell'utente attivo. Scan ricorsivo confinato alla root utente (`PathSanitizer.get_root()`), risoluzione e sanitizzazione di ogni link (traversal, path nascosti, file inesistenti o URL esterni scartati silenziosamente). Nessuna eccezione mai propagata.
- **`routes/graph.py`**: `GET /graph` (fragment/shell HTMX) e `GET /graph/data` (JSON nodi/archi).
- **`templates/components/graph_view.html`**: force-directed graph D3.js v7 (vendorizzato in `static/js/d3.min.js`), zoom/pan/drag, click-to-open sull'editor via HTMX. Pannello **CONTROLS** live: ricerca testuale (dimming), toggle nascondi orfani e frecce direzionali, 6 slider (dimensione nodi, spessore linee, forza di repulsione, distanza collegamenti, forza collegamenti, dissolvenza testi su zoom). Colorazione nodo per cartella padre (`d3.scaleOrdinal` + `schemeTableau10`), dimensione nodo proporzionale al grado, hover highlight su nodo + vicini diretti. Forze di centraggio deboli (`forceX`/`forceY`) per tenere il grafo nel viewport a qualunque intensità di repulsione.
- Nuova voce nav **GRAPH** nel dropdown MODULES.
- **`static/logo.png`**: logo esagonale con trasparenza vera (sfondo bianco rimosso da `static/logo.jpg` via flood-fill dai bordi + erosione 1px, non una soglia globale — preserva i riflessi chiari interni al disegno). Usato nell'header al posto dell'icona diamante placeholder.
- **`static/favicon/favicon.svg`**: icona vettoriale semplificata (esagono + freccia, neon-cyan) — il logo completo era illeggibile a 16px. `favicon.ico`/`favicon-16x16.png`/`favicon-32x32.png` rigenerati dal nuovo SVG; `apple-touch-icon.png` (180px) mantiene il logo completo.
- **Badge archivio persistente**: nome della cartella archivio attiva (`GET /root-badge`) visibile nell'header di ogni pagina, non solo in dashboard. Si auto-perpetua ad ogni swap (pattern già usato da `comms-unread-badge`) e ascolta `HX-Trigger: root-updated` emesso da `POST /root-picker/select` per aggiornarsi istantaneamente al cambio directory.
- **Nav MODULES**: Archive/Graph/Library/Comms/Admin raggruppati in un dropdown (`<details>` + `.glass-panel`) per alleggerire la barra di navigazione. Chiusura automatica al click esterno o alla navigazione HTMX.
- **Editor in preview di default**: `easyMDE.togglePreview()` chiamato subito dopo l'init — ogni `.md` si apre mostrando il rendering invece del buffer grezzo.
- **`DENSITY_CAPACITY`**: soglia della barra di utilizzo storage in dashboard alzata da 100 MB a 10 GB (`STORAGE_CAPACITY_BYTES` in `logic/files.py`); aggiunto il livello GB alla formattazione di `ARCHIVE_SIZE`.

### Changed

- **Header**: logo da 36px a 96px, header alzato a 128px per farci spazio. Layout a due righe: logo + "SC-ARCHIVE" a sinistra con stato SYS_ACTIVE/tagline sotto; MODULES/USERNAME/LOGOUT a destra con badge archivio sotto, allineati a destra.
- **`bin/launch.sh`**: watcher Tailwind avviato con `--watch=always` invece di `--watch` — senza `always` il processo si ferma silenziosamente appena stdin si chiude, condizione sempre vera in esecuzione non interattiva (systemd `--user`, nessun TTY). Il CSS non veniva più ricompilato dopo l'avvio del servizio.

### Fixed

- **`root_badge.html`**: mancavano `id`/attributi `hx-*` sul proprio elemento radice — al primo swap (`load`) l'elemento sostituiva se stesso con uno privo di `hx-trigger`, perdendo polling e ascolto di `root-updated` per sempre. Serviva ricaricare la pagina per vedere la nuova directory.
- **Repulsione grafo senza effetto visibile**: senza vincolo di centraggio, aumentare "Forza di repulsione" spingeva i nodi fuori dall'area visibile invece di allargarli a vista. Aggiunte forze `forceX`/`forceY` deboli per tenere il grafo centrato nel viewport.
- **Header visibile durante il fullscreen dell'editor**: leak di stacking-context (backdrop-filter dell'header) reso molto più visibile dall'header ingrandito — nascosto esplicitamente via `body:has(.aegis-fullscreen-active) header`.
- **`apple-touch-icon`**: puntava erroneamente a `favicon.svg` invece che a un PNG dedicato.

---

## [5.16.0] - PDF BOOKMARK INJECTION (2026-06-27)

Outline PDF gerarchico iniettato automaticamente su ogni esportazione.

### Added

- **`logic/conversion.py` — `PdfOutlineInjector`**: classe SRP per l'iniezione di outline PDF dopo la conversione Gotenberg. Estrae heading `#`–`######` dal Markdown sorgente, li sanitizza (rimozione inline Markdown), localizza la pagina tramite `pypdf` text extraction, calcola la coordinata Y in PDF user space via CTM×TM (`y_pdf = um[1]*tm[4] + um[3]*tm[5] + um[5]`), inietta l'outline gerarchico con `PdfWriter.add_outline_item()` e `Fit.xyz`. Fallback silenzioso: se l'injection fallisce, restituisce il PDF originale senza eccezioni.
- **`logic/conversion.py` — `GotenbergClient`**: accetta `outline_injector: Optional[PdfOutlineInjector]` nel costruttore (DIP). `render_pdf()` invoca `inject()` sull'output Gotenberg prima di restituirlo.
- **`logic/conversion.py` — `MarkdownRenderer`**: aggiunta extension `toc` alla lista `markdown.markdown()`.
- **`pyproject.toml`**: aggiunta dipendenza `pypdf (>=4.0.0,<5.0.0)`.
- **`docs/spec-pdf-bookmarks.md`**: specifica implementativa completa del PDF Outline Protocol.

---

## [5.15.0] - AEGIS UX REFINEMENTS (2026-06-19)

Metadati temporali nell'archive browser e sidebar filetree editor ridimensionabile.

### Added

- **`logic/files.py` — `DirectoryLister.list_contents()`**: ogni item (file e directory) ora espone `mtime_str` e `ctime_str` formattati `DD/MM/YYYY HH:MM`. Usa `st_birthtime` se disponibile (macOS/BSD e filesystem Linux con supporto); fallback a `st_ctime` (inode change time) su ext4/xfs.
- **`logic/files.py` — `DirectoryLister.search()`**: stessa logica applicata ai risultati di ricerca ricorsiva.
- **`templates/components/results_grid.html`**: date di creazione e modifica mostrate sotto il nome file/directory come sottotitolo inline (`CRE ... // MOD ...`), visibili da viewport `lg`. Font mono, label `text-zinc-500`, valori `text-(--neon-cyan)`.
- **`static/css/editor-aegis.css` — `#aegis-filetree-resizer`**: handle drag (4px, `cursor: col-resize`) tra sidebar e editor. Glow neon-cyan al hover e durante il drag. Classe `.no-transition` su `#aegis-filetree` per disabilitare la transizione CSS durante il resize.
- **`templates/components/editor.html`**: `<div id="aegis-filetree-resizer">` inserito tra `#aegis-filetree` e il form editor. Logica drag nell'IIFE filetree — `mousedown`/`mousemove`/`mouseup` sul `document`. Larghezza min 120px / max 600px. Persistenza in `localStorage` (`aegis-filetree-width`); ripristino al reload. Handle nascosto quando la sidebar è collassata, visibile all'apertura.

---

## [5.14.0] - DOCKER RASPBERRY PI DEPLOY (2026-04-23)

Stack containerizzato completo per Raspberry Pi 4/5 (ARM64). Build multi-stage con risoluzione automatica del binario Tailwind per architettura.

### Added

- **`Dockerfile`**: Build multi-stage in 3 fasi — `css-builder` (compila Tailwind su `$BUILDPLATFORM`, scarica binario `arm64` o `x64` da GitHub in base a `$BUILDARCH`), `deps-builder` (Poetry 2.3.2 + `poetry-plugin-export`, venv isolato), `runtime` (`python:3.13-slim` + `openssl`). Nessun binario `tailwindcss` nel contesto build.
- **`docker-compose.yml`**: Tre servizi — `sc-archive` (build .), `gotenberg/gotenberg:8`, `caddy:alpine`. Tre named volumes: `sc-archive-config` (`/app/config`), `sc-archive-userdata` (`/root/.config/sc-archive`), `sc-archive-workspaces` (`/root/sc-archive`). Caddy espone la porta `80` sulla LAN.
- **`docker/entrypoint.sh`**: Inizializza `config/settings.json` con valori Docker (`gotenberg_ip: http://gotenberg:3000`, `ollama_ip: $OLLAMA_IP`, `workspace_base: /root/sc-archive`). Genera session key via `openssl rand -hex 32` se assente. Bootstrap admin con `AEGIS_ADMIN_PASSWORD`.
- **`docker/Caddyfile`**: `http://sc-archive.lan:80 { reverse_proxy sc-archive:8000 }`. Variante IP diretto documentata.
- **`docker/.env.example`**: Template con `AEGIS_ADMIN_PASSWORD` e `OLLAMA_IP`.
- **`.dockerignore`**: Esclude `.git`, `__pycache__`, `.venv`, `tests/`, `docs/`, `static/css/output.css`, `config/settings.json`, binario `tailwindcss`.
- **`docs/docker-raspberry.md`**: Guida operativa completa — architettura, prerequisiti Docker sul Pi, installazione step-by-step, DNS LAN, primo avvio, volumi, configurazione Ollama esterno, aggiornamento, gestione container, troubleshooting.

### Change

- **`docs/rete-lan-caddy.md`** (rinominato da `rete-lan-caddy-wsl2.md`): Aggiunto Scenario B (SC-ARCHIVE su RPi, Gotenberg/Ollama esterni) e Scenario C (SC-ARCHIVE su PC Linux → Caddy su RPi). Nota esplicita che nel deploy Docker su RPi Gotenberg e Ollama sono servizi separati non installati sul Pi stesso.

---

## [5.13.0] - AEGIS BLUEPRINT VARIABLE INJECTION (2026-04-12)
Pre-compilazione guidata dei placeholder `[UPPERCASE]` nei blueprint prima dell'inserimento in editor.

### Added
- **`routes/blueprint.py` — `GET /blueprints/placeholders?path=`**: estrae i placeholder univoci dal contenuto del blueprint via regex `\[[A-Z0-9 _/\.]+\]`. Deduplicazione con `dict.fromkeys` (ordine di prima occorrenza). Restituisce `{"placeholders": [...]}`.
- **`templates/components/blueprint_variable_modal.html`**: nuovo fragment modale con form dinamico — un `<input>` per ciascun placeholder rilevato, label uppercase, focus automatico sul primo campo. Azioni: `ABORT //` e `INJECT_BLUEPRINT //`.

### Changed
- **`templates/components/blueprint_modal.html`**: click su blueprint chiama `requestBlueprint(path)` invece di `insertBlueprint(path)` diretto. Se i placeholder sono presenti, il blueprint modal si chiude e si apre `blueprint_variable_modal`; altrimenti inserimento diretto invariato. Incluso `blueprint_variable_modal.html` via `{% include %}`.

---

## [5.12.0] - AUTH HARDENING + COMMS ADMIN BYPASS + UI FIXES (2026-04-10)
Hardening dell'autenticazione (path dinamici, ISP split, secret key persistente), bypass gruppi per admin in COMMS, fix palette filetree, fix blueprint admin.

### Security / Breaking
- **`AEGIS_SECRET_KEY`** è ora **obbligatoria** — `os.environ["AEGIS_SECRET_KEY"]` senza fallback. Se assente, l'avvio fallisce immediatamente. `bin/launch.sh` genera e persiste la chiave in `~/.config/sc-archive/session.key` tramite `openssl rand -hex 32` (solo al primo avvio).
- **`auth_middleware`** cattura solo `AegisError` (non `except Exception`) — gli errori di programmazione non vengono più inghiottiti silenziosamente.

### Added
- **`logic/auth.py` — `_migrate_legacy_users()`**: Migrazione automatica a module-load. Sposta `config/users.json` → `~/.config/sc-archive/users.json` con merge (record legacy vincono su eventuali placeholder bootstrap). Elimina il file legacy dopo la migrazione.
- **`logic/auth.py` — `SyncUserStoreProtocol`**: Nuovo Protocol ISP-compliant per i path sync (bootstrap/CLI). `AuthService.__init__` ora accetta `sync_store: SyncUserStoreProtocol` separato da `store: UserStoreProtocol` — i consumer async non sono esposti ai metodi sync.

### Changed
- **`logic/auth.py` — `AuthService._default_root`**: Usa `Path.home() / "sc-archive" / username` calcolato a runtime. Rimossa ogni dipendenza da `settings.json` per il path utente — funziona cross-PC senza modificare la configurazione.
- **`logic/auth.py` — `GroupStore._group_workspace`**: Stessa correzione — `Path.home() / "sc-archive" / name`. Eliminato il crash di avvio causato da `workspace_base` hardcoded su altra macchina.
- **`config/settings.json`**: Rimosso il campo `workspace_base` — era un path assoluto di un'altra macchina e causava `PermissionError` all'avvio.
- **`logic/comms.py` — `CommsManager.allowed_recipients()`**: Admin (sender con gruppo `"admin"`) bypassa il filtro gruppi e vede tutti gli utenti. Utenti normali mantengono la restrizione al gruppo condiviso + admin.

### Fixed
- **`templates/components/blueprint_admin.html`**: Collisione virgolette singole nell'attributo `onclick` — usato `{% set bp_slug %}` per pre-calcolare lo slug fuori dall'attributo. Placeholder filename cambiato da `session-log` (nome di un blueprint esistente) a `nome-template`.
- **`templates/components/filetree_node.html`**: Palette icone e testo allineata al file browser — `.md` `neon-text`, `.pdf` icona `text-red-400`, `.html` icona `text-amber-400`. Icone ingrandite a `w-4 h-4`. Transizione folder chiusa/aperta con SVG outline puri (fix FontAwesome `fa-folder-open` parzialmente riempito).
- **`templates/icons/folder-open.html`**: Nuovo SVG outline open folder (Lucide-style, `fill="none"`, `stroke="currentColor"`) per la transizione cartella espansa nel filetree.
- **COMMS labels**: `text-zinc-100 font-bold` su tutte le label di `comms_message_reader.html`, `comms_message_list.html`, `comms_compose_modal.html`. Spaziatura checkbox destinatari aumentata (`gap-3`).

---

## [5.11.0] - UI MODAL STANDARDIZATION + MIGRATION TOOL (2026-04-05)
Standardizzazione uniforme di tutte le modali al design system di riferimento (`blueprint_modal.html`). Aggiunto script di migrazione completo per trasferimento dell'applicazione tra macchine.

### Added
- **`bin/aegis-migrate.sh`**: Script bash per export/import completo dei dati applicazione. Export crea un `.tar.gz` con timestamp contenente `settings.json`, `users.json`, `groups.json`, directory `blueprints/` e directory `workspace_base`. Import interattivo con rimappatura percorsi e aggiornamento automatico di `settings.json`.

### Changed
- **Tutte le modali** (`admin_group_modal.html`, `admin_user_modal.html`, `comms_compose_modal.html`, `create_modal.html`, `delete_modal.html`, `groupspace_create_modal.html`, `mermaid_list_modal.html`, `oracle_mermaid_modal.html`, `rename_modal.html`, `settings_modal.html`): refactoring uniforme allo stile `blueprint_modal.html` — shell `modal-box bg-zinc-900 border border-zinc-700 rounded-none p-0`, header `// TITLE` in `neon-text`/`text-violet-400`, close button ghost, footer `ABORT //` + azione primaria.
- **`templates/components/settings_modal.html`**: larghezza portata a `70vw` via inline style (`style="width:70vw;max-width:70vw;"`) — unico modo affidabile per bypassare il `max-width` hardcoded di DaisyUI `modal-box`. Layout `max-h-[90vh] flex flex-col` con area di scroll interna separata da header e footer fissi.
- **`templates/components/comms_compose_modal.html`**: stessa struttura scroll interna (`max-h-[90vh] flex flex-col`) per accomodare il contenuto esteso (recipients grid, body/preview side-by-side, original signal).

---

## [5.10.0] - REFACTORING STRUTTURALE + BLUEPRINT COMPLETATO (2026-04-05)
Riorganizzazione struttura progetto, completamento funzionalità blueprint (edit admin, accesso da groupspace), rimozione file morto `editor_pure.html`.

### Added
- **`config/settings.default.json`**: Template con valori di default per `settings.json` (inclusa chiave `blueprints_root` configurabile).

### Changed
- **`logic/templates.py` → `config/templates.py`**: Configurazione Jinja2 spostata fuori dal layer business logic.
- **`routes/auth.py` → `routes/login.py`**: Rinominato per evitare ambiguità con `logic/auth.py`.
- **`logic/blueprints.py`**: `BLUEPRINTS_ROOT` costante sostituita da `_blueprints_root()` — path leggibile da `settings.json` (chiave `blueprints_root`), fallback al default di progetto.
- **`templates/components/blueprint_admin.html`**: Campo Category trasformato in `<select>` con categorie esistenti + opzione "nuova categoria" con input libero. Aggiunto bottone EDIT per caricare un blueprint esistente nella form.
- **`templates/components/blueprint_modal.html`**: `insertBlueprint()` usa `window.aegisEditor` (EasyMDE) se disponibile, altrimenti fallback su textarea (`#gs-editor-input` / `#pure-editor-input`).
- **`templates/components/editor.html`**: Aggiunto bottone `BLUEPRINT_ARCHIVE` (`fa-book-open`) nella toolbar EasyMDE.
- **`templates/components/groupspace_editor.html`**: Aggiunto bottone `BLUEPRINT_ARCHIVE` nella toolbar. Fix layout: `#gs-editor-root` ora partecipa alla catena flex (`grow flex flex-col min-h-0`).
- **`routes/admin.py`**: `admin_panel` fetcha blueprints e passa `blueprints` + `categories` al contesto — necessario per il tab blueprint incluso via `{% include %}`.
- **`.gitignore`**: Aggiunto `config/settings.json` (contiene IP/endpoint runtime, non va in repo).

### Removed
- **`templates/components/editor_pure.html`**: File morto — non referenziato da nessun template o route.

### Fixed
- Blueprint non accessibili dal groupspace editor.
- Blueprint non modificabili dal pannello admin.
- Crash `UndefinedError: 'categories' is undefined` su `/admin?tab=blueprints`.

---

## [5.9.1] - AEGIS TEST SUITE: UNIT + ASYNC I/O (2026-04-04)
Suite pytest completa per il layer `logic/`. 170 test, 0 fallimenti. Copertura: `blueprints.py` 100%, `comms.py` 93%, `groupspace.py` 92%.

### Added
- **`tests/conftest.py`**: Fixture condivise — `tmp_workspace`, `patch_groupspace_base`, `patch_blueprints_root`, `patch_comms_base`. Isolamento filesystem via `monkeypatch` + `tmp_path`.
- **`tests/test_auth.py`**: 6 test su `UserRecord.to_dict()` e `UserStore._build_record()` (retrocompatibilità `groups=[]`).
- **`tests/test_blueprints.py`**: 10 test su `BlueprintManager._sanitize()`, `_display_name()`, `group_by_category()`.
- **`tests/test_groupspace.py`**: 15 test su `GroupSpaceAccess` (has_access, can_write, is_read_only) e `GroupSpaceManager.sanitize()`.
- **`tests/test_comms.py`**: 29 test su `FrontmatterParser` (parse/serialize), `MessageRecord.recipients`, `CommsManager.allowed_recipients()`, `_expand_recipients()`, `_slugify()`.
- **`tests/test_blueprints_async.py`**: 14 test async su `BlueprintManager` — list, read, write, delete con fixture filesystem isolato.
- **`tests/test_groupspace_async.py`**: 27 test async su `GroupSpaceManager` — list_contents, read_file, write_file, create_file, delete_file con enforcement permessi.
- **`tests/test_comms_async.py`**: 29 test async su `CommsManager` — create_comms_folders, list_folder, send_message, mark_read, delete_message, count_unread, save_draft, promote_draft.

### Changed
- **`pyproject.toml`**: Aggiunto `[tool.poetry.group.dev.dependencies]` — `pytest >=8.0`, `pytest-cov >=6.0`, `pytest-anyio`. Aggiunto `[tool.pytest.ini_options]` con `testpaths = ["tests"]`.
- **`.gitignore`**: Aggiunti `.coverage` e `htmlcov/`.

---

## [5.9.0] - SOLID REFACTORING: AUTH HOOKS, BLUEPRINT LOGIC, GROUPSPACE TEMPLATE (2026-04-04)
Refactoring SOLID post-feature su moduli recentemente introdotti. Nessuna modifica funzionale.

### Changed
- **`logic/auth.py`**: `AuthService.__init__` ora accetta `sync_group_store: SyncGroupStoreProtocol` — `bootstrap_admin` usa `self._sync_group_store` anziché il globale `_group_store` (DIP fix). Aggiunto `SyncGroupStoreProtocol` (`@runtime_checkable`).
- **`logic/auth.py`**: Rimossi gli import locali di `comms_manager` da `create_user` e `create_user_sync`. Introdotto hook registry (`_user_creation_hooks`, `_user_creation_hooks_sync`) e funzioni `register_user_creation_hook` / `register_user_creation_sync_hook` esportate (SRP fix — AuthService non conosce più CommsManager).
- **`main.py`**: Hook comms registrati a livello di modulo (prima del lifespan) via `register_user_creation_hook` / `register_user_creation_sync_hook` — garantisce che i hook siano attivi prima di `bootstrap_admin()`.
- **`logic/blueprints.py`**: Aggiunto `BlueprintManager.group_by_category()` come `@staticmethod` — logica di trasformazione dati spostata dal layer routes al layer logic (DIP fix).
- **`routes/blueprint.py`**: Rimossa funzione `_group_by_category` locale; tutte le chiamate delegate a `BlueprintManager.group_by_category()`.
- **`routes/groupspace.py`**: `groupspace_save` non restituisce più un `HTMLResponse` con HTML inline; usa `TemplateResponse` su `components/groupspace_save_confirm.html` (SRP fix).

### Added
- **`templates/components/groupspace_save_confirm.html`**: Fragment HTMX per il messaggio di conferma salvataggio nel workspace di gruppo.

---

## [5.8.0] - AEGIS BLUEPRINT: TEMPLATE LIBRARY (2026-04-04)
Libreria template Markdown app-wide per documenti narrativi. Gestione admin integrata nel pannello SYS_ADMIN.

### Added
- **`logic/blueprints.py`**: `BlueprintManager` — list, read, write, delete blueprint con path sanitization (`_sanitize()` previene traversal fuori da `blueprints/`).
- **`routes/blueprint.py`**: `GET /blueprints/modal` (gallery tutti gli utenti), `GET /blueprints/content` (contenuto raw JSON per JS), `GET /blueprints/admin` + `POST /blueprints/save` + `POST /blueprints/delete` (require_admin).
- **`templates/components/blueprint_modal.html`**: Gallery modale raggruppata per categoria; click inserisce in fondo al buffer editor con separatore `---`.
- **`templates/components/blueprint_admin.html`**: Form crea/sovrascrive blueprint + lista con PURGE.
- **`blueprints/narrative/`**: 5 template iniziali — `session-log.md`, `npc-profile.md`, `planet-description.md`, `ship-description.md`, `location-description.md`.

### Changed
- **`templates/components/editor.html`**: Aggiunto bottone `BLUEPRINT_ARCHIVE` nella toolbar EasyMDE.
- **`routes/admin.py`**: Tab `BLUEPRINT_ARCHIVE` nel pannello SYS_ADMIN; terzo tab che serve `blueprint_admin.html`.
- **`templates/components/admin_panel.html`**: Aggiunto tab BLUEPRINT_ARCHIVE; navigazione tab tramite `/admin?tab=X` per aggiornamento corretto dello stato attivo.
- **`main.py`**: Registrazione `blueprint.router`.

---

## [5.7.0] - AEGIS GROUPS & ADMIN PANEL (2026-04-04)
Sistema di gruppi utente, admin panel HTMX completo, messaggistica filtrata per gruppo.

### Added
- **`logic/auth.py`**: `GroupStore` (persistenza `~/.config/sc-archive/groups.json`, CRUD asincrono, provisioning workspace gruppo). `GroupStoreProtocol`, `GroupStoreUserProtocol`, `SyncGroupStoreProtocol`. `UserRecord.groups: list[str]` con retrocompatibilità (`groups: []` per utenti senza campo).
- **`routes/admin.py`**: CRUD utenti (`/admin/users/*`) e gruppi (`/admin/groups/*`) protetti da `require_admin`.
- **`routes/deps.py`**: Dependency `require_admin` — verifica `"admin" in record.groups`, HTTP 403 altrimenti.
- **`templates/components/admin_panel.html`**: Tab CREW_REGISTRY / TEAM_INDEX / BLUEPRINT_ARCHIVE.
- **`templates/components/admin_user_list.html`**, **`admin_user_modal.html`**, **`admin_group_list.html`**, **`admin_group_modal.html`**: Fragment HTMX admin.
- **`logic/groupspace.py`**: `GroupSpaceAccess` (controllo accesso e permessi R/W per area) + `GroupSpaceManager` (operazioni filesystem scoped al workspace di gruppo con enforcement permessi).
- **`routes/groupspace.py`**: Hub, browser, editor, save, create, delete per workspace di gruppo.
- **`templates/components/groupspace_hub.html`**, **`groupspace_browser.html`**, **`groupspace_editor.html`**, **`groupspace_create_modal.html`**, **`groupspace_save_confirm.html`**: Fragment HTMX group space.

### Changed
- **`logic/comms.py`**: `CommsManager.allowed_recipients()` — filtra destinatari per gruppo condiviso con sender o gruppo `"admin"`. `send_message()` e `promote_draft()` ricevono `allowed_usernames`.
- **`routes/comms.py`**: Handler compose/send/draft calcolano `allowed_recipients` prima di passarli a `CommsManager`.
- **`logic/auth.py`**: `UserStore` esteso con `list_users()`, `update_groups()`, `delete_user()`. `AuthService` esteso con `get_user()`, `update_user_groups()`, `delete_user()`, `list_users()`, `create_user(groups=[])`. Bootstrap crea admin con `groups=["admin"]`.
- **`templates/layouts/base.html`**: Link `GROUP_SPACE` in navbar; link `SYS_ADMIN` visibile solo se `request.session["is_admin"]`.
- **`main.py`**: Registrazione `admin.router`, `groupspace.router`. Lifespan: provisioning workspace per gruppi preesistenti via `provision_group_dirs_sync`.

### Permission Model (GROUP_SPACE)
- Root gruppo (`/{group}/`): admin R+W, membri R.
- Shared folder (`/{group}/shared/`): membri R+W, admin R.
- Enforced a livello `logic/groupspace.py` — zero fiducia nel frontend.

---

## [5.5.2] - SECURITY HARDENING: SESSION KEY & WORKSPACE ROOT (2026-03-30)

### Fixed
- **`logic/auth.py`**: `_default_root()` usa sempre `Path.home() / "sc-archive" / username` — rimossa dipendenza da `settings.get("workspace_base")`. Rimossa l'importazione di `settings` da `auth.py`.
- **`config/settings.json`**: rimosso `workspace_base` hardcoded (`/home/spacewolf/sc-archive`) che causava workspace errato per utenti diversi.
- **`main.py`**: `AEGIS_SECRET_KEY` ora obbligatoria via `os.environ["AEGIS_SECRET_KEY"]` — nessun fallback debole in produzione; l'app crasha all'avvio se la variabile non è presente.
- **`bin/launch.sh`**: generazione e persistenza automatica della session key in `~/.config/sc-archive/session.key` (permessi `600`). Riuso tra riavvii, reset manuale con cancellazione del file.

---

## [5.5.1] - AEGIS IDENTITY: SOLID HARDENING & WORKSPACE SECURITY (2026-03-29)
Rafforzamento architetturale di `logic/auth.py` e fix di sicurezza critico sul selettore workspace.

### Changed — SOLID Refactoring
- **`logic/auth.py`**: Aggiunto `UserStoreProtocol` (`@runtime_checkable`) — `AuthService.__init__` ora tipizza `store` contro l'astrazione anziché la classe concreta (DIP). Aggiunto `_aload()` async per eliminare I/O bloccante nell'event loop: `UserStore.get()`, `save_user()`, `update_root()` ora completamente asincroni. Variante `get_sync()` mantenuta per la catena bootstrap/CLI.
- **`logic/auth.py`**: `AuthService.authenticate()`, `get_user_root()`, `change_password()` resi async — cascata obbligata dall'async `UserStore.get()`.
- **`routes/auth.py`**: Aggiunto `await` su `auth_service.authenticate()` in `POST /login` e `POST /auth/password`.
- **`main.py`**: Aggiunto `await` su `auth_service.get_user_root()` in `auth_middleware`.

### Fixed — Security
- **`routes/config.py`**: Gli utenti non-admin potevano chiamare `POST /root-picker/select` con un path arbitrario (es. `~/projects/`) ottenendo accesso a directory fuori dal proprio workspace. Fix: `_user_allowed_base()` ritorna `~/sc-archive/<username>` per non-admin e `Path.home()` per admin. `select_root` valida `new_root` contro `allowed_base` prima di applicarlo; `root_picker` confina la navigazione al workspace del utente e blocca la risalita al di sopra di esso.

---

## [5.5.0] - AEGIS IDENTITY: MULTI-USER AUTH & WORKSPACE ISOLATION (2026-03-29)
Implementazione del sistema di autenticazione multi-utente con isolamento workspace per-sessione. Ogni operatore ha credenziali proprie e una cartella di lavoro dedicata.

### Added
- **`logic/auth.py`**: `UserStore` (registro persistente in `config/users.json` con hash bcrypt) + `AuthService` (autenticazione, creazione utenti, gestione workspace).
- **`logic/exceptions.py`**: `AuthError` (401) aggiunta alla gerarchia domain exceptions.
- **`routes/auth.py`**: `GET /login`, `POST /login`, `POST /logout`, `POST /auth/password` (cambio password autenticato).
- **`routes/deps.py`**: dependency `get_current_user` per route che necessitano dell'username corrente.
- **`templates/layouts/login.html`**: pagina login standalone con tema Aegis industriale.
- **`bin/create_user.sh`**: script CLI per creare nuovi utenti (`./bin/create_user.sh <username> <password>`).

### Changed
- **`logic/files.py`**: `_CURRENT_ROOT` globale → `ContextVar _REQUEST_ROOT` — ogni request ASGI ha il proprio root isolato, zero contaminazione tra sessioni concorrenti.
- **`main.py`**: `SessionMiddleware` (cookie firmato, 24h TTL) + `auth_middleware` HTTP che verifica la sessione e lega il workspace via ContextVar prima del dispatch. Versione → `5.5.0`.
- **`routes/config.py`**: `select_root` persiste il nuovo workspace in `config/users.json` per l'utente corrente.
- **`config/settings.py`**: aggiunto `workspace_base` (default: `~/sc-archive/`) ai parametri operativi.
- **`templates/layouts/base.html`**: navbar mostra username corrente e pulsante `// LOGOUT`.
- **`templates/components/settings_modal.html`**: sezione `OPERATOR_ACCESS_KEY` per il cambio password in-app, riorganizzazione layout con spaziatura ottimizzata.

### Bootstrap
- Al primo avvio, se `config/users.json` è assente, viene creato automaticamente l'utente `admin` con password `admin` e workspace `~/sc-archive/admin/`.
- Password di default override tramite `export AEGIS_ADMIN_PASSWORD="..."` prima del primo avvio.
- Cambio password obbligatorio al primo accesso tramite Settings → OPERATOR_ACCESS_KEY.

---

## [5.4.0] - AEGIS STABILITY: CENTRALIZED EXCEPTION HANDLING (2026-03-29)
Implementazione del gestore centralizzato delle eccezioni di dominio. Business logic completamente disaccoppiata da FastAPI: nessun `HTTPException` nei moduli `logic/`. Telemetria strutturata dei guasti nel log operativo.

### Added
- **`logic/exceptions.py`**: Gerarchia di eccezioni di dominio con `status_code` integrato.
  - `AegisError` — base class (`status_code=500`)
  - `AccessDeniedError` (403), `NotFoundError` (404), `InvalidPathError` (400), `InvalidFileTypeError` (400), `FileConflictError` (400), `FilenameRequiredError` (400)
  - `ConversionError` (502), `OracleError` (502), `RenderError` (502)

### Changed
- **`main.py`**: Registrato `@app.exception_handler(AegisError)` — traduce tutte le eccezioni di dominio in `JSONResponse` con `status_code` e `detail` corretti. Logging strutturato via `logging.getLogger("aegis.core")`. Versione bumped a `5.4.0`.
- **`logic/files.py`**: Tutti i `raise HTTPException(...)` sostituiti con eccezioni di dominio (`AccessDeniedError`, `NotFoundError`, `InvalidPathError`, `InvalidFileTypeError`, `FileConflictError`, `FilenameRequiredError`). Rimosso `from fastapi import HTTPException`.
- **`logic/oracle.py`**: `OracleError` locale rimossa. Importata da `logic.exceptions`.
- **`logic/conversion.py`**: `raise Exception(f"GOTENBERG_ERROR: ...")` → `raise ConversionError(...)`. Importata da `logic.exceptions`.
- **`logic/render.py`**: `raise ValueError("NO_MERMAID_BLOCKS_FOUND")` → `raise RenderError(...)`. Importata da `logic.exceptions`.
- **`routes/render.py`**: Rimosso il wrapper `try/except ValueError` intorno a `render_mermaid_zip` — gestione delegata all'handler globale.

---

## [5.3.0] - SOLID COMPLIANCE & CSP HARDENING (2026-03-28)
Refactoring architetturale completo per conformità SOLID e rimozione totale degli attributi `style=` inline per CSP compliance.

### Changed — Architettura
- **`logic/settings.py` → `config/settings.py`**: il modulo di configurazione è co-locato con `config/settings.json`. `config/` è ora un package Python con `__init__.py`. Aggiornati tutti i 6 punti di import.
- **`logic/__init__.py`**: aggiunto per dichiarazione esplicita del package (coerenza con `routes/` e `config/`).
- **`routes/__init__.py`**: estratta `build_breadcrumbs(path)` utility — eliminata la triplicazione in `archive`, `editor`, `pdf`.

### Changed — SOLID Refactoring (`logic/`)
- **`logic/conversion.py`**: introdotti Protocol `PageScaffolding`, `RendererProtocol`, `HtmlBuilderProtocol`; dataclass `DetailedScaffolding`, `MinimalScaffolding`; classi `MarkdownRenderer`, `PdfHtmlBuilder`. `GotenbergClient` accetta `url_provider: Callable`, `renderer`, `builder` via DI. Aggiunto `health_check()`.
- **`logic/oracle.py`**: `_EMBEDDING_KEYWORDS: frozenset` a livello modulo; `OracleClient.__init__` accetta `cfg: SettingsManager` (DI); aggiunti `service_status()` e `list_models()`.
- **`logic/files.py`**: introdotto registro mutation hook (`register_mutation_hook`, `_notify_mutation`) per invertire la dipendenza `FileManager` → `StorageCache`; `os.scandir` e `os.walk` offloaded via `anyio.to_thread.run_sync`; `get_recent()` spostato in `DirectoryLister`.
- **`logic/settings.py`**: `save()` e `set()` async con `anyio.open_file`; aggiunto `batch_update()` per scrittura singola su disco; `_save_sync()` esplicito per startup.
- **`routes/core.py`**: `services_status()` delega a `gotenberg.health_check()` e `oracle.service_status()`; estratto `_system_context()`.
- **`routes/pdf.py`**: estratto `_resolve_pdf_bytes()` async helper.
- **`routes/settings.py`**: `save_settings()` usa `batch_update()` — singola scrittura disco; `list_ollama_models()` rimosso (spostato in `OracleClient.list_models()`).

### Changed — CSS Architecture
- **`static/css/pdf-industrial.css`**: estratto da costante `INDUSTRIAL_CSS` in `logic/conversion.py`. Caricato una volta al module init via `Path.read_text()`.
- **`static/css/editor-aegis.css`**: estratti i due blocchi `<style>` da `templates/components/editor.html`.
- **`static/css/pdf-preview.css`**: nuovo file per tooltip override, overflow, `#pdf-iframe`, `.aegis-pdf-content`.

### Fixed — CSP Compliance
- **Eliminati tutti gli attributi `style=` inline** dai template (9 file) e dagli snippet HTML generati dai route (`routes/archive.py`, `routes/editor.py`).
- Nuove classi CSS in `main.css`: `.aegis-input-bg`, `.btn-violet`, `.aegis-hud-modal`, `#mermaid-error`.
- Nuove classi in `editor-aegis.css`: `.aegis-panel-bg`, `#editor-easymde-root`, `#aegis-filetree`, `#editor-scan-overlay`, `.aegis-editor-header`, `.aegis-editor-main`.
- Rimangono 2 soli `style=` intenzionali (valori CSS dinamici Jinja2: `--w: {{ value }}%` in `dashboard.html` e `stats_grid.html`).
- I `style=` in `logic/conversion.py` (header/footer Gotenberg) sono strutturalmente necessari: Gotenberg non ha accesso ai file statici dell'app.

## [5.2.0] - AEGIS BROADCAST & CONTEXT PRECISION (2026-03-28)
Introduzione del feedback visivo universale per lo stato del protocollo e perfezionamento della stabilità dei suggerimenti neurale.

### Added
- **Visual Alert System (Ghost-Text)**: Se il protocollo è spento, la richiesta di suggerimento attiva ora una notifica rossa nell'editor: `!! NEURAL_PROTOCOL_OFFLINE !!`.
- **Mermaid Protocol Banner**: Il modale di sintesi mostra ora un avviso prominente e blocca le operazioni sintetiche se l'Uplink è disattivato.
- **Context Isolation Protocol**: Racchiuso l'input neurale tra tag `[CONTEXT_START]` / `[CONTEXT_END]` per eliminare la ripetizione del testo utente (eco) nei suggerimenti.

### Changed
- **Ghost-Text Stability**: Implementata logica di rilevamento errore `NEURAL_LINK_DISABLED` all'interno dello stream SSE per evitare fallimenti silenziosi.
- **Improved Context Closure**: Aumento di `num_predict` a 500 per permettere la chiusura completa di frasi complesse nel Ghost-Text.
- **Layout Optimization (Mermaid)**: Banner di stato riposizionato in alto nel modale per visibilità immediata.

## [5.1.0] - AEGIS ISOLATION & NEURAL HARDENING (2026-03-28)
Isolamento logico totale del backend neurale e potenziamento della resilienza delle scansioni di intelligence.

### Added
- **Protocol Hard-Stop**: Tutte le rotte neurale (`summarize`, `complete`, `mermaid`) ora rispettano rigidamente il flag `neural_link_enabled`. Se spento, il backend solleva un `NEURAL_PROTOCOL_OFFLINE` senza toccare le API esterne.
- **Neural Scan Hardened**:
  - Finestra di contesto elevata a 16.384 token per processare documenti di grande dimensione.
  - Utilizzo di tag strutturali (`[SOURCE_DOCUMENT_START]`) per isolare il contenuto dal prompt operativo.
  - Temperatura di scansione calibrata a 0.2 per massima precisione tecnica.
- **Surgical HTML Cleanup**: Sistema di filtraggio per rimuovere tag `div` allucinati dal modello che causavano la rottura del layout HUD.
- **Dashboard Protocol Awareness**: Il pannello telemetria ora mostra lo stato `PROTOCOL_OFFLINE` ed evita probe inutili verso Ollama.

### Changed
- **Ollama Probe Optimization**: La Dashboard e il modale Settings rilevano il protocollo disattivato e annullano preventivamente la scansione dei modelli per migliorare le performance della UI.

## [5.0.0] - AEGIS PERSISTENCE & CENTRALIZED UPLINK (2026-03-28)
Centralizzazione totale della configurazione in `config/settings.json`, rinfresco industriale della UI e telemetria dashboard ripristinata.

### Added
- **Settings Persistence**: Introduzione di `logic/settings.py` e `config/settings.json`. Tutti i parametri (Ollama IP, Gotenberg IP, Modelli IA, Flags) sono ora persistenti tra i riavvii.
- **Dashboard Telemetry**: Ripristinata la rotta `/stats` in `routes/core.py`. La dashboard ora aggiorna CPU, RAM e stato root ogni 30s.
- **Reactive Refresh**: Al salvataggio dei settings, il pannello `services-status-container` della dashboard si aggiorna via HTMX (`HX-Trigger: settings-updated`).
- **Neural Filtering**: I modelli Ollama sono ora filtrati per escludere motori di embedding (`embed`, `bge`, `nomic`, ecc.) dai menu di selezione chat/sintesi.

### Changed
- **Aegis Industrial Style**: Standardizzazione globale in `base.html` per tutti i campi `input`, `select` e `textarea`.
  - Font: `Roboto Mono` 12px.
  - Padding: `0.5rem 0.75rem`.
  - Bordi: rimossi (`border: none`) in favore di background scuri integrati.
- **Settings Modal Layout**: Riorganizzazione Gestalt del modale. Tighten label-input spacing e aumento gap inter-blocco per eliminare ambiguità visiva.
- **Uplink logic**: Migrazione di tutte le rotte e servizi all'utilizzo del `SettingsManager` invece delle variabili d'ambiente.

---

## [4.8.0] - AEGIS FILETREE (2026-03-27)
Sidebar albero directory nell'editor con navigazione lazy, persistenza stato e palette colori coerente col file browser.

### Added
- **Sidebar albero directory**: colonna sinistra collassabile nell'editor (`#aegis-filetree`, larghezza 260px) con toggle `«`/`»` persistito in `localStorage`.
- **Lazy expand**: le cartelle caricano i figli via `GET /tree/expand?path=` solo al click — nessun render ricorsivo totale.
- **Highlight file attivo**: il documento aperto è evidenziato nell'albero con bordo sinistro cyan.
- **State persistence**: path espansi salvati in `localStorage['aegis-filetree-expanded']` e ripristinati dopo ogni navigazione HTMX via `htmx:afterSettle`.
- **`GET /tree?active=`** in `routes/archive.py`: root level + active_path per la sidebar.
- **`GET /tree/expand?path=&active=`** in `routes/archive.py`: figli di una cartella.
- **`templates/components/filetree_sidebar.html`**: header `ARCHIVE_TREE` + lazy load root.
- **`templates/components/filetree_node.html`**: nodi dir/file con routing corretto per `.md`, `.pdf`, `.html`, altri.
- **`templates/icons/folder-open.html`**: SVG outline open folder (stroke only, `fill="none"`) per la transizione icona.

### Changed
- **Icone cartella**: `fa-solid fa-folder-closed` → `fa-solid fa-folder-open` al toggle espansione (via swap JS su `.folder-icon-closed`/`.folder-icon-open`).
- **Palette filetree**: allineata al file browser — dir `neon-text` + drop-shadow cyan, `.md` `neon-text`, `.pdf` icona `text-red-400`, `.html` icona `text-amber-400`, altri `text-zinc-100`.
- **Fullscreen safe**: bottone toggle sidebar nascosto con `display: none !important` durante la modalità fullscreen EasyMDE (`aegis-fullscreen-active`).

### Fixed
- **Reset albero alla navigazione**: lo stato espanso viene salvato/ripristinato via `localStorage` — la navigazione tra file non azzera l'albero.
- **Toggle sidebar in fullscreen**: il bottone `#aegis-filetree-toggle-wrap` è escluso dalla viewport fullscreen tramite CSS condizionale.

---

## [4.7.4] - ORACLE TIMEOUT HARDENING (2026-03-26)
Fix timeout e messaggi di errore Oracle per distinguere server irraggiungibile da inferenza lenta.

### Fixed
- **Oracle timeout**: `httpx.AsyncClient` ora usa timeout granulari — `connect=5s`, `read=600s`, `write=30s`, `pool=5s`. In precedenza `timeout=120.0` impostava anche il read timeout a 120s, causando `NEURAL_CORE_UNREACHABLE` su GPU lente o documenti lunghi.
- **Errore fuorviante**: `httpx.TimeoutException` catturava anche `ReadTimeout` riportandolo come `NEURAL_CORE_UNREACHABLE`. Ora separato: `ConnectError`/`ConnectTimeout` → `NEURAL_CORE_UNREACHABLE`, tutti gli altri timeout → `NEURAL_INFERENCE_TIMEOUT`.

---

## [4.7.3] - DOCS & ROADMAP UPDATE (2026-03-26)
Aggiornamento documentazione al ciclo corrente e pianificazione AEGIS CHRONOS.

### Added
- **`docs/piano-aegis-chronos.md`**: Piano dettagliato per la fase [4.3] — versionamento narrativo Git opt-in con requisiti funzionali, architettura, fasi di sviluppo e vincoli espliciti.

### Changed
- **`docs/ROADMAP.md`**: [4.3] AEGIS CHRONOS ridefinito — scope ristretto a operazioni safe (no push/pull/merge), modulo opt-in solo se repo Git già presente, aggiunto link al piano dettagliato.
- **`docs/Stato-dell-Arte.md`**: Aggiornato dalla v4.0 alla v4.7.2 — documentate tutte le funzionalità implementate nei cicli 4.1–4.7 (Render Engine, Oracle resilience, Dashboard telemetry, Uplink Config, UX).

---

## [4.7.2] - DASHBOARD LAYOUT REFINEMENT (2026-03-26)
Riorganizzazione del cockpit dashboard e separazione dei modelli Ollama per categoria.

### Changed
- **Dashboard Panel Order**: Nuovo ordine — SYSTEM_STATUS + TERMINAL_MATRIX → GOTENBERG + OLLAMA → RECENT_FRAGMENTS + STORAGE_NODE.
- **Services Status — Two Panels**: GOTENBERG e OLLAMA ora sono `glass-panel` separati affiancati invece di un unico pannello diviso internamente.
- **Ollama Model Categorization**: I modelli Ollama sono ora classificati in `CHAT_MODELS` e `EMBED_MODELS` tramite keyword matching (`embed`, `bge`, `minilm`, `e5-`, `gte-`, `rerank`).
- **Stats Grid Cleanup**: `RECENT_FRAGMENTS` e `STORAGE_NODE` rimossi da `stats_grid.html` e gestiti direttamente da `dashboard.html` per controllo esplicito dell'ordine.

---

## [4.7.1] - ORACLE RESILIENCE PATCH (2026-03-26)
Hardening del layer neurale contro timeout di connessione e supporto multi-endpoint per ambienti multi-macchina.

### Added
- **Oracle Multi-Endpoint Probe**: `OracleClient.probe_url()` testa in sequenza `localhost:11434` e `172.31.112.1:11434` all'avvio e blocca l'URL sul primo endpoint attivo (timeout 2s per probe). Sovrascrivibile via `OLLAMA_URL`.

### Fixed
- **Oracle ConnectTimeout**: `generate_syntax()` e `summarize()` ora wrappano `httpx.ConnectTimeout`, `httpx.ConnectError` e `httpx.TimeoutException` in `OracleError("NEURAL_CORE_UNREACHABLE")` invece di propagare l'eccezione non gestita fino all'ASGI layer.

---

## [4.7.0] - AEGIS RENDER & COCKPIT REFINEMENT (2026-03-26)
Completamento del modulo di export Mermaid, ottimizzazione del cockpit editoriale e introduzione del pannello di telemetria backend.

### Added
- **Aegis Render Engine**: Nuovo modulo `logic/render.py` + `routes/render.py` per l'export dei diagrammi Mermaid via Gotenberg (screenshot headless Chromium).
  - `GET /render/mermaid/png?path=&index=N` — export PNG singolo per blocco.
  - `GET /render/mermaid/bulk?path=` — download ZIP di tutti i blocchi del documento.
  - Modal lista blocchi (`mermaid_list_modal.html`) con link apertura in nuova scheda.
- **Backend Services Status Panel**: Nuovo pannello dashboard (`components/services_status.html`) con sondaggio real-time di Gotenberg (`/health`) e Ollama (`/api/tags`). Auto-refresh ogni 30s via HTMX. Mostra modelli Ollama caricati.
- **Editor Toolbar — Render Actions**: Pulsanti `aegis-render` (lista blocchi) e `aegis-render-all` (ZIP bulk) integrati nella toolbar EasyMDE dopo Neural Hint.
- **Editor Toolbar — COMMIT_STABLE e PRINT_DOCUMENT**: Spostati dall'action bar breadcrumb alla toolbar EasyMDE per coerenza operativa.
- **File Grid — Export Mermaid**: Bottone export ZIP visibile direttamente nella griglia per ogni file `.md`.

### Fixed
- **File Grid Button Visibility**: Rimosso `opacity-0 group-hover:opacity-100` — tutti i pulsanti azione ora sempre visibili con intensità uniforme al bottone Delete.
- **Input/Textarea Background**: Risolto il layer conflict DaisyUI (`.input`, `.textarea` impostano `background-color` fuori `@layer`, battono le utility Tailwind) tramite `style` inline con `rgba(0,0,0,0.4)` su tutti i campi form: search bar, create modal, rename modal, oracle modal.
- **HTMX Target Inheritance**: `services-status-container` ora dichiara esplicitamente `hx-target="this"` per prevenire l'override del `hx-target` ereditato dal `body` (`#aegis-view-core`).

### Changed
- **Search Bar**: Migrata a `label.input input-bordered` DaisyUI con prefisso `SCAN_QUERY //` in neon cyan integrato — coerente con lo stile delle modali.
- **File Grid Buttons**: Aggiunto `btn-neon` (cyan) a tutti i pulsanti non-Delete e gap `gap-2` tra i bottoni. Aggiunto wrapper DaisyUI `tooltip tooltip-bottom` per ogni azione.
- **CSS — `.btn-neon`**: Aggiunta classe custom in `main.css` con `!important` per override DaisyUI su `btn-outline`.

## [4.6.2] - AEGIS_PROTOCOL (2026-03-26)
Consolidamento della stabilità dell'interfaccia e rilascio delle barriere fisiche di rendering.

### Added
- **Native Multi-Tab Sync**: Conversione universale dei trigger di navigazione in ancore `<a>` per supporto nativo browser.
- **Full-Grid Scan Overlay**: Schermo di caricamento neurale ad alta visibilità durante le scansioni dell'Oracle.
- **Wide-Format Intelligence HUD**: Modale di riepilogo espansa a 1200px per aderenza agli standard aeronautici.
- **Status Notifier 2.0**: Feedback di salvataggio potenziato con effetti pulse e glow neon Cyan.

### Fixed
- **Fullscreen Breakthrough**: Risolto il bug di "trapping" dei pannelli EasyMDE tramite disabilitazione automatica dei `backdrop-filter` genitori.
- **Z-Index Stratigraphy**: Stabilizzata la gerarchia dei layer; i tooltip ora dominano la visuale sopra l'editor e i breadcrumb.
- **Method Fallback**: Inserito supporto GET per le rotte Oracle per prevenire errori 405 durante la navigazione accidentale.

### Changed
- **Aegis Horizon Palette**: Aggiornamento cromatico verso Zinc-800 per l'editor e Slate Profondo per la preview.
- **Neural Capacity Boost**: Elevato il limite di predizione a 300 token con nuova logica di "Thought Completion".
- **Ghost-Text Visibility**: Suggerimenti IA ora visualizzati in Violetto ad alta opacità (0.8) per un contrasto ottimale.

## [4.2.0] - AEGIS PROTOCOL (2026-03-25)
Consolidamento dello strato neurale e perfezionamento dell'interfaccia industriale Aegis.

### Added
- **Manual Ghost-Text Unit**: Completamento predittivo manuale sincronizzato con priorità di input [TAB] (Single-Tab Acceptance).
- **Aegis Pulse Spinner**: Feedback visivo di uplink (`fa-circle-notch`) durante la generazione neurale per il monitoraggio della latenza.
- **Aegis Intelligence Scan**: Funzionalità di riepilogo automatico (Neural Summary) accessibile dal browser dei file.
- **Aegis Uplink Config**: Terminale di configurazione centralizzato per Branding PDF e protocolli Oracle.
- **Industrial Tooltips**: Integrazione sistematica dei tooltip DaisyUI su tutta la toolbar editoriale.
- **Documentation Expansion**: Integrata guida tecnica dettagliata per il setup industriale di Ollama su Ubuntu 24.04.

### Fixed
- **UI Ergonomics**: Ottimizzata la leggibilità delle modali neurali tramite l'adozione di `prose-lg` e ricalibrazione delle scale tipografiche (18px per i riepiloghi).
- **Editor Stability**: Risolto il bug dei "salti" di scrolling durante la generazione neurale tramite operazioni atomiche (`cm.operation`) di rendering del widget.
- **Icon Rendering conflict**: Risolta la collisione di pseudo-elementi tra DaisyUI e FontAwesome nella toolbar dell'editor.

## [4.1.0] - AEGIS REFACTOR (2026-03-25)
Protocollo di ristrutturazione architetturale completato. Allineamento totale ai principi SOLID.

### Changed
- **SOLID Filesystem Core**: Rifattorizzazione di `logic/files.py` in classi specializzate (`FileManager`, `DirectoryLister`, `Sanitizer`).
- **DIP Client Integration**: Implementati client dedicati e persistenti per Gotenberg e Oracle con gestione del ciclo di vita (FastAPI Lifespan).
- **Oracle Refactor**: Separazione del transport dalla logica di prompt engineering e transizione verso eccezioni strutturate.
- **Import Cleanup**: Eliminati gli import locali "pigri" nei router per una migliore telemetria degli errori in fase di startup.

### Fixed
- **Sanitization Warning**: Soppresso il warning `NoCssSanitizerWarning` tramite hardening del parser di stile in `bleach`.
- **Resource Leakage**: Risolto il potenziale leak di socket tramite pool client gestiti e chiusura automatica allo shutdown del kernel.

## [4.0.1] - AEGIS STABILITY PATCH (2026-03-25)
Correzioni UI e funzionalità operative post-BETA.

### Added
- **HUD_PRINT Toggle**: Generazione PDF con header/footer SC-ARCHIVE completo (HUD mode) oppure solo numero di pagina (default slim).
- **UP_DIRECTORY**: Riga di navigazione verso la directory superiore nel browser file, coerente con il Root Selector.
- **File Rename**: Funzionalità di rinomina file tramite modal HTMX con preservazione estensione automatica.

### Fixed
- **PDF Code Blocks**: Sostituito tema `atom-one-dark` con `default` di Highlight.js per leggibilità ottimale su sfondo bianco in stampa.
- **Search Icon Overflow**: L'icona di stato vuoto nella griglia risultati ora rispetta la classe dimensionale `w-12 h-12` passata via Jinja2 `with`.
- **Search Focus Style**: Campo di ricerca migrato a `input input-bordered` DaisyUI per uniformità con i controlli form delle modali (Neural Synthesis).

### Changed
- **Tailwind v4 Syntax**: Migrazione sistematica alla sintassi canonica v4 — `grow` (ex `flex-grow`), `(--var)` (ex `[var(--var)]`), `bg-linear-to-*` (ex `bg-gradient-to-*`), `z-n` (ex `z-[n]`).
- **CLAUDE.md**: Istruzioni agente consolidate con regole di stile, stack tecnologico e principi SOLID come riferimento operativo.

---

## [4.0.0-BETA] - AEGIS ORACLE (2026-03-25)
Integrazione dello strato di intelligenza neurale locale e normalizzazione industriale dell'interfaccia.

### Added
- **Neural Synthesis Unit**: Collegamento asincrono con `qwen2.5-coder` per la sintesi istantanea di diagrammi Mermaid da linguaggio naturale.
- **Neural Router**: Architettura backend dedicata (`logic/oracle.py`, `routes/oracle.py`) per il processamento SSE dei token AI.

### Fixed
- **UI Normalization (DaisyUI)**: Refactoring chirurgico delle modali (Oracle & Create) per aderenza totale agli standard `form-control` e `label` del framework.
- **Padding Protocol**: Risolto il bug dei testi "appiccicati" ai bordi tramite implementazione di un padding standardizzato di 24px (p-6) su tutti i campi di input.

### Note
- Lavoro di normalizzazione dei template identificato come **Parziale**. La migrazione verso lo standard `form-control` continuerà nelle release successive.

## [3.9.6] - AEGIS MODERNIZED STACK (2026-03-24)
Sincronizzazione della stazione con i protocolli Python 3.13 e migrazione dell'ecosistema dipendenze verso Poetry.

### Added
- **Python 3.13 Core**: Upgrade del nucleo di calcolo alla versione 3.13 per performance e stabilità superiori.
- **Poetry Migration**: Abbandono di Pipenv in favore di Poetry (v2.3.2) per una risoluzione dipendenze deterministica e ultra-veloce.
- **Aegis Signature Sync**: Aggiornate tutte le chiamate `TemplateResponse` (FastAPI/Starlette) per conformità con le nuove specifiche 0.40+.
- **Aegis Installation Guide**: Creata documentazione dedicata in `docs/installazione-pyenv-poetry.md`.
- **Tailwind CLI Spec**: Documentata formalmente la dipendenza dal compilatore standalone v4.2.1.

### Fixed
- **Type Safety**: Risolto l'errore `TypeError: unhashable type: dict` causato dalle divergenze di firma nelle nuove librerie.
- **Pipenv Removal**: Bonifica totale del workspace dai file legacy `Pipfile` e `Pipfile.lock`.

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

---

### [ARCHIVE_LINK] // LOG_STORAGE
Per i log storici delle versioni del Sistema precedenti alla v3.0.0:
🔍 [Visualizza l'Archivio Storico (v1.0.0-v2.1.0)](docs/archive/CHANGELOG_v1-2.md)

*Mantenuto dai protocolli Aegis Class System.*
