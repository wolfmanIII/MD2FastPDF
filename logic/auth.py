"""
AEGIS_IDENTITY_PROTOCOL: Multi-user authentication and workspace isolation.

UserStore: persistent registry backed by ~/.config/sc-archive/users.json.
AuthService: credential verification, user creation, workspace management.
"""
import json
import os
import bcrypt
import anyio
from pathlib import Path
from typing import Optional, Protocol, runtime_checkable

from logic.exceptions import AuthError


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


@runtime_checkable
class SyncUserStoreProtocol(Protocol):
    """Sync abstraction — used only by bootstrap/CLI paths."""

    def get_sync(self, username: str) -> Optional["UserRecord"]: ...
    def is_empty(self) -> bool: ...
    def save_user_sync(self, record: "UserRecord") -> None: ...

_CONFIG_DIR = Path.home() / ".config" / "sc-archive"
_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
USERS_FILE = _CONFIG_DIR / "users.json"
_LEGACY_USERS_FILE = Path("config/users.json")
_GROUPS_FILE: Path = _CONFIG_DIR / "groups.json"


def _migrate_legacy_users() -> None:
    """Merge users from legacy config/users.json into the new location.

    Runs at module load. Legacy entries win over bootstrap-generated entries
    (e.g. a bare admin created by bootstrap_admin). Removes legacy file after merge.
    """
    if not _LEGACY_USERS_FILE.exists():
        return
    try:
        with open(_LEGACY_USERS_FILE, "r", encoding="utf-8") as f:
            legacy: dict = json.load(f)
    except (json.JSONDecodeError, IOError):
        return
    if not legacy:
        return
    current: dict = {}
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                current = json.load(f)
        except (json.JSONDecodeError, IOError):
            current = {}
    merged = {**current, **legacy}  # legacy entries overwrite bootstrap placeholders
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=4)
    _LEGACY_USERS_FILE.unlink()


_migrate_legacy_users()


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


class UserStore:
    """Persistent user registry backed by ~/.config/sc-archive/users.json."""

    @staticmethod
    def _build_record(username: str, entry: dict) -> UserRecord:
        """Builds a UserRecord from a persisted entry dict.

        Handles backwards compatibility: entries without a 'groups' key
        default to an empty list.
        """
        return UserRecord(
            username,
            entry["password_hash"],
            entry["root"],
            entry.get("groups", []),
        )

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
        return self._build_record(username, entry)

    def get_sync(self, username: str) -> Optional[UserRecord]:
        """Sync variant — used only during bootstrap/CLI."""
        entry = self._load().get(username)
        if not entry:
            return None
        return self._build_record(username, entry)

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

    async def list_users(self) -> list[UserRecord]:
        """Returns all registered users as UserRecord list."""
        data = await self._aload()
        return [
            self._build_record(u, d)
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


class AuthService:
    """Authentication and per-user workspace management."""

    def __init__(self, store: UserStoreProtocol, sync_store: SyncUserStoreProtocol):
        self._store = store
        self._sync_store = sync_store

    def _hash(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def _verify(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    def _default_root(self, username: str) -> Path:
        return Path.home() / "sc-archive" / username

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
        record = UserRecord(username, self._hash(password), str(root), [])
        await self._store.save_user(record)
        return record

    def create_user_sync(self, username: str, password: str) -> UserRecord:
        """Sync variant — used only during bootstrap."""
        root = self._default_root(username)
        root.mkdir(parents=True, exist_ok=True)
        record = UserRecord(username, self._hash(password), str(root), [])
        self._sync_store.save_user_sync(record)
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
        if self._sync_store.is_empty():
            password = os.getenv("AEGIS_ADMIN_PASSWORD", "admin")
            self.create_user_sync("admin", password)


_store = UserStore()
auth_service = AuthService(_store, _store)
