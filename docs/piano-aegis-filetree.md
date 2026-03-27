# AEGIS FILETREE // Piano di Implementazione
**Feature standalone — Sidebar albero directory nell'editor**

---

## Obiettivo

Aggiungere una sidebar collassabile nell'editor che mostra l'albero completo della root selezionata (`SET_ARCHIVE`). L'utente può navigare tra i file senza uscire dall'editor. La sidebar è **esclusiva della view editor** — nessun impatto su dashboard, file browser o altri componenti.

---

## Comportamento Atteso

- La sidebar occupa la colonna sinistra dell'editor (larghezza fissa ~260px, collassabile).
- Mostra l'albero directory della root in modo **lazy**: le cartelle caricano i propri figli solo al click (nessun render ricorsivo totale al caricamento).
- Click su file `.md` → carica il file nell'editor (stesso comportamento del file grid).
- Click su altri file (`.pdf`, `.html`) → apre in nuova scheda.
- Bottone toggle (freccia `«` / `»`) per collassare/espandere, stato persistito in `localStorage`.
- In **fullscreen EasyMDE** la sidebar scompare naturalmente (è sorella del container editor, non genitore — nessun conflitto con i fix fullscreen esistenti).
- Il file attualmente aperto è evidenziato nell'albero (classe `active`).

---

## Architettura

### Layout — modifica a `templates/components/editor.html`

Il root `#editor-easymde-root` cambia da colonna singola a flex row:

```
┌──────────────────────────────────────────────────────┐
│ #editor-easymde-root  (flex row, height: 85vh)       │
│                                                      │
│ ┌─────────────┐  ┌───────────────────────────────┐  │
│ │ #filetree   │  │ #editor-main-col              │  │
│ │ sidebar     │  │ (tutto il contenuto attuale)  │  │
│ │ 260px       │  │ flex-grow                     │  │
│ │ collaps.    │  │                               │  │
│ └─────────────┘  └───────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

Il contenuto attuale dell'editor (breadcrumb bar, toolbar, EasyMDE, action bar) viene wrappato in `#editor-main-col` senza modifiche interne.

### Backend

**`logic/files.py`** — aggiunta funzione:
```python
async def list_directory_tree(rel_path: str = "") -> list[TreeNode]
```
`TreeNode`: `{ name, path, is_dir, children: None }` — i figli sono `None` finché non espansi (lazy).

Nessun nuovo file di logica — si estende `DirectoryLister` esistente.

**`routes/archive.py`** — nuovi endpoint:
```
GET /tree              → root tree (primo livello, lazy)
GET /tree/expand?path= → figli di una cartella (HTMX swap)
```

### Frontend

**`templates/components/filetree_sidebar.html`** — sidebar completa:
- Header con nome root + bottone toggle collapse
- Lista file/cartelle del primo livello
- Ogni cartella: icona + nome, click → `hx-get="/tree/expand?path=..."` che swappa `hx-target` con i figli
- Ogni file `.md`: link con `hx-get="/editor?path=..."` `hx-target="#aegis-view-core"`
- Ogni file non-.md: `<a target="_blank">` senza HTMX
- File attivo: classe `neon-text` + bordo sinistro cyan

**`templates/components/filetree_node.html`** — fragment per expand lazy:
- Ritorna solo i nodi figli di una cartella (HTMX swap innerHTML)
- Riciclato ricorsivamente per ogni espansione

### Persistenza stato sidebar

Gestita interamente in JS vanilla nel template (nessun endpoint server):
```javascript
// Al mount
const collapsed = localStorage.getItem('aegis-filetree-collapsed') === 'true'
// Al toggle
localStorage.setItem('aegis-filetree-collapsed', collapsed)
```

---

## Impatto sui componenti esistenti

| Componente | Modifica |
|---|---|
| `templates/components/editor.html` | Aggiunto wrapper flex row + sidebar al lato sinistro |
| `logic/files.py` | Aggiunta `list_directory_tree()` in `DirectoryLister` |
| `routes/archive.py` | Aggiunti `GET /tree` e `GET /tree/expand?path=` |
| CSS fullscreen | Nessuna modifica — sidebar è sorella, non genitore |
| Dashboard | Nessuna modifica |
| File grid | Nessuna modifica |

---

## Fullscreen — perché non è un problema

L'attuale fix fullscreen opera su `#editor-easymde-root` e sui suoi antenati (`#aegis-view-core`, `main`). La sidebar è **figlia** di `#editor-easymde-root`, non antenata — non intercetta `position: fixed` di EasyMDE. Quando EasyMDE va fullscreen prende l'intera viewport con `z-index: 8999`; la sidebar resta sotto, fuori dalla viewport, invisibile. Nessun conflitto.

---

## Fasi di Sviluppo

| Step | Descrizione | Dipendenze |
|------|-------------|-----------|
| 1 | `list_directory_tree()` in `logic/files.py` + `TreeNode` dataclass | — |
| 2 | `GET /tree` e `GET /tree/expand?path=` in `routes/archive.py` | Step 1 |
| 3 | `filetree_node.html` — fragment singolo nodo (file o cartella) | Step 2 |
| 4 | `filetree_sidebar.html` — sidebar completa con toggle e lazy load root | Step 3 |
| 5 | Modifica `editor.html` — wrap flex row, inject sidebar, `#editor-main-col` | Step 4 |
| 6 | Highlight file attivo + persistenza collapse in localStorage | Step 5 |

---

## Vincoli

- **Solo nell'editor**: nessun render della sidebar in altre view.
- **Lazy loading obbligatorio**: nessun render ricorsivo totale — root con migliaia di file deve restare responsiva.
- **Nessuna operazione file dalla sidebar**: solo navigazione (no rename/delete inline — per quello c'è il file browser).
- **Path sanitization**: tutti i path passati a `/tree/expand` validati con `PathSanitizer` esistente.
