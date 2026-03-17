import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Union
import anyio
from fastapi import HTTPException

PROJECT_ROOT = Path.home().resolve()

def sanitize_path(relative_path: str) -> Path:
    """
    Sanitizes the input path to prevent directory traversal attacks.
    Ensures the path is within PROJECT_ROOT.
    """
    try:
        requested_path = (PROJECT_ROOT / relative_path.strip("/")).resolve()
        # Security: Prevent traversal
        if not str(requested_path).startswith(str(PROJECT_ROOT)):
            raise HTTPException(status_code=403, detail="ACCESS_DENIED: Path outside project root")
        
        # Security: Prevent access to dotfiles/hidden folders
        parts = requested_path.relative_to(PROJECT_ROOT).parts
        if any(part.startswith(".") for part in parts):
            raise HTTPException(status_code=403, detail="ACCESS_DENIED: Hidden path access forbidden")
            
        return requested_path
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="INVALID_PATH_FORMAT")

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
            # Skip hidden files and directories
            if entry.name.startswith("."):
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

async def get_recent_files(limit: int = 5) -> List[Dict[str, Union[str, float]]]:
    """
    Returns the most recently modified markdown files in the project.
    """
    def _scan():
        files = []
        for root, _, filenames in os.walk(PROJECT_ROOT):
            # Skip hidden directories
            if any(part.startswith(".") for part in Path(root).relative_to(PROJECT_ROOT).parts):
                continue
                
            for filename in filenames:
                if filename.endswith(".md") and not filename.startswith("."):
                    file_path = Path(root) / filename
                    mtime = file_path.stat().st_mtime
                    files.append({
                        "name": filename,
                        "path": str(file_path.relative_to(PROJECT_ROOT)),
                        "mtime": mtime,
                        "mtime_str": datetime.fromtimestamp(mtime).strftime("%d-%m %H:%M")
                    })
        return sorted(files, key=lambda x: x["mtime"], reverse=True)[:limit]

    return await anyio.to_thread.run_sync(_scan)

async def get_storage_stats() -> Dict[str, Union[str, float]]:
    """
    Calculates storage metrics for the markdown archive.
    """
    def _calc():
        total_size = 0
        count = 0
        for root, _, filenames in os.walk(PROJECT_ROOT):
            if any(part.startswith(".") for part in Path(root).relative_to(PROJECT_ROOT).parts):
                continue
            for filename in filenames:
                if filename.endswith(".md"):
                    total_size += (Path(root) / filename).stat().st_size
                    count += 1
        
        # Format size
        if total_size < 1024:
            size_str = f"{total_size} B"
        elif total_size < 1024**2:
            size_str = f"{total_size/1024:.1f} KB"
        else:
            size_str = f"{total_size/1024**2:.1f} MB"
            
        return {
            "total_size": size_str,
            "file_count": count,
            "usage_percent": min(100, (total_size / (100 * 1024 * 1024)) * 100) # Assuming 100MB quota for Aegis Base
        }

    return await anyio.to_thread.run_sync(_calc)
