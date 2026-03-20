import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Union
import anyio
from fastapi import HTTPException

# Global state for the active project root
_CURRENT_ROOT = Path(__file__).parent.parent.resolve()

def get_project_root() -> Path:
    return _CURRENT_ROOT

def set_project_root(new_path: Union[str, Path]):
    global _CURRENT_ROOT
    # Security: Always resolve and ensure it's within Path.home()
    resolved = Path(new_path).resolve()
    if not str(resolved).startswith(str(Path.home().resolve())):
        raise HTTPException(status_code=403, detail="ACCESS_DENIED: Root must be within HOME")
    _CURRENT_ROOT = resolved
    # Invalidate cache
    _storage_cache["timestamp"] = 0

def sanitize_path(relative_path: str) -> Path:
    """
    Sanitizes the input path to prevent directory traversal attacks.
    Ensures the path is within the currently set get_project_root().
    """
    root = get_project_root()
    try:
        # If relative_path is ".", it resolves to root
        requested_path = (root / relative_path.strip("/")).resolve()
        # Security: Prevent traversal
        if not str(requested_path).startswith(str(root)):
            raise HTTPException(status_code=403, detail="ACCESS_DENIED: Path outside active root")
        
        # Security: Prevent access to dotfiles/hidden folders
        parts = requested_path.relative_to(get_project_root()).parts
        if any(part.startswith(".") for part in parts):
            raise HTTPException(status_code=403, detail="ACCESS_DENIED: Hidden path access forbidden")
            
        return requested_path
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="INVALID_PATH_FORMAT")

SKIP_DIRS = {".git", ".venv", "node_modules", ".pytest_cache", "__pycache__", ".gemini"}

# In-memory cache for storage stats
_storage_cache = {"data": None, "timestamp": 0}
CACHE_TTL = 60  # Cache duration in seconds

async def list_only_directories(relative_path: str = "") -> List[Dict[str, str]]:
    """
    Lists ONLY directories within Path.home() for the root picker.
    relative_path is relative to HOME.
    """
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

async def list_directory_contents(relative_path: str = ".") -> List[Dict[str, Union[str, bool]]]:
    """
    Lists files and directories in the specified relative path.
    Only returns .md files and directories.
    """
    target_path = sanitize_path(relative_path)
    
    if not target_path.is_dir():
        raise HTTPException(status_code=404, detail="DIRECTORY_NOT_FOUND")

    items = []
    
    # Using anyio for async dir listing if needed, but os.scandir is generally fast
    # For strict compliance with "no sync I/O", we wrap it or use aiofiles/anyio
    try:
        for entry in os.scandir(target_path):
            # Skip hidden files and skipped directories
            if entry.name.startswith(".") or entry.name in SKIP_DIRS:
                continue
                
            if entry.is_dir():
                items.append({
                    "name": entry.name,
                    "is_dir": True,
                    "path": str(Path(relative_path) / entry.name)
                })
            elif entry.name.endswith(".md"):
                items.append({
                    "name": entry.name,
                    "is_dir": False,
                    "path": str(Path(relative_path) / entry.name)
                })
    except PermissionError:
        raise HTTPException(status_code=403, detail="PERMISSION_DENIED")

    # Sort: Directories first, then files
    return sorted(items, key=lambda x: (not x["is_dir"], x["name"].lower()))

async def read_file_content(relative_path: str) -> str:
    """
    Reads the content of a markdown file asynchronously.
    """
    file_path = sanitize_path(relative_path)
    
    if not file_path.is_file() or not str(file_path).endswith(".md"):
        raise HTTPException(status_code=404, detail="FILE_NOT_FOUND")

    async with await anyio.open_file(file_path, mode="r", encoding="utf-8") as f:
        content = await f.read()
    
    return content

async def write_file_content(relative_path: str, content: str):
    """
    Writes content to a markdown file asynchronously.
    """
    file_path = sanitize_path(relative_path)
    
    # We only allow writing to .md files for security
    if not str(file_path).endswith(".md"):
        raise HTTPException(status_code=400, detail="INVALID_FILE_TYPE: Only .md files allowed")

    async with await anyio.open_file(file_path, mode="w", encoding="utf-8") as f:
        await f.write(content)

async def create_new_file(relative_dir: str, filename: str):
    """
    Creates a new empty markdown file in the specified directory.
    Ensures the .md extension.
    """
    filename = filename.strip()
    if not filename:
        raise HTTPException(status_code=400, detail="FILENAME_REQUIRED")
        
    if not filename.lower().endswith(".md"):
        filename += ".md"
        
    # Sanitize the directory first, then join and sanitize the full path
    target_dir = sanitize_path(relative_dir)
    file_path = sanitize_path(os.path.join(relative_dir, filename))
    
    # Check if file already exists
    if file_path.exists():
        raise HTTPException(status_code=400, detail="FILE_ALREADY_EXISTS")
        
    async with await anyio.open_file(file_path, mode="w", encoding="utf-8") as f:
        await f.write("")
    
    # Invalidate cache on change
    _storage_cache["timestamp"] = 0
    
    return str(Path(relative_dir) / filename)

async def delete_file(relative_path: str):
    """
    Deletes a markdown file asynchronously.
    """
    file_path = sanitize_path(relative_path)
    
    # Check if it's a file and ends with .md
    if not file_path.is_file() or not str(file_path).endswith(".md"):
        raise HTTPException(status_code=400, detail="INVALID_FILE: Only .md files can be deleted")
        
    # Use anyio to run os.remove in a thread pool to avoid blocking
    await anyio.to_thread.run_sync(os.remove, str(file_path))
    
    # Invalidate cache on change
    _storage_cache["timestamp"] = 0

async def get_recent_files(limit: int = 5) -> List[Dict[str, Union[str, float]]]:
    """
    Returns the most recently modified markdown files in the project.
    Optimized to skip non-project directories.
    """
    def _scan():
        files = []
        for root, dirs, filenames in os.walk(get_project_root()):
            # Efficiently skip unwanted directories
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
                
            for filename in filenames:
                if filename.endswith(".md") and not filename.startswith("."):
                    file_path = Path(root) / filename
                    try:
                        mtime = file_path.stat().st_mtime
                        files.append({
                            "name": filename,
                            "path": str(file_path.relative_to(get_project_root())),
                            "mtime": mtime,
                            "mtime_str": datetime.fromtimestamp(mtime).strftime("%d-%m %H:%M")
                        })
                    except (FileNotFoundError, PermissionError):
                        continue
        return sorted(files, key=lambda x: x["mtime"], reverse=True)[:limit]

    return await anyio.to_thread.run_sync(_scan)

async def get_storage_stats() -> Dict[str, Union[str, float]]:
    """
    Calculates storage metrics for the markdown archive.
    Uses in-memory cache to maintain high performance.
    """
    now = datetime.now().timestamp()
    if _storage_cache["data"] and (now - _storage_cache["timestamp"] < CACHE_TTL):
        return _storage_cache["data"]

    def _calc():
        total_size = 0
        count = 0
        for root, dirs, filenames in os.walk(get_project_root()):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
            for filename in filenames:
                if filename.endswith(".md"):
                    try:
                        total_size += (Path(root) / filename).stat().st_size
                        count += 1
                    except (FileNotFoundError, PermissionError):
                        continue
        
        # Format size
        if total_size < 1024:
            size_str = f"{total_size} B"
        elif total_size < 1024**2:
            size_str = f"{total_size/1024:.1f} KB"
        else:
            size_str = f"{total_size/1024**2:.1f} MB"
            
        stats = {
            "total_size": size_str,
            "file_count": count,
            "usage_percent": min(100, (total_size / (100 * 1024 * 1024)) * 100) # Assuming 100MB quota
        }
        return stats

    data = await anyio.to_thread.run_sync(_calc)
    _storage_cache["data"] = data
    _storage_cache["timestamp"] = now
    return data
