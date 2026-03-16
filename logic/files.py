import os
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
