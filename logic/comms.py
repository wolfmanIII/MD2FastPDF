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
