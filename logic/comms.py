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

_COMMS_SUBFOLDERS: tuple[str, ...] = ("inbound", "outbound", "staging")


def _workspace_base() -> Path:
    """Returns the resolved workspace base path from settings."""
    return Path(settings.get("workspace_base", str(Path.home() / "sc-archive"))).resolve()


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


class CommsManager:
    """Async I/O for comms operations across user workspaces.

    Path resolution bypasses PathSanitizer intentionally — cross-workspace
    writes require direct Path construction from workspace_base config.
    """

    def _workspace_root(self, username: str) -> Path:
        """All users (including admin) map to workspace_base/username."""
        return _workspace_base() / username

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

    @staticmethod
    def allowed_recipients(
        sender: str,
        sender_groups: list[str],
        all_users: list,
    ) -> list[str]:
        """Returns usernames reachable by sender.

        Admin (has 'admin' group): unrestricted — can reach all users.
        Others: reachable if recipient has 'admin' group OR shares at least
        one group with the sender. Sender is always excluded.
        all_users accepts list[UserRecord] — typed as list to avoid circular import.
        """
        if "admin" in sender_groups:
            return [u.username for u in all_users if u.username != sender]
        return [
            u.username for u in all_users
            if u.username != sender
            and (
                "admin" in u.groups
                or any(g in sender_groups for g in u.groups)
            )
        ]

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
        self, recipient_str: str, allowed_usernames: list[str], sender: str
    ) -> list[str]:
        """Expands 'ALL' to allowed_usernames excluding sender. Validates explicit recipients."""
        if recipient_str.strip().upper() == "ALL":
            return [u for u in allowed_usernames if u != sender]
        chosen = [r.strip() for r in recipient_str.split(",") if r.strip()]
        forbidden = [r for r in chosen if r not in allowed_usernames]
        if forbidden:
            raise CommsError(f"RECIPIENT_NOT_ALLOWED: {','.join(forbidden)}")
        return chosen

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

    async def send_message(
        self,
        sender: str,
        recipient_str: str,
        subject: str,
        body: str,
        allowed_usernames: list[str],
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
        recipients = self._expand_recipients(recipient_str, allowed_usernames, sender)
        base = _workspace_base()
        inbound_paths: list[tuple[str, Path]] = []
        for recipient in recipients:
            inbound_path = self._inbound(recipient) / filename
            if not inbound_path.is_relative_to(base):
                raise AccessDeniedError(
                    f"COMMS: Recipient path outside workspace boundary: {recipient}"
                )
            inbound_paths.append((recipient, inbound_path))
        # All paths validated — write outbound, then deliver to each recipient in parallel
        await self._write_message_file(self._outbound(sender) / filename, record)

        async def _deliver(recipient: str, inbound_path: Path) -> None:
            await self.ensure_comms_folders(recipient)
            await self._write_message_file(inbound_path, record)

        async with anyio.create_task_group() as tg:
            for recipient, inbound_path in inbound_paths:
                tg.start_soon(_deliver, recipient, inbound_path)
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
        self, sender: str, draft_filename: str, allowed_usernames: list[str]
    ) -> MessageRecord:
        """Sends a draft: reads staging/, calls send_message(), deletes draft."""
        path = self._staging(sender) / draft_filename
        if not await anyio.Path(path).exists():
            raise NotFoundError(f"DRAFT_NOT_FOUND: {draft_filename}")
        rec = await self._read_message_file(path)
        if rec is None:
            raise CommsError(f"DRAFT_PARSE_FAILED: {draft_filename}")
        sent = await self.send_message(
            sender, rec.recipient, rec.subject, rec.body, allowed_usernames
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
