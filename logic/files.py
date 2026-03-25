import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Union, Optional, Set
import anyio
from fastapi import HTTPException

# AEGIS_ARCHIVE_PROTOCOL: Centralized Constants
ALLOWED_EXTENSIONS: Set[str] = {".md", ".html", ".pdf"}
TEXT_EXTENSIONS: Set[str] = {".md", ".html"}
SKIP_DIRS: Set[str] = {".git", ".venv", "node_modules", ".pytest_cache", "__pycache__", ".gemini"}
CACHE_TTL: int = 60  # Seconds

# Global state for the active project root
_CURRENT_ROOT: Path = Path(__file__).parent.parent.resolve()

class PathSanitizer:
    """Handles path security and validation for the Aegis Archive."""
    
    @staticmethod
    def get_root() -> Path:
        return _CURRENT_ROOT

    @staticmethod
    def set_root(new_path: Union[str, Path]):
        global _CURRENT_ROOT
        resolved = Path(new_path).resolve()
        # Security: Always resolve and ensure it's within Path.home()
        if not str(resolved).startswith(str(Path.home().resolve())):
            raise HTTPException(status_code=403, detail="ACCESS_DENIED: Root must be within HOME")
        _CURRENT_ROOT = resolved
        StorageCache.invalidate()

    @staticmethod
    def resolve_and_sanitize(relative_path: str) -> Path:
        """Prevents directory traversal and hidden path access."""
        root = PathSanitizer.get_root()
        try:
            requested_path = (root / relative_path.strip("/")).resolve()
            
            # Traversal Check
            if not str(requested_path).startswith(str(root)):
                raise HTTPException(status_code=403, detail="ACCESS_DENIED: Path outside active root")
            
            # Hidden Path Check
            parts = requested_path.relative_to(root).parts
            if any(part.startswith(".") for part in parts):
                raise HTTPException(status_code=403, detail="ACCESS_DENIED: Hidden path access forbidden")
                
            return requested_path
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=400, detail="INVALID_PATH_FORMAT")

class DirectoryLister:
    """Tactical directory scanning and filtering."""

    @staticmethod
    async def list_home_dirs(relative_path: str = "") -> List[Dict[str, str]]:
        """Lists directories in HOME specifically for the root picker."""
        home = Path.home().resolve()
        target = (home / relative_path.strip("/")).resolve()
        
        if not str(target).startswith(str(home)):
            target = home

        dirs = []
        try:
            for entry in os.scandir(target):
                if entry.is_dir() and not entry.name.startswith("."):
                    dirs.append({
                        "name": entry.name,
                        "path": str((target / entry.name).relative_to(home))
                    })
        except PermissionError as e:
            raise HTTPException(status_code=403, detail="ACCESS_DENIED: Directory non leggibile") from e
        
        return sorted(dirs, key=lambda x: x["name"].lower())

    @staticmethod
    async def list_contents(relative_path: str = ".") -> List[Dict[str, Union[str, bool]]]:
        """Lists allowed files and directories in the project root."""
        target_path = PathSanitizer.resolve_and_sanitize(relative_path)
        
        if not target_path.is_dir():
            raise HTTPException(status_code=404, detail="DIRECTORY_NOT_FOUND")

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
            raise HTTPException(status_code=403, detail="PERMISSION_DENIED")

        return sorted(items, key=lambda x: (not x["is_dir"], x["name"].lower()))

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

class FileManager:
    """Primary file operation unit for Aegis Archives."""

    @staticmethod
    async def read_text(relative_path: str) -> str:
        path = PathSanitizer.resolve_and_sanitize(relative_path)
        if not path.is_file() or not any(str(path).lower().endswith(ext) for ext in TEXT_EXTENSIONS):
            raise HTTPException(status_code=404, detail="FILE_NOT_FOUND_OR_NOT_TEXT")

        async with await anyio.open_file(path, mode="r", encoding="utf-8") as f:
            return await f.read()

    @staticmethod
    async def read_bytes(relative_path: str) -> bytes:
        path = PathSanitizer.resolve_and_sanitize(relative_path)
        if not path.is_file():
            raise HTTPException(status_code=404, detail="FILE_NOT_FOUND")

        async with await anyio.open_file(path, mode="rb") as f:
            return await f.read()

    @staticmethod
    async def write_text(relative_path: str, content: str):
        path = PathSanitizer.resolve_and_sanitize(relative_path)
        if not any(str(path).lower().endswith(ext) for ext in TEXT_EXTENSIONS):
            raise HTTPException(status_code=400, detail="INVALID_FILE_TYPE")

        async with await anyio.open_file(path, mode="w", encoding="utf-8") as f:
            await f.write(content)

    @staticmethod
    async def create(relative_dir: str, filename: str) -> str:
        filename = filename.strip()
        if not filename:
            raise HTTPException(status_code=400, detail="FILENAME_REQUIRED")
            
        if not any(filename.lower().endswith(ext) for ext in TEXT_EXTENSIONS):
            filename += ".md"
            
        file_path = PathSanitizer.resolve_and_sanitize(os.path.join(relative_dir, filename))
        if file_path.exists():
            raise HTTPException(status_code=400, detail="FILE_ALREADY_EXISTS")
            
        async with await anyio.open_file(file_path, mode="w", encoding="utf-8") as f:
            await f.write("")
        
        StorageCache.invalidate()
        return str(Path(relative_dir) / filename)

    @staticmethod
    async def rename(relative_path: str, new_name: str) -> str:
        new_name = new_name.strip()
        if not new_name:
            raise HTTPException(status_code=400, detail="FILENAME_REQUIRED")

        old_path = PathSanitizer.resolve_and_sanitize(relative_path)
        if not old_path.is_file():
            raise HTTPException(status_code=404, detail="FILE_NOT_FOUND")

        if not Path(new_name).suffix:
            new_name += old_path.suffix

        new_path = old_path.parent / new_name
        # Security: validate destination
        PathSanitizer.resolve_and_sanitize(str(new_path.relative_to(PathSanitizer.get_root())))

        if new_path.exists():
            raise HTTPException(status_code=400, detail="FILE_ALREADY_EXISTS")

        await anyio.to_thread.run_sync(lambda: old_path.rename(new_path))
        StorageCache.invalidate()
        return str(Path(relative_path).parent / new_name)

    @staticmethod
    async def delete(relative_path: str):
        path = PathSanitizer.resolve_and_sanitize(relative_path)
        if not path.is_file() or not any(str(path).lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
            raise HTTPException(status_code=400, detail="INVALID_FILE_TYPE")
            
        await anyio.to_thread.run_sync(os.remove, str(path))
        StorageCache.invalidate()

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

    @staticmethod
    async def get_recent(limit: int = 5) -> List[Dict[str, Union[str, float]]]:
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

# --- Legacy Compatibility Layer (Aegis Backward Sync) ---
def get_project_root() -> Path: return PathSanitizer.get_root()
def set_project_root(path): PathSanitizer.set_root(path)
def sanitize_path(rel_path): return PathSanitizer.resolve_and_sanitize(rel_path)
async def list_only_directories(p=""): return await DirectoryLister.list_home_dirs(p)
async def list_directory_contents(p="."): return await DirectoryLister.list_contents(p)
async def read_file_content(p): return await FileManager.read_text(p)
async def read_file_bytes(p): return await FileManager.read_bytes(p)
async def write_file_content(p, c): await FileManager.write_text(p, c)
async def create_new_file(d, f): return await FileManager.create(d, f)
async def rename_file(p, n): return await FileManager.rename(p, n)
async def delete_file(p): await FileManager.delete(p)
async def get_recent_files(l=5): return await StorageCache.get_recent(l)
async def get_storage_stats(): return await StorageCache.get_stats()
async def search_files(q): return await DirectoryLister.search(q)
