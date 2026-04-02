# AEGIS COMMS — Documentazione

**Modulo**: `SC-ARCHIVE // COMMS_ARRAY`
**Versione**: 5.6.0
**Stato**: COMPLETATO
**Data**: 2026-03-30

---

## 1. Obiettivo

Sistema di messaggistica filesystem-based integrato in SC-ARCHIVE. Qualsiasi utente può scrivere a uno o più utenti. Broadcast a tutti disponibile a chiunque. Admin ha visibilità globale come GM/Referee. Zero database.

---

## 2. Storage & Data Model

### Struttura cartelle

| Utente | Percorso comms root |
|--------|---------------------|
| `admin` | `~/comms/` |
| `{user}` | `~/sc-archive/{user}/comms/` |

```
comms/
  inbound/    ← messaggi ricevuti
  outbound/   ← messaggi inviati
  staging/    ← bozze non ancora inviate
```

Creazione automatica in `AuthService.create_user`. Per utenti esistenti: `ensure_comms_folders()` idempotente chiamata all'entrata in `GET /comms`.

### Formato messaggio

File `.md` con frontmatter minimale (parser `re` stdlib, no PyYAML):

```markdown
---
id: a1b2c3d4-e5f6-...
from: sender_username
to: user1,user2,user3
subject: Titolo missione
timestamp: 2026-03-30T14:30:00+00:00
read: false
---

Body in Markdown
```

**`to`**: stringa comma-separated. Valore speciale `ALL` quando il sender seleziona tutti gli utenti raggiungibili (filtrato per gruppo — vedi `allowed_recipients`).

**Filename**: `{YYYYMMDDTHHmmss}_{id[:8]}_{subject_slug}.md`
Sort lessicografico = sort cronologico, zero parsing richiesto.

### `MessageRecord`

```python
@dataclass(frozen=True)
class MessageRecord:
    id: str
    sender: str
    recipient: str       # comma-separated o "ALL"
    subject: str
    timestamp: str       # ISO8601
    read: bool
    body: str
    filename: str

    @property
    def recipients(self) -> list[str]:
        return [r.strip() for r in self.recipient.split(",")]
```

---

## 3. Flusso invio

1. Sender seleziona uno o più destinatari (o ALL) — lista filtrata per gruppo
2. `CommsManager.send_message()` itera la lista destinatari espansa
3. Scrive una copia in `sender/comms/outbound/` con `to` originale
4. Scrive una copia in `recipient/comms/inbound/` per ogni destinatario
5. `ALL` espande su `allowed_usernames` escludendo il sender

Cross-workspace write bypassa `PathSanitizer`. Security assertion: path risolto deve essere sotto `Path.home()`.

---

## 4. Architettura

### File

| File | Scopo |
|------|-------|
| `logic/comms.py` | Business logic completa |
| `routes/comms.py` | APIRouter — tutti gli endpoint |
| `templates/components/comms_hub.html` | Layout principale (tab bar + panel) |
| `templates/components/comms_message_list.html` | Lista messaggi per folder |
| `templates/components/comms_message_reader.html` | Lettura singolo messaggio |
| `templates/components/comms_compose_modal.html` | Modale composizione/risposta |
| `templates/components/comms_unread_badge.html` | Badge navbar + toast trigger |
| `templates/components/comms_preview.html` | Fragment preview Markdown live |

### Modifiche a file esistenti

| File | Modifica |
|------|---------|
| `logic/auth.py` | `list_usernames()` su Protocol + UserStore; `create_comms_folders` in `create_user` |
| `logic/exceptions.py` | `CommsError` |
| `logic/templates.py` | Filtro Jinja2 `render_md` |
| `main.py` | Registrazione `comms.router` |
| `templates/layouts/base.html` | Link COMMS navbar + `#comms-unread-badge` |

---

## 5. Classi — `logic/comms.py`

### `FrontmatterParser`

- `parse(raw) → Optional[tuple[dict, str]]` — `(meta, body)` o `None` su input malformato
- `serialize(meta, body) → str` — costruisce contenuto file completo
- `_parse_value(raw) → str | bool` — converte `"true"`/`"false"` in bool

### `CommsManager`

```
Path resolution:
  _workspace_root(username) → Path
  _comms_root(username)     → Path
  _inbound / _outbound / _staging(username) → Path

Lifecycle:
  create_comms_folders_sync(username)   # sync, bootstrap only
  create_comms_folders(username)        # async
  ensure_comms_folders(username)        # idempotente, exist_ok=True

Lettura:
  list_folder(username, folder) → list[MessageRecord]   # newest-first
  get_message(username, folder, filename) → MessageRecord
  count_unread(username) → int

Scrittura:
  send_message(sender, recipient_str, subject, body, allowed_usernames) → MessageRecord
  mark_read(username, folder, filename) → None
  delete_message(username, folder, filename) → None
  save_draft(sender, recipient_str, subject, body, draft_filename?) → MessageRecord
  promote_draft(sender, draft_filename, allowed_usernames) → MessageRecord

Filtraggio:
  allowed_recipients(sender, sender_groups, all_users) → list[str]   # statico
  _expand_recipients(recipient_str, allowed_usernames, sender) → list[str]
    # "ALL" → allowed_usernames \ {sender}
    # altrimenti valida ogni destinatario → CommsError("RECIPIENT_NOT_ALLOWED")

Internal:
  _write_message_file(path, record)          # atomic: .tmp → rename
  _read_message_file(path) → Optional[MessageRecord]
```

---

## 6. Endpoint — `routes/comms.py`

| Method | Path | HTMX Target | Descrizione |
|--------|------|-------------|-------------|
| `GET` | `/comms` | `#aegis-view-core` | Hub. Default tab: inbound. Chiama `ensure_comms_folders`. |
| `GET` | `/comms/inbound` | `#comms-content-panel` | Lista messaggi ricevuti |
| `GET` | `/comms/outbound` | `#comms-content-panel` | Lista messaggi inviati |
| `GET` | `/comms/staging` | `#comms-content-panel` | Lista bozze |
| `GET` | `/comms/message` | `#comms-content-panel` | Lettura messaggio. Params: `folder`, `filename`. Triggers `mark_read`. |
| `GET` | `/comms/compose` | `#modal-container` | Modale composizione. Param opzionale: `reply_to=folder/filename`. Calcola `allowed_recipients`. |
| `POST` | `/comms/preview` | `#comms-preview-panel` | Preview Markdown live. Param: `body`. |
| `POST` | `/comms/send` | `#comms-content-panel` | Invio. Form: `recipients[]`, `subject`, `body`. |
| `POST` | `/comms/draft/save` | (notifica inline) | Salva bozza. Form: `recipients[]`, `subject`, `body`, `draft_filename?`. |
| `POST` | `/comms/draft/send` | `#comms-content-panel` | Promuove bozza. Form: `draft_filename`. |
| `POST` | `/comms/delete` | `#comms-content-panel` | Elimina. Form: `folder`, `filename`. |
| `GET` | `/comms/unread-count` | `#comms-unread-badge` | Badge count. Polled ogni 30s. |

---

## 7. UI — Vocabolario

| Folder | Label tab |
|--------|-----------|
| `inbound/` | `RECEPTION_ARRAY` |
| `outbound/` | `OUTBOUND_LOG` |
| `staging/` | `STAGING_BUFFER` |

| Azione | Label |
|--------|-------|
| Apri composizione | `OPEN_CHANNEL //` |
| Invia | `TRANSMIT //` |
| Salva bozza | `BUFFER_DRAFT` |
| Invia bozza | `TRANSMIT_BUFFERED` |
| Elimina | `PURGE_SIGNAL` |
| Rispondi | `OPEN_RESPONSE` |
| Seleziona tutti | `SELECT ALL` |

| Evento | Toast |
|--------|-------|
| Inviato | `>> SIGNAL_TRANSMITTED // DELIVERY_CONFIRMED` |
| Bozza salvata | `>> BUFFER_SECURED // DRAFT_RETAINED` |
| Bozza inviata | `>> BUFFER_FLUSHED // SIGNAL_TRANSMITTED` |
| Eliminato | `>> SIGNAL_PURGED // RECORD_EXPUNGED` |
| Nuovo messaggio | `>> INCOMING_SIGNAL // NEW_TRANSMISSION_RECEIVED` |
| Errore | `!! COMMS_FAULT // RETRY_ADVISED` |

### Toast — meccanismo unread badge

`comms_unread_badge.html` include `data-count="{{ count }}"`. Un inline script confronta con il valore precedente; se aumenta, dispatcha `comms-new-signal` che HTMX intercetta per iniettare un toast OOB in `#toast-container`.

---

## 8. SOLID compliance

| Principio | Applicazione |
|-----------|-------------|
| SRP | `FrontmatterParser` solo parsing. `CommsManager` solo I/O. `MessageRecord` value object. Route handlers solo HTTP translation. |
| OCP | Aggiungere folder type → solo `_COMMS_SUBFOLDERS` + nuova route. Nessuna classe modificata. |
| LSP | `UserStoreProtocol` aggiornato con `list_usernames` — `UserStore` soddisfa strutturalmente. |
| ISP | `CommsManager` non dipende da `PathSanitizer` né da FastAPI. `UserStore` non iniettato in `CommsManager`. |
| DIP | `CommsManager` dipende da `SettingsManager` (astrazione) e `anyio`. Non dipende da request objects. |
