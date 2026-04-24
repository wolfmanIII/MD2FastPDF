import os
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Union, Optional, Set, Callable
import anyio

from logic.exceptions import (
    AegisError, AccessDeniedError, NotFoundError, InvalidPathError,
    InvalidFileTypeError, FileConflictError, FilenameRequiredError,
)

# AEGIS_ARCHIVE_PROTOCOL: Centralized Constants
ALLOWED_EXTENSIONS: Set[str] = {".md", ".html", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".mp3", ".ogg", ".wav"}
TEXT_EXTENSIONS: Set[str] = {".md", ".html"}
SKIP_DIRS: Set[str] = {".git", ".venv", "node_modules", ".pytest_cache", "__pycache__", ".gemini", "comms"}
CACHE_TTL: int = 60  # Seconds

# Per-request root isolation via ContextVar (AEGIS_IDENTITY_PROTOCOL)
_DEFAULT_ROOT: Path = Path(__file__).parent.parent.resolve()
_REQUEST_ROOT: ContextVar[Path] = ContextVar("aegis_request_root", default=_DEFAULT_ROOT)

# Mutation hook registry — inverted dependency for cache invalidation
_mutation_hooks: list[Callable[[], None]] = []

def register_mutation_hook(fn: Callable[[], None]) -> None:
    """Registers a callback invoked after any write/delete/rename operation."""
    if fn not in _mutation_hooks:
        _mutation_hooks.append(fn)

def _notify_mutation() -> None:
    for hook in _mutation_hooks:
        hook()


class PathSanitizer:
    """Handles path security and validation for the Aegis Archive."""

    @staticmethod
    def get_root() -> Path:
        return _REQUEST_ROOT.get()

    @staticmethod
    def bind_request_root(path: Path) -> None:
        """Binds path as the root for the current async context (per-request isolation)."""
        _REQUEST_ROOT.set(path)

    @staticmethod
    def set_root(new_path: Union[str, Path]):
        global _DEFAULT_ROOT
        # Resolve to canonical form (follows symlinks). Confinement policy is
        # enforced upstream by the route (allowed_base check), not here.
        resolved = Path(new_path).resolve()
        _DEFAULT_ROOT = resolved
        _REQUEST_ROOT.set(resolved)
        _notify_mutation()

    @staticmethod
    def resolve_and_sanitize(relative_path: str) -> Path:
        """Prevents directory traversal and hidden path access."""
        root = PathSanitizer.get_root()
        # Resolve root too: if root contains symlink components the stored path
        # may differ from the fully-resolved requested_path, breaking startswith.
        resolved_root = root.resolve()
        try:
            requested_path = (root / relative_path.strip("/")).resolve()

            # Traversal Check
            if not str(requested_path).startswith(str(resolved_root)):
                raise AccessDeniedError("ACCESS_DENIED: Path outside active root")

            # Hidden Path Check
            parts = requested_path.relative_to(resolved_root).parts
            if any(part.startswith(".") for part in parts):
                raise AccessDeniedError("ACCESS_DENIED: Hidden path access forbidden")

            return requested_path
        except AegisError:
            raise
        except Exception:
            raise InvalidPathError()


class DirectoryLister:
    """Tactical directory scanning and filtering."""

    @staticmethod
    async def list_home_dirs(relative_path: str = "", base: Path | None = None) -> List[Dict[str, str]]:
        """Lists directories for the root picker, confined to `base` (default: home).
        Admin passes base=Path('/') for full-filesystem access."""
        fs_base = (base or Path.home()).resolve()
        clean = relative_path.strip("/")
        # normpath handles ".." without following symlinks — prevents traversal attacks
        # while allowing symlinks that point outside fs_base to be navigated.
        target = Path(os.path.normpath(fs_base / clean)) if clean else fs_base

        if not str(target).startswith(str(fs_base)):
            target = fs_base

        def _scan():
            dirs = []
            try:
                for entry in os.scandir(target):
                    if entry.is_dir() and not entry.name.startswith("."):
                        # Logical child: relative_to always works since target is under fs_base
                        logical_child = target / entry.name
                        dirs.append({"name": entry.name, "path": str(logical_child.relative_to(fs_base))})
            except PermissionError as e:
                raise AccessDeniedError("ACCESS_DENIED: Directory non leggibile") from e
            return sorted(dirs, key=lambda x: x["name"].lower())

        return await anyio.to_thread.run_sync(_scan)

    @staticmethod
    async def list_contents(relative_path: str = ".") -> List[Dict[str, Union[str, bool]]]:
        """Lists allowed files and directories in the project root."""
        target_path = PathSanitizer.resolve_and_sanitize(relative_path)

        if not target_path.is_dir():
            raise NotFoundError("DIRECTORY_NOT_FOUND")

        def _scan():
            items = []
            try:
                for entry in os.scandir(target_path):
                    if entry.name.startswith(".") or entry.name in SKIP_DIRS:
                        continue

                    if entry.is_dir():
                        items.append({
                            "name": entry.name,
                            "is_dir": True,
                            "path": str(Path(relative_path) / entry.name)
                        })
                    elif any(entry.name.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
                        items.append({
                            "name": entry.name,
                            "is_dir": False,
                            "path": str(Path(relative_path) / entry.name)
                        })
            except PermissionError:
                raise AccessDeniedError("PERMISSION_DENIED")
            return sorted(items, key=lambda x: (not x["is_dir"], x["name"].lower()))

        return await anyio.to_thread.run_sync(_scan)

    @staticmethod
    async def search(query: str) -> List[Dict[str, Union[str, bool]]]:
        """Recursive archive search for tactical patterns."""
        query = query.lower().strip()
        if not query:
            return []

        def _scan():
            results = []
            root = PathSanitizer.get_root()
            for r, dirs, filenames in os.walk(root):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
                for filename in filenames:
                    if any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS) and query in filename.lower():
                        file_path = Path(r) / filename
                        results.append({
                            "name": filename,
                            "is_dir": False,
                            "path": str(file_path.relative_to(root))
                        })
            return sorted(results, key=lambda x: x["name"].lower())

        return await anyio.to_thread.run_sync(_scan)

    @staticmethod
    async def get_recent(limit: int = 5) -> List[Dict[str, Union[str, float]]]:
        """Returns the most recently modified allowed files in the archive."""
        def _scan():
            files = []
            root = PathSanitizer.get_root()
            for r, dirs, filenames in os.walk(root):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
                for filename in filenames:
                    if any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS) and not filename.startswith("."):
                        file_path = Path(r) / filename
                        try:
                            mtime = file_path.stat().st_mtime
                            files.append({
                                "name": filename,
                                "path": str(file_path.relative_to(root)),
                                "mtime": mtime,
                                "mtime_str": datetime.fromtimestamp(mtime).strftime("%d-%m %H:%M")
                            })
                        except (FileNotFoundError, PermissionError):
                            continue
            return sorted(files, key=lambda x: x["mtime"], reverse=True)[:limit]

        return await anyio.to_thread.run_sync(_scan)


class FileManager:
    """Primary file operation unit for Aegis Archives."""

    @staticmethod
    async def read_text(relative_path: str) -> str:
        path = PathSanitizer.resolve_and_sanitize(relative_path)
        if not path.is_file() or not any(str(path).lower().endswith(ext) for ext in TEXT_EXTENSIONS):
            raise NotFoundError("FILE_NOT_FOUND_OR_NOT_TEXT")

        async with await anyio.open_file(path, mode="r", encoding="utf-8") as f:
            return await f.read()

    @staticmethod
    async def read_bytes(relative_path: str) -> bytes:
        path = PathSanitizer.resolve_and_sanitize(relative_path)
        if not path.is_file():
            raise NotFoundError("FILE_NOT_FOUND")

        async with await anyio.open_file(path, mode="rb") as f:
            return await f.read()

    @staticmethod
    async def write_text(relative_path: str, content: str):
        path = PathSanitizer.resolve_and_sanitize(relative_path)
        if not any(str(path).lower().endswith(ext) for ext in TEXT_EXTENSIONS):
            raise InvalidFileTypeError()

        async with await anyio.open_file(path, mode="w", encoding="utf-8") as f:
            await f.write(content)

    @staticmethod
    async def create(relative_dir: str, filename: str) -> str:
        filename = filename.strip()
        if not filename:
            raise FilenameRequiredError()

        if not any(filename.lower().endswith(ext) for ext in TEXT_EXTENSIONS):
            filename += ".md"

        file_path = PathSanitizer.resolve_and_sanitize(os.path.join(relative_dir, filename))
        if file_path.exists():
            raise FileConflictError()

        async with await anyio.open_file(file_path, mode="w", encoding="utf-8") as f:
            await f.write("")

        _notify_mutation()
        return str(Path(relative_dir) / filename)

    @staticmethod
    async def rename(relative_path: str, new_name: str) -> str:
        new_name = new_name.strip()
        if not new_name:
            raise FilenameRequiredError()

        old_path = PathSanitizer.resolve_and_sanitize(relative_path)
        if not old_path.is_file():
            raise NotFoundError("FILE_NOT_FOUND")

        if not Path(new_name).suffix:
            new_name += old_path.suffix

        new_path = old_path.parent / new_name
        # Security: validate destination
        PathSanitizer.resolve_and_sanitize(str(new_path.relative_to(PathSanitizer.get_root())))

        if new_path.exists():
            raise FileConflictError()

        await anyio.to_thread.run_sync(lambda: old_path.rename(new_path))
        _notify_mutation()
        return str(Path(relative_path).parent / new_name)

    @staticmethod
    async def delete(relative_path: str):
        path = PathSanitizer.resolve_and_sanitize(relative_path)
        if not path.is_file() or not any(str(path).lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
            raise InvalidFileTypeError()

        await anyio.to_thread.run_sync(os.remove, str(path))
        _notify_mutation()

class StorageCache:
    """In-memory telemetry cache for archive statistics."""
    _cache: Dict[str, Union[dict, float]] = {"data": None, "timestamp": 0}

    @classmethod
    def invalidate(cls):
        cls._cache["timestamp"] = 0

    @classmethod
    async def get_stats(cls) -> Dict[str, Union[str, float]]:
        now = datetime.now().timestamp()
        if cls._cache["data"] and (now - cls._cache["timestamp"] < CACHE_TTL):
            return cls._cache["data"]

        def _calc():
            total_size = 0
            count = 0
            root = PathSanitizer.get_root()
            for r, dirs, filenames in os.walk(root):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
                for filename in filenames:
                    if any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
                        try:
                            total_size += (Path(r) / filename).stat().st_size
                            count += 1
                        except (FileNotFoundError, PermissionError):
                            continue

            size_str = f"{total_size} B" if total_size < 1024 else \
                       f"{total_size/1024:.1f} KB" if total_size < 1024**2 else \
                       f"{total_size/1024**2:.1f} MB"

            return {
                "total_size": size_str,
                "file_count": count,
                "usage_percent": min(100, (total_size / (100 * 1024 * 1024)) * 100)
            }

        data = await anyio.to_thread.run_sync(_calc)
        cls._cache["data"] = data
        cls._cache["timestamp"] = now
        return data


# --- Legacy Compatibility Layer (Aegis Backward Sync) ---
def get_project_root() -> Path: return PathSanitizer.get_root()
def set_project_root(path): PathSanitizer.set_root(path)
def sanitize_path(rel_path): return PathSanitizer.resolve_and_sanitize(rel_path)
async def list_only_directories(p="", base: Path | None = None): return await DirectoryLister.list_home_dirs(p, base=base)
async def list_directory_contents(p="."): return await DirectoryLister.list_contents(p)
async def read_file_content(p): return await FileManager.read_text(p)
async def read_file_bytes(p): return await FileManager.read_bytes(p)
async def write_file_content(p, c): await FileManager.write_text(p, c)
async def create_new_file(d, f): return await FileManager.create(d, f)
async def rename_file(p, n): return await FileManager.rename(p, n)
async def delete_file(p): await FileManager.delete(p)
async def get_recent_files(l=5): return await DirectoryLister.get_recent(l)
async def get_storage_stats(): return await StorageCache.get_stats()
async def search_files(q): return await DirectoryLister.search(q)
