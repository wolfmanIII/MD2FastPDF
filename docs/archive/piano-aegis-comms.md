# AEGIS COMMS PROTOCOL — Piano di Implementazione

**Modulo**: `SC-ARCHIVE // COMMS_ARRAY`
**Status**: PLANNED
**Target Version**: 5.6.0

---

## 1. Obiettivo

Sistema di messaggistica user-to-user integrato in SC-ARCHIVE. L'admin (GM/Referee) può scrivere a qualsiasi utente o fare broadcast a tutti. Gli utenti possono scriversi tra loro. Tutto filesystem-based, nessun database.

---

## 2. Struttura cartelle

La cartella `comms/` vive sempre nella **root dell'utente**:

| Utente | Percorso comms |
|--------|----------------|
| `admin` | `~/comms/` |
| `{user}` | `~/sc-archive/{user}/comms/` |

Sottocartelle identiche per tutti:

```
comms/
  inbound/    ← messaggi ricevuti
  outbound/   ← messaggi inviati
  staging/    ← bozze non ancora inviate
```

Creazione automatica alla creazione utente (modifica `logic/auth.py`).

---

## 3. Formato messaggi

Ogni messaggio è un file `.md` con frontmatter minimale (no PyYAML — parsing con `re` stdlib):

```markdown
---
id: <uuid4>
from: sender_username
to: recipient_username   # oppure "ALL" per broadcast
subject: Titolo missione
timestamp: 2026-03-29T14:30:00+00:00
read: false
---

Body in Markdown
```

**Filename**: `{YYYYMMDDTHHmmss}_{id[:8]}_{subject_slug}.md`
Esempio: `20260329T143000_a1b2c3d4_titolo_missione.md`

Il prefisso timestamp consente sort lessicografico = sort cronologico (nessun parsing richiesto per ordinare).

---

## 4. Flusso invio

1. Sender → scrive copia in `sender/comms/outbound/`
2. Sender → scrive copia in `recipient/comms/inbound/`
3. Per broadcast (`to: ALL`): copia in `inbound/` di **ogni** utente (sender escluso)

Il cross-workspace write bypassa intenzionalmente `PathSanitizer` (che è request-scoped sul sender). Si usano path assoluti costruiti da `workspace_base` + username. Una security assertion verifica che il path risolto sia sotto `Path.home()`.

---

## 5. Architettura

### File nuovi

| File | Tipo | Scopo |
|------|------|-------|
| `logic/comms.py` | Python | Business logic completa |
| `routes/comms.py` | Python | APIRouter — tutti gli endpoint |
| `templates/components/comms_hub.html` | Jinja2 | Layout principale (tab bar + panel) |
| `templates/components/comms_message_list.html` | Jinja2 | Lista messaggi (inbound/outbound/staging) |
| `templates/components/comms_message_reader.html` | Jinja2 | Lettura singolo messaggio |
| `templates/components/comms_compose_modal.html` | Jinja2 | Modale composizione/risposta |
| `templates/components/comms_unread_badge.html` | Jinja2 | Badge contatore non letti (navbar) |

### File modificati

| File | Modifica |
|------|---------|
| `logic/auth.py` | `list_usernames()` su Protocol + UserStore; `create_comms_folders` in `create_user` |
| `logic/exceptions.py` | Aggiunta `CommsError` |
| `logic/templates.py` | Aggiunta filtro Jinja2 `render_md` |
| `main.py` | Registrazione `comms.router` |
| `templates/layouts/base.html` | Link COMMS in navbar + badge unread HTMX-polled |

---

## 6. `logic/comms.py` — Classi e firme

### `MessageRecord` (dataclass frozen)

```python
@dataclass(frozen=True)
class MessageRecord:
    id: str
    sender: str
    recipient: str       # username o "ALL"
    subject: str
    timestamp: str       # ISO8601
    read: bool
    body: str
    filename: str        # basename, nessun path
```

### `FrontmatterParser` (static utility)

```python
class FrontmatterParser:
    @classmethod
    def parse(cls, raw: str) -> Optional[tuple[dict, str]]: ...
    # Returns (meta_dict, body_str) or None on malformed input

    @classmethod
    def serialize(cls, meta: dict, body: str) -> str: ...
    # Builds full file content from meta + body

    @classmethod
    def _parse_value(cls, raw: str) -> str | bool: ...
    # Handles "true"/"false" → bool, else stripped str
```

### `CommsManager`

```python
class CommsManager:
    # Path resolution (bypassa PathSanitizer)
    def _workspace_root(self, username: str) -> Path: ...
    def _comms_root(self, username: str) -> Path: ...
    def _inbound(self, username: str) -> Path: ...
    def _outbound(self, username: str) -> Path: ...
    def _staging(self, username: str) -> Path: ...

    # Lifecycle cartelle
    def create_comms_folders_sync(self, username: str) -> None: ...
    async def create_comms_folders(self, username: str) -> None: ...
    async def ensure_comms_folders(self, username: str) -> None: ...
    # ensure_* è idempotente (exist_ok=True) — chiamata all'entrata in GET /comms

    # Lettura
    async def list_folder(self, username: str, folder: str) -> list[MessageRecord]: ...
    async def get_message(self, username: str, folder: str, filename: str) -> MessageRecord: ...
    async def count_unread(self, username: str) -> int: ...

    # Scrittura
    async def send_message(self, sender: str, recipient: str, subject: str, body: str, all_usernames: list[str]) -> MessageRecord: ...
    async def mark_read(self, username: str, folder: str, filename: str) -> None: ...
    async def delete_message(self, username: str, folder: str, filename: str) -> None: ...
    async def save_draft(self, sender: str, recipient: str, subject: str, body: str, draft_filename: Optional[str] = None) -> MessageRecord: ...
    async def promote_draft(self, sender: str, draft_filename: str, all_usernames: list[str]) -> MessageRecord: ...

    # Helpers interni
    async def _write_message_file(self, path: Path, record: MessageRecord) -> None: ...
    # Scrittura atomica: write su .tmp → rename
    async def _read_message_file(self, path: Path) -> Optional[MessageRecord]: ...

# Singleton
comms_manager = CommsManager()
```

---

## 7. `routes/comms.py` — Endpoint

| Method | Path | HTMX Target | Descrizione |
|--------|------|-------------|-------------|
| `GET` | `/comms` | `#aegis-view-core` | Hub principale. Default tab: inbound. Chiama `ensure_comms_folders`. |
| `GET` | `/comms/inbound` | `#comms-content-panel` | Lista messaggi ricevuti |
| `GET` | `/comms/outbound` | `#comms-content-panel` | Lista messaggi inviati |
| `GET` | `/comms/staging` | `#comms-content-panel` | Lista bozze |
| `GET` | `/comms/message` | `#comms-content-panel` | Lettura singolo messaggio. Params: `folder`, `filename`. Triggers `mark_read`. |
| `GET` | `/comms/compose` | `#modal-container` | Modale composizione. Param opzionale: `reply_to` (pre-fill risposta). |
| `POST` | `/comms/send` | `#comms-content-panel` | Invio nuovo messaggio. Form: `recipient`, `subject`, `body`. |
| `POST` | `/comms/draft/save` | (notifica inline) | Salva bozza. Form: `recipient`, `subject`, `body`, `draft_filename` (opz.). |
| `POST` | `/comms/draft/send` | `#comms-content-panel` | Promuove bozza a inviato. Form: `draft_filename`. |
| `POST` | `/comms/delete` | `#comms-content-panel` | Elimina messaggio. Form: `folder`, `filename`. Redirige a lista folder. |
| `GET` | `/comms/unread-count` | `#comms-unread-badge` | Badge contatore non letti. Polled ogni 30s dalla navbar. |

---

## 8. Template — Layout HTMX

```
shell.html
  └── comms_hub.html          (#aegis-view-core)
        ├── Tab bar           (RECEPTION_ARRAY / OUTBOUND_LOG / STAGING_BUFFER)
        └── #comms-content-panel
              ├── comms_message_list.html    (lista per folder)
              └── comms_message_reader.html  (lettura singolo)

#modal-container
  └── comms_compose_modal.html

#comms-unread-badge  (in base.html navbar)
  └── comms_unread_badge.html
```

---

## 9. Modifica `logic/auth.py`

### `UserStoreProtocol`

```python
async def list_usernames(self) -> list[str]: ...
def list_usernames_sync(self) -> list[str]: ...
```

### `UserStore`

```python
async def list_usernames(self) -> list[str]:
    data = await self._aload()
    return list(data.keys())

def list_usernames_sync(self) -> list[str]:
    return list(self._load().keys())
```

### `AuthService.create_user()` / `create_user_sync()`

Dopo `root.mkdir(parents=True, exist_ok=True)`:

```python
# Import locale per evitare circular import
from logic.comms import comms_manager
await comms_manager.create_comms_folders(username)      # async
comms_manager.create_comms_folders_sync(username)       # sync
```

---

## 10. Modifica `logic/exceptions.py`

```python
class CommsError(AegisError):
    """Comms message transmission or retrieval failure."""
    def __init__(self, detail: str = "COMMS_ERROR"):
        super().__init__(detail, status_code=400)
```

---

## 11. Modifica `logic/templates.py`

Aggiunta filtro `render_md` per rendering Markdown nel message reader:

```python
import markdown as _md
import bleach

_ALLOWED_TAGS = bleach.sanitizer.ALLOWED_TAGS | {
    "p", "pre", "code", "h1", "h2", "h3", "h4",
    "table", "thead", "tbody", "tr", "th", "td", "br", "hr"
}

def _render_markdown(value: str) -> str:
    raw = _md.markdown(value, extensions=["fenced_code", "tables"])
    return bleach.clean(raw, tags=_ALLOWED_TAGS, strip=True)

templates.env.filters["render_md"] = _render_markdown
```

Uso nel template: `{{ message.body | render_md | safe }}`

---

## 12. Modifica `templates/layouts/base.html`

Aggiunta al nav (dopo i link esistenti):

```html
<a href="/comms" hx-get="/comms" hx-push-url="true"
   class="text-zinc-400 hover:neon-text transition-colors cursor-pointer no-underline flex items-center space-x-1">
    <span>COMMS</span>
    <span id="comms-unread-badge"
          hx-get="/comms/unread-count"
          hx-trigger="load, every 30s"
          hx-swap="outerHTML">
    </span>
</a>
```

---

## 13. Naming — Vocabolario UI

### Label tab

| Cartella | Label UI |
|----------|----------|
| `inbound/` | `RECEPTION_ARRAY` |
| `outbound/` | `OUTBOUND_LOG` |
| `staging/` | `STAGING_BUFFER` |

### Pulsanti

| Azione | Label |
|--------|-------|
| Apri composizione | `OPEN_CHANNEL //` |
| Invia messaggio | `TRANSMIT //` |
| Salva bozza | `BUFFER_DRAFT` |
| Invia bozza | `TRANSMIT_BUFFERED` |
| Elimina | `PURGE_SIGNAL` |
| Rispondi | `OPEN_RESPONSE` |

### Titoli sezione

| Sezione | Titolo |
|---------|--------|
| Hub principale | `COMMS_ARRAY // SIGNAL MANAGEMENT` |
| Lettura messaggio | `SIGNAL_RECEIVED // DECODING` |
| Composizione | `SIGNAL_COMPOSER // NEW_TRANSMISSION` |
| Folder vuota | `NO_SIGNALS_DETECTED` |
| Broadcast | `BROADCAST // ALL_OPERATORS` |

### Notifiche HTMX

| Evento | Messaggio |
|--------|-----------|
| Inviato | `>> SIGNAL_TRANSMITTED // DELIVERY_CONFIRMED` |
| Bozza salvata | `>> BUFFER_SECURED // DRAFT_RETAINED` |
| Bozza inviata | `>> BUFFER_FLUSHED // SIGNAL_TRANSMITTED` |
| Eliminato | `>> SIGNAL_PURGED // RECORD_EXPUNGED` |
| Destinatario sconosciuto | `!! RECIPIENT_UNKNOWN // TRANSMISSION_ABORTED` |
| Errore generico | `!! COMMS_FAULT // RETRY_ADVISED` |

---

## 14. Sequenza implementazione

```
Phase 0  logic/exceptions.py        → AggiungI CommsError
Phase 0  logic/templates.py         → Aggiungi filtro render_md
Phase 1  logic/comms.py             → Implementazione completa
Phase 2  logic/auth.py              → list_usernames + create_comms_folders
Phase 3  routes/comms.py            → APIRouter completo
Phase 4  templates/components/      → 5 template Jinja2
Phase 5  main.py                    → Registrazione router
Phase 6  templates/layouts/base.html → Nav link + badge
```

---

## 15. Compatibilità utenti esistenti

Gli utenti già presenti in `config/users.json` non hanno le cartelle comms. Soluzione: `CommsManager.ensure_comms_folders(username)` (idempotente, `exist_ok=True`) chiamata all'entrata in `GET /comms`. Nessuna migrazione separata richiesta.

---

## 16. SOLID compliance

| Principio | Applicazione |
|-----------|-------------|
| SRP | `FrontmatterParser` solo parsing. `CommsManager` solo I/O. `MessageRecord` value object. Route handlers solo HTTP. |
| OCP | Aggiungere folder type → solo `_COMMS_SUBFOLDERS` + nuova route. Nessuna classe modificata. |
| LSP | `UserStoreProtocol` aggiornato con `list_usernames` — `UserStore` soddisfa strutturalmente. |
| ISP | `CommsManager` non dipende da `PathSanitizer` né da FastAPI. `UserStore` non iniettato in `CommsManager`. |
| DIP | `CommsManager` dipende da `SettingsManager` (astrazione) e `anyio`. Non dipende da request objects. |