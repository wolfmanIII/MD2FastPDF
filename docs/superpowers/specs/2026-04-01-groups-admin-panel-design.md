# Groups & Admin Panel — Design Spec

**Feature**: User group management + admin panel + group-based messaging restriction
**Version target**: 5.7.0
**Date**: 2026-04-01
**Status**: APPROVED
**Depends on**: AEGIS COMMS (2026-03-30-aegis-comms-design.md)

---

## 1. Obiettivo

Aggiungere un sistema di gruppi agli utenti di SC-ARCHIVE con tre effetti:

1. **Admin panel** (`/admin`) — interfaccia HTMX per creare/eliminare gruppi, creare/modificare/eliminare utenti con assegnazione gruppi.
2. **Promozione admin via gruppo** — chiunque abbia il gruppo `"admin"` ha privilegi amministrativi, non solo l'utente `admin` hardcoded.
3. **Messaggistica ristretta** — in AEGIS COMMS, un utente può scrivere solo a utenti che condividono almeno un gruppo con lui, e agli admin. La selezione `ALL` è limitata agli utenti raggiungibili.

---

## 2. Storage & Data Model

### `groups.json` — `~/.config/sc-archive/groups.json`

```json
{
  "admin": {},
  "crew": {},
  "engineering": {}
}
```

Dict `group_name → {}`. Vuoto ora, estendibile senza breaking change. Il gruppo `"admin"` viene creato al bootstrap se non esiste.

### `users.json` esteso

Ogni entry acquisisce il campo `groups`:

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

    def __init__(self, username: str, password_hash: str, root: str, groups: list[str]):
        ...

    def to_dict(self) -> dict:
        return {"password_hash": self.password_hash, "root": self.root, "groups": self.groups}
```

### `GroupError`

Aggiunta a `logic/exceptions.py`:

```python
class GroupError(Exception):
    """Raised for group management violations."""
```

---

## 3. `GroupStore` — `logic/auth.py`

```python
class GroupStore:
    """Persistent registry for available groups, backed by ~/.config/sc-archive/groups.json."""

    async def list_groups(self) -> list[str]: ...
    async def create_group(self, name: str) -> None:
        # raises GroupError("GROUP_ALREADY_EXISTS") se esiste
    async def delete_group(self, name: str, user_store: "UserStore") -> None:
        # raises GroupError("GROUP_HAS_MEMBERS") se utenti assegnati
        # raises GroupError("GROUP_NOT_FOUND") se non esiste
    def list_groups_sync(self) -> list[str]:
        # usato solo nel bootstrap
```

`delete_group` interroga `UserStore` per verificare che nessun utente abbia `name` nei propri gruppi prima di procedere.

---

## 4. `UserStore` esteso

Aggiunta a `UserStore` e `UserStoreProtocol`:

```python
async def list_users(self) -> list[UserRecord]: ...
async def update_groups(self, username: str, groups: list[str]) -> None: ...
async def delete_user(self, username: str) -> None: ...
```

`list_users()` aggiunto anche a `UserStoreProtocol`.

---

## 5. `AuthService` esteso

```python
async def create_user(self, username: str, password: str, groups: list[str] = []) -> UserRecord:
    # groups default [] per retrocompatibilità
async def get_user(self, username: str) -> Optional[UserRecord]: ...
    # wrapper su _store.get() — usato da require_admin e route handlers
async def update_user_groups(self, username: str, groups: list[str]) -> None: ...
async def delete_user(self, username: str) -> None:
    # raises AuthError("CANNOT_DELETE_ADMIN") se username == "admin"
async def list_users(self) -> list[UserRecord]: ...
```

`bootstrap_admin` crea admin con `groups=["admin"]`. Crea anche il gruppo `"admin"` in `GroupStore` se `groups.json` non esiste.

---

## 6. Admin Panel — `routes/admin.py`

### Guard — `routes/deps.py`

```python
async def require_admin(
    username: str = Depends(get_current_user),
) -> str:
    record = await auth_service.get_user(username)
    if "admin" not in (record.groups if record else []):
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    return username
```

### Endpoint

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

Tutti gli endpoint usano `require_admin` come dipendenza.

---

## 7. Template

### File nuovi

| File | Scopo |
|------|-------|
| `templates/components/admin_panel.html` | Layout principale — tab Users / Groups |
| `templates/components/admin_user_list.html` | Lista utenti con gruppi assegnati |
| `templates/components/admin_user_modal.html` | Modale crea/modifica utente (checkbox gruppi) |
| `templates/components/admin_group_list.html` | Lista gruppi con contatore utenti |
| `templates/components/admin_group_modal.html` | Modale crea gruppo (nome) |

### File modificati

| File | Modifica |
|------|---------|
| `templates/layouts/base.html` | Link `/admin` nel nav, visibile solo se current user ha gruppo `"admin"` |

Il nav link admin viene renderizzato condizionalmente:

```html
{% if request.session.get("is_admin") %}
  <a href="/admin" hx-get="/admin" hx-push-url="true" ...>SYS_ADMIN</a>
{% endif %}
```

`request.session["is_admin"]` viene settato da `routes/auth.py` nel handler `POST /login`, dopo che `authenticate()` ritorna il `UserRecord`: `request.session["is_admin"] = "admin" in record.groups`.

---

## 8. Messaggistica filtrata — impatto su AEGIS COMMS

### Logica di filtraggio

```python
def _allowed_recipients(
    sender: str,
    sender_groups: list[str],
    all_users: list[UserRecord],
) -> list[str]:
    return [
        u.username for u in all_users
        if u.username != sender
        and (
            "admin" in u.groups
            or any(g in sender_groups for g in u.groups)
        )
    ]
```

Un destinatario è raggiungibile se: ha gruppo `"admin"` **oppure** condivide almeno un gruppo col sender.

### Impatto su `CommsManager`

- `send_message()` riceve `allowed_usernames: list[str]` invece di `all_usernames`
- `_expand_recipients()` valida che tutti i destinatari scelti siano in `allowed_usernames`; altrimenti `CommsError("RECIPIENT_NOT_ALLOWED")`
- `"ALL"` espande esclusivamente su `allowed_usernames`

### Impatto su `routes/comms.py`

- `GET /comms/compose`: carica `UserRecord` del sender, calcola `allowed_usernames` via `_allowed_recipients`, passa al template
- `POST /comms/send`: ricalcola `allowed_usernames` e lo passa a `send_message()`

---

## 9. SOLID compliance

| Principio | Applicazione |
|-----------|-------------|
| SRP | `GroupStore` solo I/O gruppi. `UserStore` solo I/O utenti. Filtraggio destinatari in `CommsManager`, non in `AuthService`. |
| OCP | Aggiungere campi a `UserRecord` → solo `to_dict`/costruttore. Nessuna classe consumer modificata. |
| LSP | `UserStoreProtocol` aggiornato con `list_users`, `update_groups`, `delete_user`. `UserStore` soddisfa strutturalmente. |
| ISP | `require_admin` dipende solo da `get_current_user` + `auth_service`. Non porta dipendenze di route. |
| DIP | `GroupStore.delete_group` riceve `UserStore` come parametro — nessuna dipendenza hardcoded. |

---

## 10. Sequenza implementazione

```
Phase 0  logic/exceptions.py       → GroupError
Phase 1  logic/auth.py             → UserRecord groups, GroupStore, UserStore list_users/update_groups/delete_user, AuthService esteso, bootstrap_admin aggiornato
Phase 2  routes/deps.py            → require_admin
Phase 3  routes/admin.py           → APIRouter completo
Phase 4  templates/components/     → 5 template admin
Phase 5  main.py                   → registrazione admin.router
Phase 6  templates/layouts/base.html → nav link admin condizionale
Phase 7  logic/comms.py            → _allowed_recipients, send_message allowed_usernames
Phase 8  routes/comms.py           → calcolo allowed_usernames in compose + send
```
