# Groups & Admin Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add user groups, a `/admin` management panel, and group-based messaging restrictions to SC-ARCHIVE.

**Architecture:** `GroupStore` persists groups to `~/.config/sc-archive/groups.json`. `UserRecord` gains a `groups: list[str]` field. An admin-gated HTMX panel at `/admin` handles CRUD for users and groups. AEGIS COMMS messaging is filtered by group membership via `CommsManager.allowed_recipients()`. Tasks 9–10 require the AEGIS COMMS plan to be completed first.

**Tech Stack:** Python 3.13, FastAPI, anyio, Jinja2/HTMX, Tailwind v4.

---

## Task 1: GroupError

**Files:**
- Modify: `logic/exceptions.py`

- [ ] **Step 1: Add GroupError after RenderError**

Append at the end of `logic/exceptions.py`:

```python
# --- Group Errors ---

class GroupError(AegisError):
    """Group management violation (already exists, has members, not found)."""
    def __init__(self, detail: str = "GROUP_ERROR"):
        super().__init__(detail, status_code=400)
```

- [ ] **Step 2: Verify**

```bash
cd /home/spacewolf/Progetti/MD2FastPDF
poetry run python -c "from logic.exceptions import GroupError; e = GroupError('GROUP_HAS_MEMBERS'); assert e.status_code == 400; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add logic/exceptions.py
git commit -m "feat(groups): add GroupError to exception hierarchy"
```

---

## Task 2: UserRecord + groups field

**Files:**
- Modify: `logic/auth.py`

- [ ] **Step 1: Update UserRecord to include groups**

Replace the `UserRecord` class (currently at the line `class UserRecord:`):

```python
class UserRecord:
    """Represents a single authenticated user entry."""
    __slots__ = ("username", "password_hash", "root", "groups")

    def __init__(self, username: str, password_hash: str, root: str, groups: list[str]):
        self.username = username
        self.password_hash = password_hash
        self.root = root
        self.groups = groups

    def to_dict(self) -> dict:
        return {
            "password_hash": self.password_hash,
            "root": self.root,
            "groups": self.groups,
        }
```

- [ ] **Step 2: Update UserStore.get() and get_sync() to load groups**

Replace the `get` method:

```python
    async def get(self, username: str) -> Optional[UserRecord]:
        """Returns the UserRecord for the given username, or None if not found."""
        entry = (await self._aload()).get(username)
        if not entry:
            return None
        return UserRecord(
            username,
            entry["password_hash"],
            entry["root"],
            entry.get("groups", []),
        )
```

Replace the `get_sync` method:

```python
    def get_sync(self, username: str) -> Optional[UserRecord]:
        """Sync variant — used only during bootstrap/CLI."""
        entry = self._load().get(username)
        if not entry:
            return None
        return UserRecord(
            username,
            entry["password_hash"],
            entry["root"],
            entry.get("groups", []),
        )
```

- [ ] **Step 3: Verify existing users are loaded with groups=[] fallback**

```bash
poetry run python -c "
from logic.auth import auth_service
import asyncio

async def test():
    record = await auth_service.get_user('admin')
    assert hasattr(record, 'groups'), 'no groups field'
    assert isinstance(record.groups, list), 'groups not a list'
    print(f'admin groups: {record.groups}')
    print('OK')

asyncio.run(test())
"
```

Expected: `admin groups: [...]` (may be `[]` for existing admin) then `OK`

- [ ] **Step 4: Commit**

```bash
git add logic/auth.py
git commit -m "feat(groups): UserRecord gains groups field with backwards-compat fallback"
```

---

## Task 3: UserStore extensions + Protocol update

**Files:**
- Modify: `logic/auth.py`

- [ ] **Step 1: Add list_users, update_groups, delete_user to UserStore**

Inside the `UserStore` class, append after `update_root`:

```python
    async def list_users(self) -> list[UserRecord]:
        """Returns all registered users as UserRecord list."""
        data = await self._aload()
        return [
            UserRecord(u, d["password_hash"], d["root"], d.get("groups", []))
            for u, d in data.items()
        ]

    async def update_groups(self, username: str, groups: list[str]) -> None:
        """Replaces the groups list for the given user."""
        data = await self._aload()
        if username not in data:
            raise AuthError(f"USER_NOT_FOUND: {username}")
        data[username]["groups"] = groups
        await self._save(data)

    async def delete_user(self, username: str) -> None:
        """Removes the user entry. Does not delete filesystem workspace."""
        data = await self._aload()
        if username not in data:
            raise AuthError(f"USER_NOT_FOUND: {username}")
        del data[username]
        await self._save(data)
```

- [ ] **Step 2: Update UserStoreProtocol**

Replace the `UserStoreProtocol` class:

```python
@runtime_checkable
class UserStoreProtocol(Protocol):
    """Async abstraction over the user persistence backend. Used by AuthService."""

    async def get(self, username: str) -> Optional["UserRecord"]: ...
    def is_empty(self) -> bool: ...
    async def save_user(self, record: "UserRecord") -> None: ...
    async def update_root(self, username: str, root: str) -> None: ...
    async def list_users(self) -> list["UserRecord"]: ...
    async def update_groups(self, username: str, groups: list[str]) -> None: ...
    async def delete_user(self, username: str) -> None: ...
```

- [ ] **Step 3: Verify**

```bash
poetry run python -c "
from logic.auth import auth_service
import asyncio

async def test():
    users = await auth_service.list_users()
    print(f'Users found: {[u.username for u in users]}')
    print('OK')

asyncio.run(test())
"
```

Expected: `Users found: ['admin']` (or however many exist) then `OK`

- [ ] **Step 4: Commit**

```bash
git add logic/auth.py
git commit -m "feat(groups): UserStore gains list_users, update_groups, delete_user"
```

---

## Task 4: GroupStore

**Files:**
- Modify: `logic/auth.py`

- [ ] **Step 1: Add _GROUPS_FILE path constant**

After `_LEGACY_USERS_FILE = Path("config/users.json")`, add:

```python
_GROUPS_FILE: Path = _CONFIG_DIR / "groups.json"
```

- [ ] **Step 2: Add GroupStore class**

Add the full class before `UserRecord` (after `_migrate_legacy_users()`):

```python
class GroupStore:
    """Persistent registry for available groups, backed by ~/.config/sc-archive/groups.json."""

    def _load(self) -> dict:
        if not _GROUPS_FILE.exists():
            return {}
        try:
            with open(_GROUPS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    async def _aload(self) -> dict:
        p = anyio.Path(_GROUPS_FILE)
        if not await p.exists():
            return {}
        try:
            content = await p.read_text(encoding="utf-8")
            return json.loads(content)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_sync(self, data: dict) -> None:
        with open(_GROUPS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    async def _save(self, data: dict) -> None:
        content = json.dumps(data, indent=4)
        async with await anyio.open_file(_GROUPS_FILE, "w") as f:
            await f.write(content)

    def list_groups_sync(self) -> list[str]:
        """Sync — used only in bootstrap."""
        return list(self._load().keys())

    async def list_groups(self) -> list[str]:
        """Returns all group names in insertion order."""
        return list((await self._aload()).keys())

    async def create_group(self, name: str) -> None:
        """Adds a new group. Raises GroupError if name already exists."""
        from logic.exceptions import GroupError
        data = await self._aload()
        if name in data:
            raise GroupError(f"GROUP_ALREADY_EXISTS: {name}")
        data[name] = {}
        await self._save(data)

    async def delete_group(self, name: str, user_store: "UserStore") -> None:
        """Removes a group. Raises GroupError if group has assigned users or does not exist."""
        from logic.exceptions import GroupError
        data = await self._aload()
        if name not in data:
            raise GroupError(f"GROUP_NOT_FOUND: {name}")
        users = await user_store.list_users()
        if any(name in u.groups for u in users):
            raise GroupError("GROUP_HAS_MEMBERS")
        del data[name]
        await self._save(data)

    def ensure_admin_group_sync(self) -> None:
        """Creates the 'admin' group if absent. Sync — bootstrap only."""
        data = self._load()
        if "admin" not in data:
            data["admin"] = {}
            self._save_sync(data)
```

- [ ] **Step 3: Verify GroupStore**

```bash
poetry run python -c "
from logic.auth import GroupStore
import asyncio

async def test():
    gs = GroupStore()
    groups = await gs.list_groups()
    print(f'Groups: {groups}')
    print('OK')

asyncio.run(test())
"
```

Expected: `Groups: [...]` then `OK`

- [ ] **Step 4: Commit**

```bash
git add logic/auth.py
git commit -m "feat(groups): add GroupStore with create/delete/list"
```

---

## Task 5: AuthService extensions + bootstrap update

**Files:**
- Modify: `logic/auth.py`

- [ ] **Step 1: Update create_user and create_user_sync to accept groups**

Replace `create_user`:

```python
    async def create_user(self, username: str, password: str, groups: list[str] | None = None) -> UserRecord:
        """Creates a new user with hashed password, default workspace, and optional groups."""
        root = self._default_root(username)
        await anyio.to_thread.run_sync(lambda: root.mkdir(parents=True, exist_ok=True))
        record = UserRecord(username, self._hash(password), str(root), groups or [])
        await self._store.save_user(record)
        return record
```

Replace `create_user_sync`:

```python
    def create_user_sync(self, username: str, password: str, groups: list[str] | None = None) -> UserRecord:
        """Sync variant — used only during bootstrap."""
        root = self._default_root(username)
        root.mkdir(parents=True, exist_ok=True)
        record = UserRecord(username, self._hash(password), str(root), groups or [])
        self._sync_store.save_user_sync(record)
        return record
```

- [ ] **Step 2: Add get_user, update_user_groups, delete_user, list_users to AuthService**

Append inside `AuthService` class, after `change_password`:

```python
    async def get_user(self, username: str) -> Optional[UserRecord]:
        """Returns the UserRecord for username, or None if not found."""
        return await self._store.get(username)

    async def update_user_groups(self, username: str, groups: list[str]) -> None:
        """Replaces the groups list for the given user."""
        await self._store.update_groups(username, groups)

    async def delete_user(self, username: str) -> None:
        """Removes a user. Raises AuthError if attempting to delete 'admin'."""
        if username == "admin":
            raise AuthError("CANNOT_DELETE_ADMIN")
        await self._store.delete_user(username)

    async def list_users(self) -> list[UserRecord]:
        """Returns all registered users."""
        return await self._store.list_users()
```

- [ ] **Step 3: Update bootstrap_admin to set groups and create admin group**

Replace `bootstrap_admin`:

```python
    def bootstrap_admin(self) -> None:
        """Creates the admin user on first run if no users exist. Always ensures 'admin' group exists."""
        if self._sync_store.is_empty():
            password = os.getenv("AEGIS_ADMIN_PASSWORD", "admin")
            self.create_user_sync("admin", password, groups=["admin"])
        _group_store.ensure_admin_group_sync()
```

- [ ] **Step 4: Export group_store and user_store at module bottom**

Replace the current module-level singletons at the bottom of `logic/auth.py`:

```python
_store = UserStore()
_group_store = GroupStore()
auth_service = AuthService(_store, _store)
group_store = _group_store
user_store = _store
```

- [ ] **Step 5: Verify bootstrap and group_store export**

```bash
poetry run python -c "
from logic.auth import auth_service, group_store, user_store
import asyncio

async def test():
    groups = await group_store.list_groups()
    assert 'admin' in groups, f'admin group missing: {groups}'
    admin = await auth_service.get_user('admin')
    assert admin is not None, 'admin not found'
    assert 'admin' in admin.groups, f'admin missing admin group: {admin.groups}'
    print(f'admin.groups = {admin.groups}')
    print(f'available groups = {groups}')
    print('OK')

asyncio.run(test())
"
```

Expected: `admin.groups = ['admin']`, `available groups = ['admin']`, `OK`

- [ ] **Step 6: Commit**

```bash
git add logic/auth.py
git commit -m "feat(groups): AuthService extended — get_user, update_user_groups, delete_user, list_users; bootstrap sets admin group"
```

---

## Task 6: require_admin dep + is_admin session

**Files:**
- Modify: `routes/deps.py`
- Modify: `routes/auth.py`

- [ ] **Step 1: Replace routes/deps.py with require_admin added**

```python
"""
AEGIS_IDENTITY_DEPS: FastAPI dependencies for authenticated routes.
"""
from fastapi import Depends, HTTPException, Request
from logic.auth import auth_service


def get_current_user(request: Request) -> str:
    """Returns the authenticated username from the session.
    Auth guard and root binding are handled by the auth middleware in main.py."""
    return request.session.get("username", "")


async def require_admin(username: str = Depends(get_current_user)) -> str:
    """Raises HTTP 403 if the current user does not have the 'admin' group."""
    record = await auth_service.get_user(username)
    if not record or "admin" not in record.groups:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    return username
```

- [ ] **Step 2: Update POST /login in routes/auth.py to set is_admin in session**

Replace the `login` handler body:

```python
@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    """Authenticates credentials, opens a session, and redirects to the dashboard."""
    try:
        record = await auth_service.authenticate(username, password)
        request.session["username"] = username
        request.session["is_admin"] = "admin" in record.groups
        return RedirectResponse(url="/", status_code=302)
    except AuthError:
        request.session["login_error"] = "INVALID_CREDENTIALS"
        return RedirectResponse(url="/login", status_code=302)
```

- [ ] **Step 3: Verify**

```bash
poetry run python -c "
from routes.deps import get_current_user, require_admin
print('deps OK')
"
```

Expected: `deps OK`

- [ ] **Step 4: Commit**

```bash
git add routes/deps.py routes/auth.py
git commit -m "feat(groups): add require_admin dep; POST /login sets is_admin in session"
```

---

## Task 7: routes/admin.py

**Files:**
- Create: `routes/admin.py`

- [ ] **Step 1: Create routes/admin.py**

```python
"""
AEGIS_ADMIN_ROUTER: Admin panel — user and group management.
All endpoints require the 'admin' group via require_admin dependency.
"""
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from logic.auth import auth_service, group_store, user_store
from logic.exceptions import AuthError, GroupError
from logic.templates import templates
from routes.deps import require_admin

router = APIRouter(prefix="/admin", tags=["Aegis Admin"])


def _group_members(groups: list[str], users: list) -> dict[str, int]:
    return {g: sum(1 for u in users if g in u.groups) for g in groups}


@router.get("", response_class=HTMLResponse)
async def admin_panel(
    request: Request,
    username: str = Depends(require_admin),
):
    """Admin hub. Renders panel with user list as default tab."""
    users = await auth_service.list_users()
    groups = await group_store.list_groups()
    return templates.TemplateResponse(
        request,
        "components/admin_panel.html",
        {"users": users, "groups": groups},
    )


@router.get("/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    username: str = Depends(require_admin),
):
    """User list fragment."""
    users = await auth_service.list_users()
    groups = await group_store.list_groups()
    return templates.TemplateResponse(
        request,
        "components/admin_user_list.html",
        {"users": users, "groups": groups},
    )


@router.get("/users/create", response_class=HTMLResponse)
async def admin_user_create_modal(
    request: Request,
    username: str = Depends(require_admin),
):
    """Create user modal."""
    groups = await group_store.list_groups()
    return templates.TemplateResponse(
        request,
        "components/admin_user_modal.html",
        {"groups": groups, "mode": "create", "error": None},
    )


@router.post("/users/create", response_class=HTMLResponse)
async def admin_user_create(
    request: Request,
    username: str = Depends(require_admin),
    new_username: str = Form(...),
    password: str = Form(...),
    groups: list[str] = Form(default=[]),
):
    """Creates a new user. Always returns updated user list (error shown inline in list)."""
    error = None
    try:
        await auth_service.create_user(new_username, password, groups)
    except AuthError as e:
        error = e.detail
    users = await auth_service.list_users()
    all_groups = await group_store.list_groups()
    return templates.TemplateResponse(
        request,
        "components/admin_user_list.html",
        {"users": users, "groups": all_groups, "error": error},
    )


@router.get("/users/{target}/edit", response_class=HTMLResponse)
async def admin_user_edit_modal(
    request: Request,
    target: str,
    username: str = Depends(require_admin),
):
    """Edit user groups modal."""
    user = await auth_service.get_user(target)
    groups = await group_store.list_groups()
    return templates.TemplateResponse(
        request,
        "components/admin_user_modal.html",
        {"user": user, "groups": groups, "mode": "edit", "error": None},
    )


@router.post("/users/{target}/edit", response_class=HTMLResponse)
async def admin_user_edit(
    request: Request,
    target: str,
    username: str = Depends(require_admin),
    groups: list[str] = Form(default=[]),
):
    """Updates user groups. Returns updated user list."""
    await auth_service.update_user_groups(target, groups)
    users = await auth_service.list_users()
    all_groups = await group_store.list_groups()
    return templates.TemplateResponse(
        request,
        "components/admin_user_list.html",
        {"users": users, "groups": all_groups},
    )


@router.post("/users/{target}/delete", response_class=HTMLResponse)
async def admin_user_delete(
    request: Request,
    target: str,
    username: str = Depends(require_admin),
):
    """Deletes a user (cannot delete 'admin'). Returns updated user list."""
    error = None
    try:
        await auth_service.delete_user(target)
    except AuthError as e:
        error = e.detail
    users = await auth_service.list_users()
    all_groups = await group_store.list_groups()
    return templates.TemplateResponse(
        request,
        "components/admin_user_list.html",
        {"users": users, "groups": all_groups, "error": error},
    )


@router.get("/groups", response_class=HTMLResponse)
async def admin_groups(
    request: Request,
    username: str = Depends(require_admin),
):
    """Group list fragment."""
    groups = await group_store.list_groups()
    users = await auth_service.list_users()
    return templates.TemplateResponse(
        request,
        "components/admin_group_list.html",
        {"groups": groups, "group_members": _group_members(groups, users)},
    )


@router.get("/groups/create", response_class=HTMLResponse)
async def admin_group_create_modal(
    request: Request,
    username: str = Depends(require_admin),
):
    """Create group modal."""
    return templates.TemplateResponse(
        request,
        "components/admin_group_modal.html",
        {"error": None},
    )


@router.post("/groups/create", response_class=HTMLResponse)
async def admin_group_create(
    request: Request,
    username: str = Depends(require_admin),
    group_name: str = Form(...),
):
    """Creates a new group. Always returns updated group list (error shown inline)."""
    error = None
    try:
        await group_store.create_group(group_name.strip().lower())
    except GroupError as e:
        error = e.detail
    groups = await group_store.list_groups()
    users = await auth_service.list_users()
    return templates.TemplateResponse(
        request,
        "components/admin_group_list.html",
        {"groups": groups, "group_members": _group_members(groups, users), "error": error},
    )


@router.post("/groups/{name}/delete", response_class=HTMLResponse)
async def admin_group_delete(
    request: Request,
    name: str,
    username: str = Depends(require_admin),
):
    """Deletes a group. Blocked if any user is assigned to it."""
    error = None
    try:
        await group_store.delete_group(name, user_store)
    except GroupError as e:
        error = e.detail
    groups = await group_store.list_groups()
    users = await auth_service.list_users()
    return templates.TemplateResponse(
        request,
        "components/admin_group_list.html",
        {"groups": groups, "group_members": _group_members(groups, users), "error": error},
    )
```

- [ ] **Step 2: Verify import**

```bash
poetry run python -c "from routes.admin import router; print('admin router OK')"
```

Expected: `admin router OK`

- [ ] **Step 3: Commit**

```bash
git add routes/admin.py
git commit -m "feat(groups): routes/admin.py — full CRUD for users and groups"
```

---

## Task 8: Admin templates

**Files:**
- Create: `templates/components/admin_panel.html`
- Create: `templates/components/admin_user_list.html`
- Create: `templates/components/admin_user_modal.html`
- Create: `templates/components/admin_group_list.html`
- Create: `templates/components/admin_group_modal.html`

- [ ] **Step 1: Create admin_panel.html**

```html
<div class="flex flex-col gap-6 w-full">
  <div class="flex items-center justify-between border-b border-zinc-800 pb-4">
    <span class="neon-text font-mono text-lg uppercase tracking-widest">// SYS_ADMIN</span>
    <div class="flex gap-2">
      <button
        hx-get="/admin/users"
        hx-target="#admin-content-panel"
        class="text-xs font-mono uppercase tracking-widest px-3 py-1.5 border border-zinc-700 hover:border-(--neon-cyan) hover:neon-text transition-colors cursor-pointer bg-transparent">
        CREW_REGISTRY
      </button>
      <button
        hx-get="/admin/groups"
        hx-target="#admin-content-panel"
        class="text-xs font-mono uppercase tracking-widest px-3 py-1.5 border border-zinc-700 hover:border-(--neon-cyan) hover:neon-text transition-colors cursor-pointer bg-transparent">
        FACTION_INDEX
      </button>
    </div>
  </div>
  <div id="admin-content-panel">
    {% include 'components/admin_user_list.html' %}
  </div>
</div>
```

- [ ] **Step 2: Create admin_user_list.html**

```html
<div class="flex flex-col gap-4">
  <div class="flex justify-between items-center">
    <span class="text-zinc-400 text-xs font-mono uppercase tracking-widest">
      CREW_REGISTRY // {{ users | length }} PERSONNEL
    </span>
    <button
      hx-get="/admin/users/create"
      hx-target="#modal-container"
      class="text-xs font-mono uppercase tracking-widest px-3 py-1.5 border border-zinc-700 hover:border-(--neon-cyan) hover:neon-text transition-colors cursor-pointer bg-transparent">
      + ENLIST //
    </button>
  </div>

  {% if error is defined and error %}
  <p class="text-red-400 text-xs font-mono uppercase tracking-widest animate-pulse">!! {{ error }}</p>
  {% endif %}

  <div class="flex flex-col gap-2">
    {% for user in users %}
    <div class="glass-panel p-4 flex items-center justify-between gap-4">
      <div class="flex flex-col gap-1.5 min-w-0">
        <span class="neon-text font-mono text-sm">{{ user.username | upper }}</span>
        <div class="flex gap-1.5 flex-wrap">
          {% for g in user.groups %}
          <span class="text-[10px] font-mono uppercase tracking-widest px-2 py-0.5 border border-zinc-700 text-zinc-400">{{ g }}</span>
          {% else %}
          <span class="text-[10px] font-mono uppercase text-zinc-600">NO_FACTION</span>
          {% endfor %}
        </div>
      </div>
      <div class="flex gap-2 shrink-0">
        <button
          hx-get="/admin/users/{{ user.username }}/edit"
          hx-target="#modal-container"
          class="text-xs font-mono uppercase tracking-widest px-2 py-1 border border-zinc-700 hover:border-(--neon-cyan) hover:neon-text transition-colors cursor-pointer bg-transparent">
          MODIFY
        </button>
        {% if user.username != "admin" %}
        <button
          hx-post="/admin/users/{{ user.username }}/delete"
          hx-target="#admin-content-panel"
          hx-confirm="PURGE {{ user.username | upper }} FROM REGISTRY?"
          class="text-xs font-mono uppercase tracking-widest px-2 py-1 border border-zinc-700 hover:border-red-400 hover:text-red-400 transition-colors cursor-pointer bg-transparent">
          PURGE
        </button>
        {% endif %}
      </div>
    </div>
    {% endfor %}
  </div>
</div>
```

- [ ] **Step 3: Create admin_user_modal.html**

```html
<div id="admin-user-modal" class="modal modal-open">
  <div class="modal-box glass-panel border-(--neon-cyan)/30 max-w-md flex flex-col gap-5">

    <div class="flex items-center justify-between">
      <span class="neon-text font-mono text-sm uppercase tracking-widest">
        {% if mode == "create" %}// ENLIST_PERSONNEL{% else %}// MODIFY_CLEARANCE // {{ user.username | upper }}{% endif %}
      </span>
      <button onclick="closeAegisModal('admin-user-modal')"
              class="text-zinc-500 hover:text-red-400 font-mono text-xs bg-transparent border-none cursor-pointer">✕</button>
    </div>

    <form
      hx-post="{% if mode == 'create' %}/admin/users/create{% else %}/admin/users/{{ user.username }}/edit{% endif %}"
      hx-target="#admin-content-panel"
      hx-on::after-request="closeAegisModal('admin-user-modal')"
      class="flex flex-col gap-4">

      {% if mode == "create" %}
      <div class="flex flex-col gap-1">
        <label class="text-zinc-400 text-[10px] font-mono uppercase tracking-widest">CALLSIGN</label>
        <input type="text" name="new_username" required autocomplete="off"
               class="bg-zinc-900 border border-zinc-700 text-zinc-100 font-mono text-sm px-3 py-2 focus:outline-none focus:border-(--neon-cyan)">
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-zinc-400 text-[10px] font-mono uppercase tracking-widest">ACCESS_KEY</label>
        <input type="password" name="password" required autocomplete="new-password"
               class="bg-zinc-900 border border-zinc-700 text-zinc-100 font-mono text-sm px-3 py-2 focus:outline-none focus:border-(--neon-cyan)">
      </div>
      {% endif %}

      <div class="flex flex-col gap-2">
        <label class="text-zinc-400 text-[10px] font-mono uppercase tracking-widest">FACTION_ASSIGNMENT</label>
        {% if groups %}
        <div class="flex flex-wrap gap-3">
          {% for g in groups %}
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" name="groups" value="{{ g }}"
                   {% if mode == "edit" and user and g in user.groups %}checked{% endif %}
                   class="accent-(--neon-cyan)">
            <span class="text-xs font-mono uppercase text-zinc-300">{{ g }}</span>
          </label>
          {% endfor %}
        </div>
        {% else %}
        <span class="text-zinc-600 text-[10px] font-mono uppercase">NO_FACTIONS_DEFINED</span>
        {% endif %}
      </div>

      <div class="flex justify-end">
        <button type="button" onclick="closeAegisModal('admin-user-modal')"
                class="text-xs font-mono uppercase tracking-widest px-3 py-1.5 border border-zinc-700 hover:border-red-400 hover:text-red-400 transition-colors cursor-pointer bg-transparent mr-2">
          ABORT
        </button>
        <button type="submit"
                class="text-xs font-mono uppercase tracking-widest px-4 py-1.5 border border-zinc-700 hover:border-(--neon-cyan) hover:neon-text transition-colors cursor-pointer bg-transparent">
          {% if mode == "create" %}ENLIST //{% else %}UPDATE_CLEARANCE //{% endif %}
        </button>
      </div>
    </form>
  </div>
  <div class="modal-backdrop" onclick="closeAegisModal('admin-user-modal')"></div>
</div>
```

- [ ] **Step 4: Create admin_group_list.html**

```html
<div class="flex flex-col gap-4">
  <div class="flex justify-between items-center">
    <span class="text-zinc-400 text-xs font-mono uppercase tracking-widest">
      FACTION_INDEX // {{ groups | length }} FACTIONS
    </span>
    <button
      hx-get="/admin/groups/create"
      hx-target="#modal-container"
      class="text-xs font-mono uppercase tracking-widest px-3 py-1.5 border border-zinc-700 hover:border-(--neon-cyan) hover:neon-text transition-colors cursor-pointer bg-transparent">
      + ESTABLISH //
    </button>
  </div>

  {% if error is defined and error %}
  <p class="text-red-400 text-xs font-mono uppercase tracking-widest animate-pulse">!! {{ error }}</p>
  {% endif %}

  <div class="flex flex-col gap-2">
    {% for g in groups %}
    {% set member_count = group_members.get(g, 0) %}
    <div class="glass-panel p-4 flex items-center justify-between gap-4">
      <div class="flex flex-col gap-1">
        <span class="neon-text font-mono text-sm">{{ g | upper }}</span>
        <span class="text-zinc-500 text-[10px] font-mono uppercase tracking-widest">
          {{ member_count }} PERSONNEL
        </span>
      </div>
      {% if member_count == 0 %}
      <button
        hx-post="/admin/groups/{{ g }}/delete"
        hx-target="#admin-content-panel"
        hx-confirm="DISSOLVE FACTION {{ g | upper }}?"
        class="text-xs font-mono uppercase tracking-widest px-2 py-1 border border-zinc-700 hover:border-red-400 hover:text-red-400 transition-colors cursor-pointer bg-transparent">
        DISSOLVE
      </button>
      {% else %}
      <span class="text-zinc-600 text-[10px] font-mono uppercase tracking-widest">ACTIVE</span>
      {% endif %}
    </div>
    {% endfor %}
  </div>
</div>
```

- [ ] **Step 5: Create admin_group_modal.html**

```html
<div id="admin-group-modal" class="modal modal-open">
  <div class="modal-box glass-panel border-(--neon-cyan)/30 max-w-sm flex flex-col gap-5">

    <div class="flex items-center justify-between">
      <span class="neon-text font-mono text-sm uppercase tracking-widest">// ESTABLISH_FACTION</span>
      <button onclick="closeAegisModal('admin-group-modal')"
              class="text-zinc-500 hover:text-red-400 font-mono text-xs bg-transparent border-none cursor-pointer">✕</button>
    </div>

    <form
      hx-post="/admin/groups/create"
      hx-target="#admin-content-panel"
      hx-on::after-request="closeAegisModal('admin-group-modal')"
      class="flex flex-col gap-4">
      <div class="flex flex-col gap-1">
        <label class="text-zinc-400 text-[10px] font-mono uppercase tracking-widest">FACTION_DESIGNATION</label>
        <input type="text" name="group_name" required autocomplete="off"
               class="bg-zinc-900 border border-zinc-700 text-zinc-100 font-mono text-sm px-3 py-2 focus:outline-none focus:border-(--neon-cyan)">
      </div>
      <div class="flex justify-end">
        <button type="button" onclick="closeAegisModal('admin-group-modal')"
                class="text-xs font-mono uppercase tracking-widest px-3 py-1.5 border border-zinc-700 hover:border-red-400 hover:text-red-400 transition-colors cursor-pointer bg-transparent mr-2">
          ABORT
        </button>
        <button type="submit"
                class="text-xs font-mono uppercase tracking-widest px-4 py-1.5 border border-zinc-700 hover:border-(--neon-cyan) hover:neon-text transition-colors cursor-pointer bg-transparent">
          ESTABLISH //
        </button>
      </div>
    </form>
  </div>
  <div class="modal-backdrop" onclick="closeAegisModal('admin-group-modal')"></div>
</div>
```

- [ ] **Step 6: Commit**

```bash
git add templates/components/admin_panel.html \
        templates/components/admin_user_list.html \
        templates/components/admin_user_modal.html \
        templates/components/admin_group_list.html \
        templates/components/admin_group_modal.html
git commit -m "feat(groups): admin panel templates — user list, group list, modals"
```

---

## Task 9: main.py + base.html nav link

**Files:**
- Modify: `main.py`
- Modify: `templates/layouts/base.html`

- [ ] **Step 1: Register admin router in main.py**

In `main.py`, add the import at the top with the other route imports:

```python
from routes import core, archive, editor, pdf, config, oracle, render, settings, auth, admin
```

Then append the router registration after `app.include_router(settings.router)`:

```python
app.include_router(admin.router)       # Admin Panel
```

- [ ] **Step 2: Add SYS_ADMIN nav link to base.html**

In `templates/layouts/base.html`, find this exact block:

```html
                <span class="text-zinc-700">|</span>
                <span class="text-zinc-400 text-[12px] tracking-widest">{{ request.session.get("username", "") | upper }}</span>
```

Replace it with:

```html
                <span class="text-zinc-700">|</span>
                {% if request.session.get("is_admin") %}
                <a href="/admin" hx-get="/admin" hx-push-url="true"
                   class="text-zinc-400 hover:neon-text transition-colors cursor-pointer no-underline">SYS_ADMIN</a>
                <span class="text-zinc-700">|</span>
                {% endif %}
                <span class="text-zinc-400 text-[12px] tracking-widest">{{ request.session.get("username", "") | upper }}</span>
```

- [ ] **Step 3: Verify app starts**

```bash
poetry run python -c "
import main
print('main.py OK')
"
```

Expected: `main.py OK`

- [ ] **Step 4: Commit**

```bash
git add main.py templates/layouts/base.html
git commit -m "feat(groups): register admin router; add SYS_ADMIN nav link for admin users"
```

---

## Task 10: AEGIS COMMS — group-based recipient filtering

> **Prerequisite:** Complete the AEGIS COMMS implementation plan (`docs/superpowers/plans/2026-03-30-aegis-comms.md`) before executing this task.

**Files:**
- Modify: `logic/comms.py`
- Modify: `routes/comms.py`

- [ ] **Step 1: Add allowed_recipients static method to CommsManager**

Inside the `CommsManager` class in `logic/comms.py`, add after `ensure_comms_folders`:

```python
    @staticmethod
    def allowed_recipients(
        sender: str,
        sender_groups: list[str],
        all_users: list,
    ) -> list[str]:
        """Returns usernames reachable by sender.

        A user is reachable if they have the 'admin' group OR share at least
        one group with the sender. The sender is always excluded.
        all_users accepts list[UserRecord] — typed as list to avoid circular import.
        """
        return [
            u.username for u in all_users
            if u.username != sender
            and (
                "admin" in u.groups
                or any(g in sender_groups for g in u.groups)
            )
        ]
```

- [ ] **Step 2: Update _expand_recipients to validate against allowed_usernames**

Replace the existing `_expand_recipients` method in `CommsManager`:

```python
    def _expand_recipients(
        self, recipient_str: str, allowed_usernames: list[str], sender: str
    ) -> list[str]:
        """Expands 'ALL' to allowed_usernames excluding sender. Otherwise validates chosen recipients."""
        if recipient_str.strip().upper() == "ALL":
            return [u for u in allowed_usernames if u != sender]
        chosen = [r.strip() for r in recipient_str.split(",") if r.strip()]
        forbidden = [r for r in chosen if r not in allowed_usernames]
        if forbidden:
            raise CommsError(f"RECIPIENT_NOT_ALLOWED: {','.join(forbidden)}")
        return chosen
```

- [ ] **Step 3: Update send_message signature to use allowed_usernames**

In `CommsManager.send_message`, replace the parameter `all_usernames: list[str]` with `allowed_usernames: list[str]` and update the internal `_expand_recipients` call accordingly:

```python
    async def send_message(
        self,
        sender: str,
        recipient_str: str,
        subject: str,
        body: str,
        allowed_usernames: list[str],
    ) -> MessageRecord:
```

And inside the method body, replace the call:
```python
        recipients = self._expand_recipients(recipient_str, allowed_usernames, sender)
```

- [ ] **Step 4: Update promote_draft to pass allowed_usernames**

In `CommsManager.promote_draft`, replace parameter `all_usernames` with `allowed_usernames` and forward it to `send_message`.

- [ ] **Step 5: Update routes/comms.py compose and send endpoints**

In `routes/comms.py`, add imports at the top:

```python
from logic.auth import auth_service
```

In `GET /comms/compose` handler, compute `allowed` before rendering the template:

```python
    sender_record = await auth_service.get_user(username)
    sender_groups = sender_record.groups if sender_record else []
    all_users = await auth_service.list_users()
    allowed = CommsManager.allowed_recipients(username, sender_groups, all_users)
```

Pass `allowed` to the template context instead of the full user list (replace `all_usernames=...` with `all_usernames=allowed`).

In `POST /comms/send` handler, repeat the same computation before calling `comms_manager.send_message(...)`:

```python
    sender_record = await auth_service.get_user(username)
    sender_groups = sender_record.groups if sender_record else []
    all_users = await auth_service.list_users()
    allowed = CommsManager.allowed_recipients(username, sender_groups, all_users)
    # pass allowed to send_message instead of all_usernames
```

In `POST /comms/draft/send` handler, same pattern — compute `allowed` and pass it to `comms_manager.promote_draft(...)`.

- [ ] **Step 6: Verify**

```bash
poetry run python -c "
from logic.comms import CommsManager

class FakeUser:
    def __init__(self, username, groups):
        self.username = username
        self.groups = groups

users = [
    FakeUser('admin', ['admin']),
    FakeUser('alice', ['crew']),
    FakeUser('bob', ['crew']),
    FakeUser('zara', ['engineering']),
]

# alice (crew) can reach bob (crew) and admin, not zara
allowed = CommsManager.allowed_recipients('alice', ['crew'], users)
assert 'bob' in allowed, 'bob should be reachable'
assert 'admin' in allowed, 'admin should always be reachable'
assert 'zara' not in allowed, 'zara is different group'
assert 'alice' not in allowed, 'sender excluded'
print(f'alice allowed: {allowed}')
print('OK')
"
```

Expected: `alice allowed: ['admin', 'bob']` then `OK`

- [ ] **Step 7: Commit**

```bash
git add logic/comms.py routes/comms.py
git commit -m "feat(groups): AEGIS COMMS filtered by group membership — allowed_recipients, _expand_recipients validation"
```
