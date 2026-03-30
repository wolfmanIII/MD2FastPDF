# AEGIS COMMS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a filesystem-based user-to-user messaging system with multi-recipient support, draft management, live preview, and unread badge notifications.

**Architecture:** Messages are `.md` files with frontmatter stored in per-user `comms/{inbound,outbound,staging}/` directories. `CommsManager` handles all I/O with direct `Path` construction (bypasses `PathSanitizer`). HTMX fragment-based UI with tab navigation, compose modal, and polling badge.

**Tech Stack:** Python 3.13, FastAPI, anyio, Jinja2/HTMX, Tailwind v4, `re` stdlib (no PyYAML), `markdown` + `bleach` (already in deps).

---

## Task 1: CommsError + render_md filter

**Files:**
- Modify: `logic/exceptions.py`
- Modify: `logic/templates.py`

- [ ] **Step 1: Add CommsError to logic/exceptions.py**

Append after the `RenderError` class:

```python
# --- Comms Errors ---

class CommsError(AegisError):
    """Comms message transmission or retrieval failure."""
    def __init__(self, detail: str = "COMMS_ERROR"):
        super().__init__(detail, status_code=400)
```

- [ ] **Step 2: Add render_md filter to logic/templates.py**

Replace entire file content:

```python
import markdown as _md
import bleach
from fastapi.templating import Jinja2Templates
from pathlib import Path

# AEGIS_TEMPLATE_CORE: Unified access to Jinja2 fragments
templates = Jinja2Templates(directory="templates")


def parent_path_filter(value: str) -> str:
    path = Path(value)
    return str(path.parent) if str(path.parent) != "." else "."


_ALLOWED_TAGS: set = bleach.sanitizer.ALLOWED_TAGS | {
    "p", "pre", "code", "h1", "h2", "h3", "h4",
    "table", "thead", "tbody", "tr", "th", "td", "br", "hr",
}


def _render_markdown(value: str) -> str:
    raw = _md.markdown(value, extensions=["fenced_code", "tables"])
    return bleach.clean(raw, tags=_ALLOWED_TAGS, strip=True)


templates.env.filters["parent_path"] = parent_path_filter
templates.env.filters["render_md"] = _render_markdown
```

- [ ] **Step 3: Verify the app still starts**

```bash
cd /home/spacewolf/Progetti/MD2FastPDF
poetry run python -c "from logic.templates import templates; from logic.exceptions import CommsError; print('OK')"
```

Expected output: `OK`

- [ ] **Step 4: Commit**

```bash
git add logic/exceptions.py logic/templates.py
git commit -m "feat(comms): add CommsError + render_md Jinja2 filter"
```

---

## Task 2: FrontmatterParser + MessageRecord

**Files:**
- Create: `logic/comms.py`

- [ ] **Step 1: Create logic/comms.py with FrontmatterParser and MessageRecord**

```python
"""
AEGIS_COMMS_PROTOCOL: User-to-user secure message transmission system.

FrontmatterParser: Parses and serializes Markdown frontmatter (no PyYAML).
MessageRecord: Immutable value object for a single transmission.
CommsManager: Async I/O across user workspaces. (added in subsequent tasks)
"""
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import anyio

from config.settings import settings
from logic.exceptions import CommsError, NotFoundError, AccessDeniedError

_ADMIN_USERNAME: str = "admin"
_COMMS_SUBFOLDERS: tuple[str, ...] = ("inbound", "outbound", "staging")


@dataclass(frozen=True)
class MessageRecord:
    """Immutable representation of a single comms transmission."""
    id: str
    sender: str
    recipient: str      # comma-separated usernames, or "ALL"
    subject: str
    timestamp: str      # ISO8601
    read: bool
    body: str
    filename: str       # basename only, no path

    @property
    def recipients(self) -> list[str]:
        """Expands recipient string into a list. Does not expand 'ALL'."""
        return [r.strip() for r in self.recipient.split(",")]


class FrontmatterParser:
    """Parses and serializes Markdown YAML-lite frontmatter without external deps.

    Supported scalar types: str, bool (true/false). No nested structures.
    Returns None from parse() on malformed input — callers must handle gracefully.
    """

    _DELIMITER: str = "---"
    _BOOL_MAP: dict[str, bool] = {"true": True, "false": False}

    @classmethod
    def parse(cls, raw: str) -> Optional[tuple[dict, str]]:
        """Returns (meta_dict, body_str) or None if format is invalid."""
        lines = raw.split("\n")
        if not lines or lines[0].strip() != cls._DELIMITER:
            return None
        try:
            end = lines.index(cls._DELIMITER, 1)
        except ValueError:
            return None
        meta: dict = {}
        for line in lines[1:end]:
            m = re.match(r"^(\w+):\s*(.*)", line)
            if m:
                meta[m.group(1)] = cls._parse_value(m.group(2))
        body = "\n".join(lines[end + 1:]).strip()
        return meta, body

    @classmethod
    def serialize(cls, meta: dict, body: str) -> str:
        """Builds the full file content from meta dict and body string."""
        lines = [cls._DELIMITER]
        for k, v in meta.items():
            lines.append(f"{k}: {str(v).lower() if isinstance(v, bool) else v}")
        lines.append(cls._DELIMITER)
        lines.append("")
        lines.append(body)
        return "\n".join(lines)

    @classmethod
    def _parse_value(cls, raw: str) -> str | bool:
        """Converts raw string value to Python bool or stripped str."""
        stripped = raw.strip()
        return cls._BOOL_MAP.get(stripped.lower(), stripped)
```

- [ ] **Step 2: Verify parse/serialize round-trip**

```bash
poetry run python -c "
from logic.comms import FrontmatterParser, MessageRecord

raw = '''---
id: abc123
from: admin
to: user1,user2
subject: Test mission
timestamp: 2026-03-30T14:00:00+00:00
read: false
---

Hello world
'''

result = FrontmatterParser.parse(raw)
assert result is not None, 'parse returned None'
meta, body = result
assert meta['read'] == False
assert meta['from'] == 'admin'
assert body == 'Hello world'

# Round-trip
serialized = FrontmatterParser.serialize(meta, body)
result2 = FrontmatterParser.parse(serialized)
assert result2 is not None
print('FrontmatterParser OK')
"
```

Expected: `FrontmatterParser OK`

- [ ] **Step 3: Commit**

```bash
git add logic/comms.py
git commit -m "feat(comms): FrontmatterParser + MessageRecord"
```

---

## Task 3: CommsManager — path resolution + folder lifecycle

**Files:**
- Modify: `logic/comms.py`

- [ ] **Step 1: Append CommsManager class to logic/comms.py**

Add after `FrontmatterParser`:

```python
class CommsManager:
    """Async I/O for comms operations across user workspaces.

    Path resolution bypasses PathSanitizer intentionally — cross-workspace
    writes require direct Path construction from workspace_base config.
    """

    def _workspace_root(self, username: str) -> Path:
        """Admin maps to Path.home(). Others to workspace_base/username."""
        if username == _ADMIN_USERNAME:
            return Path.home().resolve()
        base = Path(settings.get("workspace_base", str(Path.home() / "sc-archive")))
        return (base / username).resolve()

    def _comms_root(self, username: str) -> Path:
        return self._workspace_root(username) / "comms"

    def _inbound(self, username: str) -> Path:
        return self._comms_root(username) / "inbound"

    def _outbound(self, username: str) -> Path:
        return self._comms_root(username) / "outbound"

    def _staging(self, username: str) -> Path:
        return self._comms_root(username) / "staging"

    def create_comms_folders_sync(self, username: str) -> None:
        """Creates inbound/, outbound/, staging/. Sync — for bootstrap only."""
        for sub in _COMMS_SUBFOLDERS:
            (self._comms_root(username) / sub).mkdir(parents=True, exist_ok=True)

    async def create_comms_folders(self, username: str) -> None:
        """Async variant — called from AuthService.create_user()."""
        for sub in _COMMS_SUBFOLDERS:
            await anyio.Path(self._comms_root(username) / sub).mkdir(
                parents=True, exist_ok=True
            )

    async def ensure_comms_folders(self, username: str) -> None:
        """Idempotent — called at GET /comms entry point for existing users."""
        await self.create_comms_folders(username)
```

- [ ] **Step 2: Verify path resolution**

```bash
poetry run python -c "
from logic.comms import CommsManager
from pathlib import Path
import os

cm = CommsManager()

# Admin root must be home
admin_root = cm._workspace_root('admin')
assert admin_root == Path.home().resolve(), f'Admin root wrong: {admin_root}'

# Regular user must be under workspace_base
user_root = cm._workspace_root('testuser')
assert 'testuser' in str(user_root), f'User root wrong: {user_root}'

print('Path resolution OK')
print(f'  admin root: {admin_root}')
print(f'  user root:  {user_root}')
"
```

Expected: `Path resolution OK` with both paths printed.

- [ ] **Step 3: Commit**

```bash
git add logic/comms.py
git commit -m "feat(comms): CommsManager path resolution + folder lifecycle"
```

---

## Task 4: CommsManager — read operations

**Files:**
- Modify: `logic/comms.py`

- [ ] **Step 1: Add static helpers + read methods to CommsManager**

Inside the `CommsManager` class, after `ensure_comms_folders`, add:

```python
    @staticmethod
    def _build_filename(timestamp: datetime, msg_id: str, subject: str) -> str:
        """Produces: {YYYYMMDDTHHmmss}_{id[:8]}_{subject_slug}.md"""
        ts = timestamp.strftime("%Y%m%dT%H%M%S")
        slug = CommsManager._slugify(subject)
        return f"{ts}_{msg_id[:8]}_{slug}.md"

    @staticmethod
    def _slugify(text: str) -> str:
        """Lowercase ASCII slug, max 32 chars."""
        slug = re.sub(r"[^a-z0-9]+", "_", text.lower().strip())
        return slug[:32].strip("_") or "msg"

    def _expand_recipients(
        self, recipient_str: str, all_usernames: list[str], sender: str
    ) -> list[str]:
        """Expands 'ALL' to all users except sender. Otherwise splits by comma."""
        if recipient_str.strip().upper() == "ALL":
            return [u for u in all_usernames if u != sender]
        return [r.strip() for r in recipient_str.split(",") if r.strip()]

    async def list_folder(self, username: str, folder: str) -> list[MessageRecord]:
        """Returns all messages in folder, sorted newest-first."""
        folder_path = self._comms_root(username) / folder
        if not await anyio.Path(folder_path).exists():
            return []

        def _scan() -> list[Path]:
            return sorted(
                [p for p in folder_path.iterdir() if p.suffix == ".md"],
                key=lambda p: p.name,
                reverse=True,
            )

        files = await anyio.to_thread.run_sync(_scan)
        records: list[MessageRecord] = []
        for f in files:
            rec = await self._read_message_file(f)
            if rec is not None:
                records.append(rec)
        return records

    async def get_message(
        self, username: str, folder: str, filename: str
    ) -> MessageRecord:
        """Reads a single message. Raises NotFoundError if absent."""
        path = self._comms_root(username) / folder / filename
        if not await anyio.Path(path).exists():
            raise NotFoundError(f"MESSAGE_NOT_FOUND: {filename}")
        rec = await self._read_message_file(path)
        if rec is None:
            raise CommsError(f"MESSAGE_PARSE_FAILED: {filename}")
        return rec

    async def count_unread(self, username: str) -> int:
        """Returns count of unread messages in inbound/."""
        messages = await self.list_folder(username, "inbound")
        return sum(1 for m in messages if not m.read)

    async def _read_message_file(self, path: Path) -> Optional[MessageRecord]:
        """Reads and parses a single .md file. Returns None on failure."""
        try:
            content = await anyio.Path(path).read_text(encoding="utf-8")
        except (IOError, OSError):
            return None
        parsed = FrontmatterParser.parse(content)
        if parsed is None:
            return None
        meta, body = parsed
        try:
            return MessageRecord(
                id=str(meta.get("id", "")),
                sender=str(meta.get("from", "")),
                recipient=str(meta.get("to", "")),
                subject=str(meta.get("subject", "")),
                timestamp=str(meta.get("timestamp", "")),
                read=bool(meta.get("read", False)),
                body=body,
                filename=path.name,
            )
        except (KeyError, TypeError):
            return None
```

- [ ] **Step 2: Verify slugify and filename builder**

```bash
poetry run python -c "
from logic.comms import CommsManager
from datetime import datetime, timezone

cm = CommsManager()
ts = datetime(2026, 3, 30, 14, 0, 0, tzinfo=timezone.utc)
fn = cm._build_filename(ts, 'a1b2c3d4-xxxx', 'Test Mission Alpha')
assert fn == '20260330T140000_a1b2c3_test_mission_alpha.md', f'Got: {fn}'
print(f'Filename: {fn}')
print('Read helpers OK')
"
```

Expected: filename printed, `Read helpers OK`

- [ ] **Step 3: Commit**

```bash
git add logic/comms.py
git commit -m "feat(comms): CommsManager read operations + _read_message_file"
```

---

## Task 5: CommsManager — write operations

**Files:**
- Modify: `logic/comms.py`

- [ ] **Step 1: Add write methods to CommsManager**

Inside `CommsManager`, after `_read_message_file`, add:

```python
    async def send_message(
        self,
        sender: str,
        recipient_str: str,
        subject: str,
        body: str,
        all_usernames: list[str],
    ) -> MessageRecord:
        """Dual-write: sender outbound + each recipient's inbound."""
        now = datetime.now(timezone.utc)
        msg_id = str(uuid.uuid4())
        filename = self._build_filename(now, msg_id, subject)
        record = MessageRecord(
            id=msg_id,
            sender=sender,
            recipient=recipient_str.strip(),
            subject=subject,
            timestamp=now.isoformat(),
            read=False,
            body=body,
            filename=filename,
        )
        await self._write_message_file(self._outbound(sender) / filename, record)
        recipients = self._expand_recipients(recipient_str, all_usernames, sender)
        home = Path.home().resolve()
        for recipient in recipients:
            inbound_path = self._inbound(recipient) / filename
            if not str(inbound_path.resolve()).startswith(str(home)):
                raise AccessDeniedError(
                    f"COMMS: Recipient path outside home boundary: {recipient}"
                )
            await self.ensure_comms_folders(recipient)
            await self._write_message_file(inbound_path, record)
        return record

    async def mark_read(self, username: str, folder: str, filename: str) -> None:
        """Toggles read: true in frontmatter. No-op if already read or not found."""
        path = self._comms_root(username) / folder / filename
        if not await anyio.Path(path).exists():
            return
        rec = await self._read_message_file(path)
        if rec is None or rec.read:
            return
        meta = {
            "id": rec.id,
            "from": rec.sender,
            "to": rec.recipient,
            "subject": rec.subject,
            "timestamp": rec.timestamp,
            "read": True,
        }
        await self._write_message_file(path, rec)
        content = FrontmatterParser.serialize(meta, rec.body)
        tmp = path.with_suffix(".tmp")
        async with await anyio.open_file(tmp, "w", encoding="utf-8") as f:
            await f.write(content)
        await anyio.to_thread.run_sync(lambda: tmp.rename(path))

    async def delete_message(
        self, username: str, folder: str, filename: str
    ) -> None:
        """Permanently removes a message file."""
        path = self._comms_root(username) / folder / filename
        if not await anyio.Path(path).exists():
            raise NotFoundError(f"MESSAGE_NOT_FOUND: {filename}")
        await anyio.to_thread.run_sync(path.unlink)

    async def save_draft(
        self,
        sender: str,
        recipient_str: str,
        subject: str,
        body: str,
        draft_filename: Optional[str] = None,
    ) -> MessageRecord:
        """Writes or overwrites a draft in sender's staging/."""
        now = datetime.now(timezone.utc)
        msg_id = str(uuid.uuid4())
        filename = draft_filename or self._build_filename(now, msg_id, subject or "draft")
        record = MessageRecord(
            id=msg_id,
            sender=sender,
            recipient=recipient_str.strip(),
            subject=subject,
            timestamp=now.isoformat(),
            read=False,
            body=body,
            filename=filename,
        )
        await self._write_message_file(self._staging(sender) / filename, record)
        return record

    async def promote_draft(
        self, sender: str, draft_filename: str, all_usernames: list[str]
    ) -> MessageRecord:
        """Sends a draft: reads staging/, calls send_message(), deletes draft."""
        path = self._staging(sender) / draft_filename
        if not await anyio.Path(path).exists():
            raise NotFoundError(f"DRAFT_NOT_FOUND: {draft_filename}")
        rec = await self._read_message_file(path)
        if rec is None:
            raise CommsError(f"DRAFT_PARSE_FAILED: {draft_filename}")
        sent = await self.send_message(
            sender, rec.recipient, rec.subject, rec.body, all_usernames
        )
        await anyio.to_thread.run_sync(path.unlink)
        return sent

    async def _write_message_file(self, path: Path, record: MessageRecord) -> None:
        """Atomic write: .tmp → rename. Ensures no partial reads."""
        meta = {
            "id": record.id,
            "from": record.sender,
            "to": record.recipient,
            "subject": record.subject,
            "timestamp": record.timestamp,
            "read": record.read,
        }
        content = FrontmatterParser.serialize(meta, record.body)
        tmp = path.with_suffix(".tmp")
        async with await anyio.open_file(tmp, "w", encoding="utf-8") as f:
            await f.write(content)
        await anyio.to_thread.run_sync(lambda: tmp.rename(path))


comms_manager = CommsManager()
```

Note: `mark_read` has a redundant `_write_message_file` call — remove it. The correct `mark_read` is:

```python
    async def mark_read(self, username: str, folder: str, filename: str) -> None:
        """Toggles read: true in frontmatter. No-op if already read or not found."""
        path = self._comms_root(username) / folder / filename
        if not await anyio.Path(path).exists():
            return
        rec = await self._read_message_file(path)
        if rec is None or rec.read:
            return
        meta = {
            "id": rec.id,
            "from": rec.sender,
            "to": rec.recipient,
            "subject": rec.subject,
            "timestamp": rec.timestamp,
            "read": True,
        }
        content = FrontmatterParser.serialize(meta, rec.body)
        tmp = path.with_suffix(".tmp")
        async with await anyio.open_file(tmp, "w", encoding="utf-8") as f:
            await f.write(content)
        await anyio.to_thread.run_sync(lambda: tmp.rename(path))
```

- [ ] **Step 2: Verify import of complete module**

```bash
poetry run python -c "
from logic.comms import comms_manager, CommsManager, MessageRecord, FrontmatterParser
print('logic/comms.py import OK')
print(f'  CommsManager methods: {[m for m in dir(comms_manager) if not m.startswith(\"__\")]}')
"
```

Expected: import OK, method list printed.

- [ ] **Step 3: Commit**

```bash
git add logic/comms.py
git commit -m "feat(comms): CommsManager write operations — send, draft, mark_read, delete"
```

---

## Task 6: logic/auth.py — list_usernames + comms folder creation

**Files:**
- Modify: `logic/auth.py`

- [ ] **Step 1: Add list_usernames to UserStoreProtocol**

In `UserStoreProtocol`, after `async def update_root(...)`:

```python
    async def list_usernames(self) -> list[str]: ...
```

In `SyncUserStoreProtocol`, after `def save_user_sync(...)`:

```python
    def list_usernames_sync(self) -> list[str]: ...
```

- [ ] **Step 2: Implement list_usernames on UserStore**

In `UserStore`, after `update_root`:

```python
    async def list_usernames(self) -> list[str]:
        """Returns all registered usernames."""
        return list((await self._aload()).keys())

    def list_usernames_sync(self) -> list[str]:
        """Sync variant — for bootstrap/CLI paths."""
        return list(self._load().keys())
```

- [ ] **Step 3: Call create_comms_folders in AuthService.create_user**

In `AuthService.create_user`, after `await self._store.save_user(record)`:

```python
        from logic.comms import comms_manager  # local import: avoids circular dep
        await comms_manager.create_comms_folders(username)
```

In `AuthService.create_user_sync`, after `self._sync_store.save_user_sync(record)`:

```python
        from logic.comms import comms_manager  # local import: avoids circular dep
        comms_manager.create_comms_folders_sync(username)
```

- [ ] **Step 4: Verify auth still works**

```bash
poetry run python -c "
from logic.auth import auth_service, _store
import asyncio

async def check():
    users = await _store.list_usernames()
    print(f'Registered users: {users}')

asyncio.run(check())
print('auth.py OK')
"
```

Expected: list of current users printed, `auth.py OK`

- [ ] **Step 5: Commit**

```bash
git add logic/auth.py
git commit -m "feat(comms): auth.py — list_usernames + auto-create comms folders on user creation"
```

---

## Task 7: routes/comms.py

**Files:**
- Create: `routes/comms.py`

- [ ] **Step 1: Create routes/comms.py**

```python
"""
AEGIS_COMMS_ROUTER: Signal transmission and reception endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse

from logic.comms import comms_manager
from logic.auth import _store
from logic.templates import templates
from logic.conversion import MarkdownRenderer
from routes.deps import get_current_user

router = APIRouter(prefix="/comms", tags=["Aegis Comms"])

_md_renderer = MarkdownRenderer()


@router.get("", response_class=HTMLResponse)
async def comms_hub(
    request: Request,
    tab: str = "inbound",
    username: str = Depends(get_current_user),
) -> HTMLResponse:
    """Main COMMS hub. Ensures comms folders exist for existing users."""
    await comms_manager.ensure_comms_folders(username)
    messages = await comms_manager.list_folder(username, tab)
    context = {
        "request": request,
        "tab": tab,
        "messages": messages,
        "username": username,
        "title": "SC-ARCHIVE // COMMS",
        "component_template": "components/comms_hub.html",
    }
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request=request, name="components/comms_hub.html", context=context
        )
    return templates.TemplateResponse(
        request=request, name="shell.html", context=context
    )


@router.get("/inbound", response_class=HTMLResponse)
async def get_inbound(
    request: Request, username: str = Depends(get_current_user)
) -> HTMLResponse:
    messages = await comms_manager.list_folder(username, "inbound")
    return templates.TemplateResponse(
        request=request,
        name="components/comms_message_list.html",
        context={"request": request, "messages": messages, "folder": "inbound"},
    )


@router.get("/outbound", response_class=HTMLResponse)
async def get_outbound(
    request: Request, username: str = Depends(get_current_user)
) -> HTMLResponse:
    messages = await comms_manager.list_folder(username, "outbound")
    return templates.TemplateResponse(
        request=request,
        name="components/comms_message_list.html",
        context={"request": request, "messages": messages, "folder": "outbound"},
    )


@router.get("/staging", response_class=HTMLResponse)
async def get_staging(
    request: Request, username: str = Depends(get_current_user)
) -> HTMLResponse:
    messages = await comms_manager.list_folder(username, "staging")
    return templates.TemplateResponse(
        request=request,
        name="components/comms_message_list.html",
        context={"request": request, "messages": messages, "folder": "staging"},
    )


@router.get("/message", response_class=HTMLResponse)
async def read_message(
    request: Request,
    folder: str,
    filename: str,
    username: str = Depends(get_current_user),
) -> HTMLResponse:
    """Reads a single message and marks it as read."""
    message = await comms_manager.get_message(username, folder, filename)
    await comms_manager.mark_read(username, folder, filename)
    return templates.TemplateResponse(
        request=request,
        name="components/comms_message_reader.html",
        context={"request": request, "message": message, "folder": folder},
    )


@router.get("/compose", response_class=HTMLResponse)
async def compose_form(
    request: Request,
    reply_to: Optional[str] = None,
    username: str = Depends(get_current_user),
) -> HTMLResponse:
    """Compose modal. reply_to format: 'folder/filename'."""
    all_users = await _store.list_usernames()
    recipients = [u for u in all_users if u != username]
    original: Optional[object] = None
    if reply_to:
        parts = reply_to.split("/", 1)
        if len(parts) == 2:
            try:
                original = await comms_manager.get_message(username, parts[0], parts[1])
            except Exception:
                original = None
    return templates.TemplateResponse(
        request=request,
        name="components/comms_compose_modal.html",
        context={
            "request": request,
            "recipients": recipients,
            "original": original,
            "reply_to": reply_to,
        },
    )


@router.post("/preview", response_class=HTMLResponse)
async def preview_markdown(
    request: Request,
    body: str = Form(default=""),
) -> HTMLResponse:
    """Live Markdown preview fragment for the compose modal."""
    html = _md_renderer.render(body) if body.strip() else ""
    return templates.TemplateResponse(
        request=request,
        name="components/comms_preview.html",
        context={"request": request, "html": html},
    )


@router.post("/send", response_class=HTMLResponse)
async def send_message(
    request: Request,
    recipients: list[str] = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    username: str = Depends(get_current_user),
) -> HTMLResponse:
    all_users = await _store.list_usernames()
    recipient_str = "ALL" if recipients == ["ALL"] else ",".join(recipients)
    await comms_manager.send_message(username, recipient_str, subject, body, all_users)
    messages = await comms_manager.list_folder(username, "outbound")
    return templates.TemplateResponse(
        request=request,
        name="components/comms_message_list.html",
        context={
            "request": request,
            "messages": messages,
            "folder": "outbound",
            "notification": ">> SIGNAL_TRANSMITTED // DELIVERY_CONFIRMED",
        },
    )


@router.post("/draft/save", response_class=HTMLResponse)
async def save_draft(
    request: Request,
    recipients: list[str] = Form(default=[]),
    subject: str = Form(default=""),
    body: str = Form(default=""),
    draft_filename: str = Form(default=""),
    username: str = Depends(get_current_user),
) -> HTMLResponse:
    recipient_str = ",".join(recipients) if recipients else ""
    await comms_manager.save_draft(
        username, recipient_str, subject, body, draft_filename or None
    )
    return HTMLResponse(
        content='<div class="text-[10px] neon-text tracking-widest">▶ BUFFER_SECURED // DRAFT_RETAINED</div>'
    )


@router.post("/draft/send", response_class=HTMLResponse)
async def send_draft(
    request: Request,
    draft_filename: str = Form(...),
    username: str = Depends(get_current_user),
) -> HTMLResponse:
    all_users = await _store.list_usernames()
    await comms_manager.promote_draft(username, draft_filename, all_users)
    messages = await comms_manager.list_folder(username, "outbound")
    return templates.TemplateResponse(
        request=request,
        name="components/comms_message_list.html",
        context={
            "request": request,
            "messages": messages,
            "folder": "outbound",
            "notification": ">> BUFFER_FLUSHED // SIGNAL_TRANSMITTED",
        },
    )


@router.post("/delete", response_class=HTMLResponse)
async def delete_message(
    request: Request,
    folder: str = Form(...),
    filename: str = Form(...),
    username: str = Depends(get_current_user),
) -> HTMLResponse:
    await comms_manager.delete_message(username, folder, filename)
    messages = await comms_manager.list_folder(username, folder)
    return templates.TemplateResponse(
        request=request,
        name="components/comms_message_list.html",
        context={
            "request": request,
            "messages": messages,
            "folder": folder,
            "notification": ">> SIGNAL_PURGED // RECORD_EXPUNGED",
        },
    )


@router.get("/unread-count", response_class=HTMLResponse)
async def unread_count_badge(
    request: Request,
    username: str = Depends(get_current_user),
) -> HTMLResponse:
    """Polled every 30s from navbar for unread badge + toast trigger."""
    count = await comms_manager.count_unread(username)
    return templates.TemplateResponse(
        request=request,
        name="components/comms_unread_badge.html",
        context={"request": request, "count": count},
    )
```

- [ ] **Step 2: Verify import**

```bash
poetry run python -c "from routes.comms import router; print(f'Routes: {[r.path for r in router.routes]}')"
```

Expected: list of 12 route paths printed.

- [ ] **Step 3: Commit**

```bash
git add routes/comms.py
git commit -m "feat(comms): routes/comms.py — all 12 endpoints"
```

---

## Task 8: main.py router registration + base.html

**Files:**
- Modify: `main.py`
- Modify: `templates/layouts/base.html`

- [ ] **Step 1: Register comms router in main.py**

In `main.py`, update the imports line:

```python
from routes import core, archive, editor, pdf, config, oracle, render, settings, auth, comms
```

After `app.include_router(settings.router)`, add:

```python
app.include_router(comms.router)     # Comms Protocol
```

- [ ] **Step 2: Add toast container to base.html**

In `templates/layouts/base.html`, after `<div id="modal-container"></div>`, add:

```html
<div id="toast-container" class="fixed bottom-6 right-6 z-50 flex flex-col items-end space-y-2 pointer-events-none"></div>
```

- [ ] **Step 3: Add COMMS nav link + unread badge to base.html**

In the `<nav>` section of `base.html`, after the `SYS_ACTIVE` span block and before the username span, add:

```html
                <span class="text-zinc-700">|</span>
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

- [ ] **Step 4: Start app and verify /comms loads**

```bash
cd /home/spacewolf/Progetti/MD2FastPDF && poetry run uvicorn main:app --port 8001 &
sleep 3
curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/comms
kill %1
```

Expected: `302` (redirect to login — unauthenticated access is correctly blocked).

- [ ] **Step 5: Commit**

```bash
git add main.py templates/layouts/base.html
git commit -m "feat(comms): register router, add nav link + toast container to base.html"
```

---

## Task 9: Templates — comms_hub + comms_message_list

**Files:**
- Create: `templates/components/comms_hub.html`
- Create: `templates/components/comms_message_list.html`

- [ ] **Step 1: Create comms_hub.html**

```html
<div class="space-y-6">
    <div class="flex items-center justify-between py-2 border-b border-white/5">
        <div>
            <h1 class="text-2xl font-bold text-zinc-100 tracking-tight">COMMS_ARRAY // SIGNAL MANAGEMENT</h1>
            <p class="text-zinc-500 text-sm mt-1">SECURE INTER-OPERATOR COMMUNICATION PROTOCOL</p>
        </div>
        <button hx-get="/comms/compose" hx-target="#modal-container"
            class="btn-ghost text-[10px] rounded-sm focus:outline-none">
            OPEN_CHANNEL //
        </button>
    </div>

    <!-- Tab bar -->
    <div class="flex space-x-1 border-b border-white/5">
        <button hx-get="/comms/inbound" hx-target="#comms-content-panel"
            class="text-[10px] tracking-widest uppercase px-4 py-2 transition-colors
                {% if tab == 'inbound' %}neon-text border-b-2 border-(--neon-cyan){% else %}text-zinc-500 hover:text-zinc-300{% endif %}">
            RECEPTION_ARRAY
        </button>
        <button hx-get="/comms/outbound" hx-target="#comms-content-panel"
            class="text-[10px] tracking-widest uppercase px-4 py-2 transition-colors
                {% if tab == 'outbound' %}neon-text border-b-2 border-(--neon-cyan){% else %}text-zinc-500 hover:text-zinc-300{% endif %}">
            OUTBOUND_LOG
        </button>
        <button hx-get="/comms/staging" hx-target="#comms-content-panel"
            class="text-[10px] tracking-widest uppercase px-4 py-2 transition-colors
                {% if tab == 'staging' %}neon-text border-b-2 border-(--neon-cyan){% else %}text-zinc-500 hover:text-zinc-300{% endif %}">
            STAGING_BUFFER
        </button>
    </div>

    <!-- Content panel -->
    <div id="comms-content-panel">
        {% include 'components/comms_message_list.html' %}
    </div>
</div>
```

- [ ] **Step 2: Create comms_message_list.html**

```html
{% if notification is defined and notification %}
<div class="text-[10px] neon-text tracking-widest mb-4 animate-pulse">{{ notification }}</div>
{% endif %}

{% if messages %}
<div class="space-y-2">
    {% for msg in messages %}
    <div class="glass-panel glass-panel-hover p-4 cursor-pointer tracking-widest uppercase
            {% if not msg.read and folder == 'inbound' %}border-l-2 border-(--neon-cyan){% endif %}"
        hx-get="/comms/message?folder={{ folder }}&filename={{ msg.filename }}"
        hx-target="#comms-content-panel">
        <div class="flex items-start justify-between gap-4">
            <div class="space-y-1 min-w-0">
                <div class="flex items-center space-x-2">
                    {% if not msg.read and folder == 'inbound' %}
                    <span class="w-2 h-2 rounded-full neon-bg shrink-0 animate-pulse"></span>
                    {% endif %}
                    <span class="text-[11px] font-bold text-zinc-100 truncate">{{ msg.subject }}</span>
                </div>
                <div class="text-[10px] text-zinc-500">
                    {% if folder == 'inbound' %}
                    FROM: <span class="text-zinc-400">{{ msg.sender }}</span>
                    {% elif folder == 'outbound' %}
                    TO: <span class="text-zinc-400">{{ msg.recipient }}</span>
                    {% else %}
                    TO: <span class="text-zinc-400">{{ msg.recipient }}</span>
                    <span class="text-zinc-700 ml-2">// DRAFT</span>
                    {% endif %}
                </div>
            </div>
            <div class="flex flex-col items-end shrink-0 space-y-1">
                <span class="text-[9px] text-zinc-600 font-mono">
                    {{ msg.timestamp[:10] }}
                </span>
                {% if folder == 'staging' %}
                <form hx-post="/comms/draft/send" hx-target="#comms-content-panel" class="m-0">
                    <input type="hidden" name="draft_filename" value="{{ msg.filename }}">
                    <button type="submit" onclick="event.stopPropagation()"
                        class="text-[9px] tracking-widest uppercase neon-text hover:neon-bg hover:text-[#0f172a] border border-(--glass-border) px-2 py-0.5 rounded-sm transition-colors">
                        TRANSMIT_BUFFERED
                    </button>
                </form>
                {% endif %}
            </div>
        </div>
    </div>
    {% endfor %}
</div>
{% else %}
<div class="glass-panel p-12 text-center tracking-widest uppercase">
    <p class="text-zinc-600 text-[10px]">NO_SIGNALS_DETECTED</p>
</div>
{% endif %}
```

- [ ] **Step 3: Commit**

```bash
git add templates/components/comms_hub.html templates/components/comms_message_list.html
git commit -m "feat(comms): comms_hub + comms_message_list templates"
```

---

## Task 10: Templates — comms_message_reader + comms_compose_modal

**Files:**
- Create: `templates/components/comms_message_reader.html`
- Create: `templates/components/comms_compose_modal.html`

- [ ] **Step 1: Create comms_message_reader.html**

```html
<div class="glass-panel p-6 space-y-6 tracking-widest uppercase">
    <!-- Signal header -->
    <div class="border-b border-(--glass-border) pb-4 space-y-3">
        <h2 class="text-sm font-bold neon-text">SIGNAL_RECEIVED // DECODING</h2>
        <div class="grid grid-cols-2 gap-x-6 gap-y-1 text-[10px]">
            <div><span class="text-zinc-500">FROM:</span> <span class="text-zinc-300 font-bold">{{ message.sender }}</span></div>
            <div class="truncate"><span class="text-zinc-500">TO:</span> <span class="text-zinc-300">{{ message.recipient }}</span></div>
            <div class="col-span-2"><span class="text-zinc-500">SUBJECT:</span> <span class="text-zinc-100 font-bold">{{ message.subject }}</span></div>
            <div class="col-span-2"><span class="text-zinc-500">TIMESTAMP:</span> <span class="text-zinc-400 font-mono normal-case">{{ message.timestamp[:16] | replace("T", " ") }}</span></div>
        </div>
    </div>

    <!-- Body -->
    <div class="prose prose-invert prose-sm max-w-none text-zinc-300 leading-relaxed normal-case text-sm">
        {{ message.body | render_md | safe }}
    </div>

    <!-- Actions -->
    <div class="flex items-center justify-between pt-4 border-t border-(--glass-border)">
        <button hx-get="/comms/compose?reply_to={{ folder }}/{{ message.filename }}"
            hx-target="#modal-container"
            class="btn-ghost text-[10px] rounded-sm focus:outline-none">
            OPEN_RESPONSE
        </button>
        <form hx-post="/comms/delete" hx-target="#comms-content-panel" class="m-0">
            <input type="hidden" name="folder" value="{{ folder }}">
            <input type="hidden" name="filename" value="{{ message.filename }}">
            <button type="submit"
                class="text-[10px] tracking-widest uppercase text-red-500 hover:text-red-300 transition-colors border border-red-900/40 hover:border-red-500/60 px-4 py-2 rounded-sm">
                PURGE_SIGNAL
            </button>
        </form>
    </div>
</div>
```

- [ ] **Step 2: Create comms_compose_modal.html**

```html
<div id="comms-compose-modal"
    class="modal modal-open bg-black/80 backdrop-blur-sm z-100 flex items-center justify-center fixed inset-0">
    <div class="modal-box glass-panel w-full max-w-4xl max-h-[90vh] overflow-y-auto p-6 space-y-4">

        <div class="flex items-center justify-between border-b border-(--glass-border) pb-3">
            <h2 class="text-sm font-bold neon-text tracking-widest uppercase">SIGNAL_COMPOSER // NEW_TRANSMISSION</h2>
            <button onclick="closeAegisModal('comms-compose-modal')"
                class="text-zinc-500 hover:neon-text transition-colors text-xl leading-none">✕</button>
        </div>

        <form hx-post="/comms/send" hx-target="#comms-content-panel"
              hx-on::after-request="closeAegisModal('comms-compose-modal')"
              class="space-y-4">

            <!-- Recipients -->
            <div class="space-y-2">
                <div class="flex items-center justify-between">
                    <label class="text-[10px] text-zinc-400 uppercase tracking-widest font-bold">TO:</label>
                    <button type="button" id="select-all-btn" onclick="toggleAllRecipients()"
                        class="text-[9px] tracking-widest uppercase text-zinc-500 hover:neon-text transition-colors">
                        SELECT ALL
                    </button>
                </div>
                <div class="grid grid-cols-3 gap-2 max-h-28 overflow-y-auto border border-(--glass-border) rounded-sm p-3">
                    {% for r in recipients %}
                    <label class="flex items-center space-x-2 text-[10px] text-zinc-400 tracking-widest uppercase cursor-pointer hover:text-zinc-200 transition-colors">
                        <input type="checkbox" name="recipients" value="{{ r }}"
                            class="recipient-checkbox accent-(--neon-cyan)"
                            {% if original and r == original.sender %}checked{% endif %}>
                        <span>{{ r }}</span>
                    </label>
                    {% endfor %}
                </div>
            </div>

            <!-- Subject -->
            <div class="space-y-1">
                <label class="text-[10px] text-zinc-400 uppercase tracking-widest font-bold">SUBJECT:</label>
                <input type="text" name="subject" class="w-full"
                    value="{% if original %}Re: {{ original.subject }}{% endif %}"
                    placeholder="TRANSMISSION_SUBJECT...">
            </div>

            <!-- Body + Preview side-by-side -->
            <div class="grid grid-cols-2 gap-4">
                <div class="space-y-1">
                    <label class="text-[10px] text-zinc-400 uppercase tracking-widest font-bold">BODY:</label>
                    <textarea name="body" id="comms-body"
                        class="w-full resize-none font-mono text-[11px]" style="height: 200px;"
                        placeholder="AWAITING_TRANSMISSION..."
                        hx-post="/comms/preview"
                        hx-trigger="input changed delay:300ms"
                        hx-target="#comms-preview-panel"
                        hx-swap="innerHTML"></textarea>
                </div>
                <div class="space-y-1">
                    <label class="text-[10px] text-zinc-400 uppercase tracking-widest font-bold">PREVIEW:</label>
                    <div id="comms-preview-panel"
                        class="overflow-y-auto bg-black/40 border border-zinc-800 rounded-sm p-3 text-sm text-zinc-300 leading-relaxed normal-case"
                        style="height: 200px;">
                        <span class="text-zinc-600 text-[10px] uppercase tracking-widest">AWAITING_INPUT...</span>
                    </div>
                </div>
            </div>

            <!-- ORIGINAL_SIGNAL (reply context only) -->
            {% if original %}
            <details class="glass-panel p-3">
                <summary class="text-[10px] tracking-widest uppercase text-zinc-500 cursor-pointer hover:neon-text transition-colors select-none">
                    ↩ ORIGINAL_SIGNAL ▶
                </summary>
                <div class="mt-3 space-y-2 text-[10px] text-zinc-500 tracking-widest uppercase border-t border-(--glass-border) pt-3">
                    <div><span class="text-zinc-600">SUBJECT:</span> {{ original.subject }}</div>
                    <div><span class="text-zinc-600">FROM:</span> {{ original.sender }}</div>
                    <pre class="text-zinc-600 font-mono normal-case text-[10px] mt-2 leading-relaxed whitespace-pre-wrap">{{ original.body.split('\n')[:3] | join('\n') }}{% if original.body.split('\n') | length > 3 %}
...{% endif %}</pre>
                </div>
            </details>
            {% endif %}

            <!-- Draft filename (hidden, used when overwriting a draft) -->
            <input type="hidden" name="draft_filename" id="comms-draft-filename" value="">

            <!-- Actions -->
            <div class="flex items-center justify-between pt-2 border-t border-(--glass-border)">
                <div class="flex items-center space-x-3">
                    <button type="button"
                        hx-post="/comms/draft/save"
                        hx-include="closest form"
                        hx-target="#draft-save-feedback"
                        class="btn-ghost text-[10px] rounded-sm focus:outline-none">
                        BUFFER_DRAFT
                    </button>
                    <div id="draft-save-feedback"></div>
                </div>
                <button type="submit" class="btn-solid text-[10px] rounded-sm focus:outline-none">
                    TRANSMIT //
                </button>
            </div>
        </form>
    </div>
</div>

<script>
function toggleAllRecipients() {
    const cbs = document.querySelectorAll('.recipient-checkbox');
    const allChecked = Array.from(cbs).every(cb => cb.checked);
    cbs.forEach(cb => { cb.checked = !allChecked; });
    document.getElementById('select-all-btn').textContent = allChecked ? 'SELECT ALL' : 'DESELECT ALL';
}
</script>
```

- [ ] **Step 3: Commit**

```bash
git add templates/components/comms_message_reader.html templates/components/comms_compose_modal.html
git commit -m "feat(comms): comms_message_reader + comms_compose_modal templates"
```

---

## Task 11: Templates — comms_unread_badge + comms_preview

**Files:**
- Create: `templates/components/comms_unread_badge.html`
- Create: `templates/components/comms_preview.html`

- [ ] **Step 1: Create comms_unread_badge.html**

```html
<span id="comms-unread-badge"
      class="{% if count > 0 %}neon-bg text-[#0f172a] text-[9px] font-bold px-1.5 py-0.5 rounded-sm ml-1{% endif %}"
      data-count="{{ count }}"
      hx-get="/comms/unread-count"
      hx-trigger="load, every 30s"
      hx-swap="outerHTML">
    {% if count > 0 %}{{ count }}{% endif %}
    <script>
    (function () {
        window._commsLastCount = window._commsLastCount ?? 0;
        const prev = window._commsLastCount;
        const next = {{ count }};
        window._commsLastCount = next;
        if (next > prev) {
            const container = document.getElementById('toast-container');
            if (!container) return;
            const toast = document.createElement('div');
            toast.className = 'glass-panel border border-(--glass-border) px-4 py-3 text-[10px] neon-text tracking-widest uppercase pointer-events-auto shadow-lg';
            toast.textContent = '▶ INCOMING_SIGNAL // NEW_TRANSMISSION_RECEIVED';
            container.appendChild(toast);
            setTimeout(function () { toast.remove(); }, 4000);
        }
    })();
    </script>
</span>
```

- [ ] **Step 2: Create comms_preview.html**

```html
<div id="comms-preview-panel"
    class="overflow-y-auto bg-black/40 border border-zinc-800 rounded-sm p-3 text-sm text-zinc-300 leading-relaxed normal-case"
    style="height: 200px;">
    {% if html %}
        {{ html | safe }}
    {% else %}
        <span class="text-zinc-600 text-[10px] uppercase tracking-widest">AWAITING_INPUT...</span>
    {% endif %}
</div>
```

- [ ] **Step 3: Commit**

```bash
git add templates/components/comms_unread_badge.html templates/components/comms_preview.html
git commit -m "feat(comms): comms_unread_badge (toast delta) + comms_preview templates"
```

---

## Task 12: End-to-end verification + version bump

**Files:**
- Modify: `main.py` (version)
- Modify: `docs/Stato-dell-Arte.md`

- [ ] **Step 1: Start the app**

```bash
cd /home/spacewolf/Progetti/MD2FastPDF
./bin/launch.sh
```

- [ ] **Step 2: Smoke test checklist**

In the browser at `http://localhost:8000`:

1. Login as `admin`
2. Click **COMMS** in navbar → hub loads with 3 tabs
3. Click **OPEN_CHANNEL //** → compose modal opens, recipient list shows users
4. Select a recipient, write subject + body → preview updates live
5. Click **BUFFER_DRAFT** → `▶ BUFFER_SECURED // DRAFT_RETAINED` appears
6. Click **STAGING_BUFFER** tab → draft appears in list
7. Compose a new message and click **TRANSMIT //** → modal closes, `>> SIGNAL_TRANSMITTED` flash
8. Login as another user → check RECEPTION_ARRAY → message present with unread indicator
9. Click message → reader shows header + rendered body, unread dot disappears
10. Click **OPEN_RESPONSE** → compose modal opens pre-filled with `Re:` subject + ORIGINAL_SIGNAL visible
11. Click **PURGE_SIGNAL** → message removed, `>> SIGNAL_PURGED` notification

- [ ] **Step 3: Bump version in main.py**

```python
version="5.6.0",
```

- [ ] **Step 4: Update Stato-dell-Arte.md**

Change `[5.0] AEGIS COMMS` status from `Planned — Next` to `COMPLETED` in the roadmap table. Update version to 5.6.0.

- [ ] **Step 5: Final commit**

```bash
git add main.py docs/Stato-dell-Arte.md
git commit -m "feat(comms): AEGIS COMMS v5.6.0 complete — bump version"
```

---

## Self-Review

**Spec coverage:**

| Spec requirement | Task |
|---|---|
| Comms folders on user creation | Task 6 |
| `ensure_comms_folders` for existing users | Task 3, Task 7 (GET /comms) |
| FrontmatterParser (no PyYAML) | Task 2 |
| MessageRecord + recipients property | Task 2 |
| Multi-recipient send (comma-separated) | Task 5, Task 7 |
| ALL broadcast expansion | Task 5 (_expand_recipients) |
| Cross-workspace write + security assertion | Task 5 |
| Draft save/promote | Task 5, Task 7 |
| mark_read on message open | Task 5, Task 7 |
| render_md filter | Task 1 |
| All 12 routes including /comms/preview | Task 7 |
| comms_hub with tab bar | Task 9 |
| comms_message_list with unread indicator | Task 9 |
| comms_message_reader with structured header | Task 10 |
| comms_compose_modal with multi-select + preview | Task 10 |
| ORIGINAL_SIGNAL collapsible in reply | Task 10 |
| SELECT ALL toggle | Task 10 |
| comms_unread_badge with toast delta | Task 11 |
| comms_preview fragment | Task 11 |
| Toast container in base.html | Task 8 |
| COMMS nav link | Task 8 |
| main.py router registration | Task 8 |

**Type consistency check:** `MessageRecord` fields (`id`, `sender`, `recipient`, `subject`, `timestamp`, `read`, `body`, `filename`) used identically across Tasks 2, 5, 7, 9, 10. `comms_manager` singleton referenced consistently in Tasks 7, 8. `_store.list_usernames()` called in Tasks 6 (definition) and 7 (usage).

**No placeholders found.**
