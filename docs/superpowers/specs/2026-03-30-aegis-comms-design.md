# AEGIS COMMS — Design Spec

**Feature**: User-to-user messaging system for SC-ARCHIVE
**Version target**: 5.6.0
**Date**: 2026-03-30
**Status**: APPROVED

---

## 1. Obiettivo

Sistema di messaggistica integrato in SC-ARCHIVE. Qualsiasi utente può scrivere a uno o più utenti. Broadcast a tutti disponibile a chiunque. Admin ha visibilità globale come GM/Referee. Tutto filesystem-based, zero database.

---

## 2. Storage & Data Model

### Struttura cartelle

| Utente | Percorso comms root |
|--------|---------------------|
| `admin` | `~/comms/` |
| `{user}` | `~/sc-archive/{user}/comms/` |

Sottocartelle identiche per tutti:

```
comms/
  inbound/    ← messaggi ricevuti
  outbound/   ← messaggi inviati
  staging/    ← bozze non ancora inviate
```

Creazione automatica alla registrazione utente (`AuthService.create_user`). Per utenti esistenti: `ensure_comms_folders()` idempotente chiamata all'entrata in `GET /comms`.

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

**`to`**: stringa comma-separated. Valore speciale `ALL` quando il sender seleziona tutti gli utenti. Il valore è preservato invariato sia in `outbound/` del sender che in ogni copia `inbound/` dei destinatari.

**Filename**: `{YYYYMMDDTHHmmss}_{id[:8]}_{subject_slug}.md`
Esempio: `20260330T143000_a1b2c3d4_titolo_missione.md`
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
    filename: str        # basename, nessun path

    @property
    def recipients(self) -> list[str]:
        """Espande recipient in lista. 'ALL' non viene espanso qui."""
        return [r.strip() for r in self.recipient.split(",")]
```

---

## 3. Flusso invio

1. Sender seleziona uno o più destinatari (o ALL)
2. `CommsManager.send_message()` itera la lista destinatari espansa
3. Scrive una copia in `sender/comms/outbound/` con `to` originale
4. Scrive una copia in `recipient/comms/inbound/` per ogni destinatario
5. Per `ALL`: `CommsManager` espande a runtime dalla lista utenti, esclude il sender

Cross-workspace write bypassa `PathSanitizer` (request-scoped). Usa path assoluti costruiti da `workspace_base + username`. Security assertion: path risolto deve essere sotto `Path.home()`.

---

## 4. Architettura

### File nuovi

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

### File modificati

| File | Modifica |
|------|---------|
| `logic/auth.py` | `list_usernames()` su Protocol + UserStore; call `create_comms_folders` in `create_user` |
| `logic/exceptions.py` | `CommsError` |
| `logic/templates.py` | Filtro Jinja2 `render_md` |
| `main.py` | Registrazione `comms.router` |
| `templates/layouts/base.html` | Link COMMS navbar + `#comms-unread-badge` |

---

## 5. Classi — `logic/comms.py`

### `FrontmatterParser` (static utility)

- `parse(raw: str) -> Optional[tuple[dict, str]]` — restituisce `(meta, body)` o `None` su input malformato
- `serialize(meta: dict, body: str) -> str` — costruisce contenuto file completo
- `_parse_value(raw: str) -> str | bool` — converte `"true"`/`"false"` in bool

### `CommsManager`

```
Path resolution:
  _workspace_root(username) → Path
  _comms_root(username)     → Path
  _inbound(username)        → Path
  _outbound(username)       → Path
  _staging(username)        → Path

Lifecycle:
  create_comms_folders_sync(username)   # sync, per bootstrap
  create_comms_folders(username)        # async
  ensure_comms_folders(username)        # idempotente, exist_ok=True

Lettura:
  list_folder(username, folder) → list[MessageRecord]   # sort: newest-first
  get_message(username, folder, filename) → MessageRecord
  count_unread(username) → int

Scrittura:
  send_message(sender, recipient_str, subject, body, all_usernames) → MessageRecord
  mark_read(username, folder, filename) → None
  delete_message(username, folder, filename) → None
  save_draft(sender, recipient_str, subject, body, draft_filename?) → MessageRecord
  promote_draft(sender, draft_filename, all_usernames) → MessageRecord

Internal:
  _write_message_file(path, record)   # atomic: .tmp → rename
  _read_message_file(path) → Optional[MessageRecord]
  _expand_recipients(recipient_str, all_usernames, sender) → list[str]
  # espande "ALL" → tutti eccetto sender; altrimenti split(",")
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
| `GET` | `/comms/compose` | `#modal-container` | Modale composizione. Param opzionale: `reply_to=folder/filename`. |
| `GET` | `/comms/preview` | `#comms-preview-panel` | Preview Markdown live. Param: `body`. |
| `POST` | `/comms/send` | `#comms-content-panel` | Invio. Form: `recipients[]`, `subject`, `body`. |
| `POST` | `/comms/draft/save` | (notifica inline) | Salva bozza. Form: `recipients[]`, `subject`, `body`, `draft_filename?`. |
| `POST` | `/comms/draft/send` | `#comms-content-panel` | Promuove bozza. Form: `draft_filename`. |
| `POST` | `/comms/delete` | `#comms-content-panel` | Elimina. Form: `folder`, `filename`. Ritorna lista folder. |
| `GET` | `/comms/unread-count` | `#comms-unread-badge` | Badge count. Polled ogni 30s. |

---

## 7. UI Layout

### Compose modal

```
┌─ SIGNAL_COMPOSER // NEW_TRANSMISSION ──────────────────────┐
│ TO: [checkbox list utenti]              [SELECT ALL]        │
│ SUBJECT: [input text]                                       │
├─────────────────────────┬───────────────────────────────────┤
│ [textarea Markdown]     │ [preview renderizzato live]       │
│                         │ hx-get=/comms/preview             │
│                         │ hx-trigger="input delay:300ms"    │
├─────────────────────────┴───────────────────────────────────┤
│ ↩ ORIGINAL_SIGNAL ▶  (collapsibile — solo in reply)         │
│   Subject: ...  /  primi 3 righe body originale             │
├─────────────────────────────────────────────────────────────┤
│                  [BUFFER_DRAFT]   [TRANSMIT //]             │
└─────────────────────────────────────────────────────────────┘
```

### Message reader

```
┌─ SIGNAL_RECEIVED // DECODING ──────────────────────────────┐
│ FROM: sender   TO: user1, user2   TIMESTAMP: ...           │
│ SUBJECT: Titolo missione                                    │
├─────────────────────────────────────────────────────────────┤
│ [body Markdown renderizzato via filtro render_md]           │
├─────────────────────────────────────────────────────────────┤
│ [OPEN_RESPONSE]                         [PURGE_SIGNAL]      │
└─────────────────────────────────────────────────────────────┘
```

### Toast notification

Il fragment `comms_unread_badge.html` include `data-count="{{ count }}"`. Un inline script paragona il valore ricevuto con quello precedente; se aumenta, dispatcha evento `comms-new-signal` che HTMX intercetta per iniettare un toast OOB in `#toast-container`.

```html
<span id="comms-unread-badge"
      data-count="{{ count }}"
      hx-get="/comms/unread-count"
      hx-trigger="load, every 30s"
      hx-swap="outerHTML">
  ...
  <script>
    (function() {
      const prev = parseInt(document.getElementById('comms-unread-badge')?.dataset.count || '0');
      const next = {{ count }};
      if (next > prev) htmx.trigger(document.body, 'comms-new-signal');
    })();
  </script>
</span>
```

---

## 8. Naming — Vocabolario UI

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

| Evento | Toast / Notifica |
|--------|-----------------|
| Inviato | `>> SIGNAL_TRANSMITTED // DELIVERY_CONFIRMED` |
| Bozza salvata | `>> BUFFER_SECURED // DRAFT_RETAINED` |
| Bozza inviata | `>> BUFFER_FLUSHED // SIGNAL_TRANSMITTED` |
| Eliminato | `>> SIGNAL_PURGED // RECORD_EXPUNGED` |
| Nuovo messaggio | `>> INCOMING_SIGNAL // NEW_TRANSMISSION_RECEIVED` |
| Errore | `!! COMMS_FAULT // RETRY_ADVISED` |

---

## 9. Sequenza implementazione

```
Phase 0  logic/exceptions.py         → CommsError
Phase 0  logic/templates.py          → filtro render_md
Phase 1  logic/comms.py              → implementazione completa
Phase 2  logic/auth.py               → list_usernames + create_comms_folders
Phase 3  routes/comms.py             → APIRouter completo (+ /comms/preview)
Phase 4  templates/components/       → 8 template Jinja2
Phase 5  main.py                     → registrazione router
Phase 6  templates/layouts/base.html → nav link + badge polling
```

---

## 10. SOLID compliance

| Principio | Applicazione |
|-----------|-------------|
| SRP | `FrontmatterParser` solo parsing. `CommsManager` solo I/O. `MessageRecord` value object. Route handlers solo HTTP translation. |
| OCP | Aggiungere folder type → solo `_COMMS_SUBFOLDERS` + nuova route. Nessuna classe modificata. |
| LSP | `UserStoreProtocol` aggiornato con `list_usernames` — `UserStore` soddisfa strutturalmente. |
| ISP | `CommsManager` non dipende da `PathSanitizer` né da FastAPI. `UserStore` non iniettato in `CommsManager`. |
| DIP | `CommsManager` dipende da `SettingsManager` (astrazione) e `anyio`. Non dipende da request objects. |
