"""
AEGIS_IDENTITY_PROTOCOL: Multi-user authentication and workspace isolation.

UserStore: persistent registry backed by config/users.json.
AuthService: credential verification, user creation, workspace management.
"""
import json
import os
import bcrypt
import anyio
from pathlib import Path
from typing import Optional, Protocol, runtime_checkable

from config.settings import settings
from logic.exceptions import AuthError


@runtime_checkable
class UserStoreProtocol(Protocol):
    """Abstraction over the user persistence backend."""

    async def get(self, username: str) -> Optional["UserRecord"]: ...
    def get_sync(self, username: str) -> Optional["UserRecord"]: ...
    def is_empty(self) -> bool: ...
    async def save_user(self, record: "UserRecord") -> None: ...
    def save_user_sync(self, record: "UserRecord") -> None: ...
    async def update_root(self, username: str, root: str) -> None: ...

USERS_FILE = Path("config/users.json")


class UserRecord:
    """Represents a single authenticated user entry."""
    __slots__ = ("username", "password_hash", "root")

    def __init__(self, username: str, password_hash: str, root: str):
        self.username = username
        self.password_hash = password_hash
        self.root = root

    def to_dict(self) -> dict:
        return {"password_hash": self.password_hash, "root": self.root}


class UserStore:
    """Persistent user registry backed by config/users.json."""

    def _load(self) -> dict:
        """Sync load — used only by bootstrap/CLI sync chain."""
        if not USERS_FILE.exists():
            return {}
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    async def _aload(self) -> dict:
        """Async load — used by all async-context operations."""
        p = anyio.Path(USERS_FILE)
        if not await p.exists():
            return {}
        try:
            content = await p.read_text(encoding="utf-8")
            return json.loads(content)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_sync(self, data: dict) -> None:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    async def _save(self, data: dict) -> None:
        content = json.dumps(data, indent=4)
        async with await anyio.open_file(USERS_FILE, "w") as f:
            await f.write(content)

    async def get(self, username: str) -> Optional[UserRecord]:
        """Returns the UserRecord for the given username, or None if not found."""
        entry = (await self._aload()).get(username)
        if not entry:
            return None
        return UserRecord(username, entry["password_hash"], entry["root"])

    def get_sync(self, username: str) -> Optional[UserRecord]:
        """Sync variant — used only during bootstrap/CLI."""
        entry = self._load().get(username)
        if not entry:
            return None
        return UserRecord(username, entry["password_hash"], entry["root"])

    def is_empty(self) -> bool:
        return len(self._load()) == 0

    async def save_user(self, record: UserRecord) -> None:
        data = await self._aload()
        data[record.username] = record.to_dict()
        await self._save(data)

    def save_user_sync(self, record: UserRecord) -> None:
        """Sync write — used only during bootstrap."""
        data = self._load()
        data[record.username] = record.to_dict()
        self._save_sync(data)

    async def update_root(self, username: str, root: str) -> None:
        """Persists a new workspace root for the given user."""
        data = await self._aload()
        if username not in data:
            raise AuthError(f"USER_NOT_FOUND: {username}")
        data[username]["root"] = root
        await self._save(data)


class AuthService:
    """Authentication and per-user workspace management."""

    def __init__(self, store: UserStoreProtocol):
        self._store = store

    def _hash(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def _verify(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    def _default_root(self, username: str) -> Path:
        base = Path(settings.get("workspace_base", str(Path.home() / "sc-archive")))
        return base / username

    async def authenticate(self, username: str, password: str) -> UserRecord:
        """Verifies credentials. Raises AuthError on failure."""
        record = await self._store.get(username)
        if not record or not self._verify(password, record.password_hash):
            raise AuthError("INVALID_CREDENTIALS")
        return record

    async def create_user(self, username: str, password: str) -> UserRecord:
        """Creates a new user with hashed password and default workspace directory."""
        root = self._default_root(username)
        await anyio.to_thread.run_sync(lambda: root.mkdir(parents=True, exist_ok=True))
        record = UserRecord(username, self._hash(password), str(root))
        await self._store.save_user(record)
        return record

    def create_user_sync(self, username: str, password: str) -> UserRecord:
        """Sync variant — used only during bootstrap."""
        root = self._default_root(username)
        root.mkdir(parents=True, exist_ok=True)
        record = UserRecord(username, self._hash(password), str(root))
        self._store.save_user_sync(record)
        return record

    async def get_user_root(self, username: str) -> Path:
        """Returns the workspace root for the given user."""
        record = await self._store.get(username)
        if not record:
            raise AuthError(f"USER_NOT_FOUND: {username}")
        return Path(record.root)

    async def update_user_root(self, username: str, new_root: Path) -> None:
        """Persists a new workspace root for the given user."""
        await self._store.update_root(username, str(new_root))

    async def change_password(self, username: str, new_password: str) -> None:
        """Replaces the stored password hash for the given user."""
        record = await self._store.get(username)
        if not record:
            raise AuthError(f"USER_NOT_FOUND: {username}")
        record.password_hash = self._hash(new_password)
        await self._store.save_user(record)

    def bootstrap_admin(self) -> None:
        """Creates the admin user on first run if no users exist."""
        if self._store.is_empty():
            password = os.getenv("AEGIS_ADMIN_PASSWORD", "admin")
            self.create_user_sync("admin", password)


_store = UserStore()
auth_service = AuthService(_store)
