"""
AEGIS_GROUPSPACE_PROTOCOL: Shared workspace access control and file operations for groups.

Permission model:
  - Group root (/{group}/):    admin R+W, members R only
  - Shared folder (/{group}/shared/): members R+W, admin R only
"""
import os
from pathlib import Path
from typing import Any

import anyio

from logic.exceptions import AccessDeniedError, NotFoundError
from logic.files import ALLOWED_EXTENSIONS, TEXT_EXTENSIONS, SKIP_DIRS


def _workspace_base() -> Path:
    from config.settings import settings
    return Path(settings.get("workspace_base", str(Path.home() / "sc-archive")))


class GroupSpaceAccess:
    """Resolves access rights for a user within a group workspace."""

    @staticmethod
    def has_access(group_name: str, user_groups: list[str]) -> bool:
        """Returns True if the user is a member of the group or is admin."""
        return group_name in user_groups or "admin" in user_groups

    @staticmethod
    def can_write(relative_path: str, user_groups: list[str]) -> bool:
        """
        Admin: write anywhere except shared/.
        Members: write only inside shared/.
        """
        in_shared = relative_path.strip("/").startswith("shared")
        is_admin = "admin" in user_groups
        if is_admin:
            return not in_shared
        return in_shared

    @staticmethod
    def is_read_only(relative_path: str, user_groups: list[str]) -> bool:
        return not GroupSpaceAccess.can_write(relative_path, user_groups)


class GroupSpaceManager:
    """File operations scoped to a group workspace with access control enforcement."""

    @staticmethod
    def group_root(group_name: str) -> Path:
        return _workspace_base() / group_name

    @staticmethod
    def sanitize(group_name: str, relative_path: str) -> Path:
        """Resolves a relative path inside the group workspace. Prevents traversal."""
        root = GroupSpaceManager.group_root(group_name).resolve()
        resolved = (root / relative_path.strip("/")).resolve()
        if not str(resolved).startswith(str(root)):
            raise AccessDeniedError("ACCESS_DENIED: Path outside group workspace")
        parts = resolved.relative_to(root).parts
        if any(part.startswith(".") for part in parts):
            raise AccessDeniedError("ACCESS_DENIED: Hidden path access forbidden")
        return resolved

    @staticmethod
    async def list_contents(
        group_name: str,
        relative_path: str,
        user_groups: list[str],
    ) -> list[dict[str, Any]]:
        """Lists files and directories in the group workspace at the given path."""
        if not GroupSpaceAccess.has_access(group_name, user_groups):
            raise AccessDeniedError("ACCESS_DENIED: Not a member of this group")

        target = GroupSpaceManager.sanitize(group_name, relative_path)
        if not target.is_dir():
            raise NotFoundError("DIRECTORY_NOT_FOUND")

        def _scan() -> list[dict[str, Any]]:
            items = []
            for entry in os.scandir(target):
                if entry.name.startswith(".") or entry.name in SKIP_DIRS:
                    continue
                if entry.is_dir():
                    items.append({
                        "name": entry.name,
                        "is_dir": True,
                        "path": str(Path(relative_path) / entry.name) if relative_path else entry.name,
                    })
                elif any(entry.name.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
                    items.append({
                        "name": entry.name,
                        "is_dir": False,
                        "path": str(Path(relative_path) / entry.name) if relative_path else entry.name,
                    })
            return sorted(items, key=lambda x: (not x["is_dir"], x["name"].lower()))

        return await anyio.to_thread.run_sync(_scan)

    @staticmethod
    async def read_file(
        group_name: str,
        relative_path: str,
        user_groups: list[str],
    ) -> str:
        """Returns file content. All members and admin can read."""
        if not GroupSpaceAccess.has_access(group_name, user_groups):
            raise AccessDeniedError("ACCESS_DENIED: Not a member of this group")
        file_path = GroupSpaceManager.sanitize(group_name, relative_path)
        if not file_path.is_file() or not any(str(file_path).lower().endswith(ext) for ext in TEXT_EXTENSIONS):
            raise NotFoundError("FILE_NOT_FOUND_OR_NOT_TEXT")
        async with await anyio.open_file(file_path, mode="r", encoding="utf-8") as f:
            return await f.read()

    @staticmethod
    async def write_file(
        group_name: str,
        relative_path: str,
        content: str,
        user_groups: list[str],
    ) -> None:
        """Writes file content. Enforces write permissions."""
        if not GroupSpaceAccess.has_access(group_name, user_groups):
            raise AccessDeniedError("ACCESS_DENIED: Not a member of this group")
        if not GroupSpaceAccess.can_write(relative_path, user_groups):
            raise AccessDeniedError("ACCESS_DENIED: Write not permitted in this area")
        file_path = GroupSpaceManager.sanitize(group_name, relative_path)
        if not any(str(file_path).lower().endswith(ext) for ext in TEXT_EXTENSIONS):
            raise AccessDeniedError("ACCESS_DENIED: Only text files allowed")
        async with await anyio.open_file(file_path, mode="w", encoding="utf-8") as f:
            await f.write(content)

    @staticmethod
    async def create_file(
        group_name: str,
        relative_dir: str,
        filename: str,
        user_groups: list[str],
    ) -> str:
        """Creates a new empty file. Returns relative path."""
        if not GroupSpaceAccess.has_access(group_name, user_groups):
            raise AccessDeniedError("ACCESS_DENIED: Not a member of this group")
        filename = filename.strip()
        if not filename:
            raise AccessDeniedError("FILENAME_REQUIRED")
        if not any(filename.lower().endswith(ext) for ext in TEXT_EXTENSIONS):
            filename += ".md"
        relative_path = str(Path(relative_dir) / filename) if relative_dir else filename
        if not GroupSpaceAccess.can_write(relative_path, user_groups):
            raise AccessDeniedError("ACCESS_DENIED: Write not permitted in this area")
        file_path = GroupSpaceManager.sanitize(group_name, relative_path)
        if file_path.exists():
            raise AccessDeniedError("FILE_ALREADY_EXISTS")
        async with await anyio.open_file(file_path, mode="w", encoding="utf-8") as f:
            await f.write("")
        return relative_path

    @staticmethod
    async def delete_file(
        group_name: str,
        relative_path: str,
        user_groups: list[str],
    ) -> None:
        """Deletes a file. Enforces write permissions."""
        if not GroupSpaceAccess.has_access(group_name, user_groups):
            raise AccessDeniedError("ACCESS_DENIED: Not a member of this group")
        if not GroupSpaceAccess.can_write(relative_path, user_groups):
            raise AccessDeniedError("ACCESS_DENIED: Delete not permitted in this area")
        file_path = GroupSpaceManager.sanitize(group_name, relative_path)
        if not file_path.is_file():
            raise NotFoundError("FILE_NOT_FOUND")
        await anyio.to_thread.run_sync(os.remove, str(file_path))
