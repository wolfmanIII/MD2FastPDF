# Groups & Admin Panel — Documentazione

**Modulo**: `SC-ARCHIVE // SYS_ADMIN`
**Versione**: 5.9.0
**Stato**: COMPLETATO
**Data**: 2026-04-04
**Dipende da**: AEGIS COMMS (v5.6.0)

---

## 1. Obiettivo

Sistema di gruppi utente con tre effetti:

1. **Admin panel** (`/admin`) — interfaccia HTMX per creare/eliminare gruppi, creare/modificare/eliminare utenti con assegnazione gruppi.
2. **Promozione admin via gruppo** — chiunque abbia il gruppo `"admin"` ha privilegi amministrativi (non più hardcoded su username).
3. **Messaggistica ristretta** — in AEGIS COMMS, un utente può scrivere solo a utenti che condividono almeno un gruppo con lui, e agli admin.

---

## 2. Storage & Data Model

### `~/.config/sc-archive/groups.json`

```json
{
  "admin": {},
  "crew": {},
  "engineering": {}
}
```

Dict `group_name → {}`. Il gruppo `"admin"` viene creato al bootstrap se non esiste.

### `~/.config/sc-archive/users.json` esteso

```json
{
  "admin":  { "password_hash": "...", "root": "...", "groups": ["admin"] },
  "john":   { "password_hash": "...", "root": "...", "groups": ["crew", "engineering"] }
}
```

Retrocompatibilità: utenti senza campo `groups` vengono letti con `groups: []`.

### `UserRecord` esteso

```python
class UserRecord:
    __slots__ = ("username", "password_hash", "root", "groups")

    def __init__(self, username: str, password_hash: str, root: str, groups: list[str]): ...

    def to_dict(self) -> dict:
        return {"password_hash": self.password_hash, "root": self.root, "groups": self.groups}
```

---

## 3. Architettura — `logic/auth.py`

### `GroupStore`

Persiste in `~/.config/sc-archive/groups.json`.

```python
async def list_groups() → list[str]
async def create_group(name) → None          # GroupError("GROUP_ALREADY_EXISTS") + crea workspace
async def delete_group(name, user_store) → None
    # GroupError("GROUP_NOT_FOUND") | GroupError("GROUP_HAS_MEMBERS")
    # Nota: la cartella workspace NON viene eliminata (sicurezza dati)
async def provision_group_dirs(name) → None  # crea {workspace_base}/{name}/shared/
def provision_group_dirs_sync(name) → None   # sync — usato al boot per migrazione
def list_groups_sync() → list[str]           # bootstrap only
def ensure_admin_group_sync() → None         # bootstrap only + provision_group_dirs_sync("admin")
```

`delete_group` riceve `user_store` come parametro — nessuna dipendenza hardcoded (DIP).

### Workspace provisioning

`create_group()` crea automaticamente la struttura filesystem del gruppo:

```
~/sc-archive/{group_name}/
└── shared/
```

Al boot, `main.py` chiama `provision_group_dirs_sync()` per ogni gruppo esistente in `groups.json` — garantisce la presenza delle cartelle anche per gruppi creati prima di questa feature.

La cartella **non viene mai eliminata** quando un gruppo viene rimosso da `groups.json` — prevenzione perdita dati.

### `UserStore` — metodi aggiunti

```python
async def list_users() → list[UserRecord]
async def update_groups(username, groups) → None
async def delete_user(username) → None
```

### `AuthService` — metodi aggiunti

```python
async def get_user(username) → Optional[UserRecord]
async def update_user_groups(username, groups) → None
async def delete_user(username) → None        # AuthError("CANNOT_DELETE_ADMIN") se username == "admin"
async def list_users() → list[UserRecord]
async def create_user(username, password, groups=[]) → UserRecord
```

`bootstrap_admin` crea admin con `groups=["admin"]` e chiama `GroupStore.ensure_admin_group_sync()`.

---

## 4. Admin Guard — `routes/deps.py`

```python
async def require_admin(username: str = Depends(get_current_user)) -> str:
    record = await auth_service.get_user(username)
    if not record or "admin" not in record.groups:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    return username
```

`POST /login` in `routes/auth.py` setta `request.session["is_admin"] = "admin" in record.groups`.

---

## 5. Endpoint — `routes/admin.py`

Tutti protetti da `require_admin`.

| Method | Path | HTMX Target | Descrizione |
|--------|------|-------------|-------------|
| `GET` | `/admin` | `#aegis-view-core` | Panel. Default tab: users |
| `GET` | `/admin/users` | `#admin-content-panel` | Lista utenti fragment |
| `GET` | `/admin/users/create` | `#modal-container` | Modale creazione utente |
| `POST` | `/admin/users/create` | `#admin-content-panel` | Crea utente → ritorna lista |
| `GET` | `/admin/users/{username}/edit` | `#modal-container` | Modale modifica gruppi |
| `POST` | `/admin/users/{username}/edit` | `#admin-content-panel` | Aggiorna gruppi → ritorna lista |
| `POST` | `/admin/users/{username}/delete` | `#admin-content-panel` | Elimina utente → ritorna lista |
| `GET` | `/admin/groups` | `#admin-content-panel` | Lista gruppi fragment |
| `GET` | `/admin/groups/create` | `#modal-container` | Modale creazione gruppo |
| `POST` | `/admin/groups/create` | `#admin-content-panel` | Crea gruppo → ritorna lista |
| `POST` | `/admin/groups/{name}/delete` | `#admin-content-panel` | Elimina gruppo (bloccato se ha utenti) |

---

## 6. Template

| File | Scopo |
|------|-------|
| `templates/components/admin_panel.html` | Layout — tab CREW_REGISTRY / FACTION_INDEX |
| `templates/components/admin_user_list.html` | Lista utenti con gruppi assegnati |
| `templates/components/admin_user_modal.html` | Modale crea/modifica utente (checkbox gruppi) |
| `templates/components/admin_group_list.html` | Lista gruppi con contatore utenti |
| `templates/components/admin_group_modal.html` | Modale crea gruppo |

Nav link `SYS_ADMIN` in `base.html` visibile solo se `request.session.get("is_admin")`.

---

## 7. Messaggistica filtrata — impatto su AEGIS COMMS

### `CommsManager.allowed_recipients` (statico)

```python
@staticmethod
def allowed_recipients(sender, sender_groups, all_users) -> list[str]:
    return [
        u.username for u in all_users
        if u.username != sender
        and ("admin" in u.groups or any(g in sender_groups for g in u.groups))
    ]
```

Un destinatario è raggiungibile se ha gruppo `"admin"` **oppure** condivide almeno un gruppo col sender.

### Impatto su `CommsManager`

- `send_message()` e `promote_draft()` ricevono `allowed_usernames` invece di `all_usernames`
- `_expand_recipients()` valida i destinatari espliciti contro `allowed_usernames` → `CommsError("RECIPIENT_NOT_ALLOWED")`
- `"ALL"` espande esclusivamente su `allowed_usernames`

### Impatto su `routes/comms.py`

Nei handler `GET /comms/compose`, `POST /comms/send`, `POST /comms/draft/send`:

```python
sender_record = await auth_service.get_user(username)
sender_groups = sender_record.groups if sender_record else []
all_users = await auth_service.list_users()
allowed = CommsManager.allowed_recipients(username, sender_groups, all_users)
```

---

## 8. SOLID compliance

| Principio | Applicazione |
|-----------|-------------|
| SRP | `GroupStore` solo I/O gruppi. `UserStore` solo I/O utenti. Filtraggio destinatari in `CommsManager`, non in `AuthService`. |
| OCP | Aggiungere campi a `UserRecord` → solo `to_dict`/costruttore. Nessuna classe consumer modificata. |
| LSP | `UserStoreProtocol` aggiornato con `list_users`, `update_groups`, `delete_user`. `UserStore` soddisfa strutturalmente. |
| ISP | `require_admin` dipende solo da `get_current_user` + `auth_service`. Non porta dipendenze di route. |
| DIP | `GroupStore.delete_group` riceve `UserStore` come parametro — nessuna dipendenza hardcoded. |
