"""
AEGIS_BLUEPRINT_PROTOCOL: Template library management for narrative documents.
Blueprints are app-wide Markdown files stored in blueprints/ at the project root.
Categories are derived from subfolder names.
"""
import os
from pathlib import Path
from typing import Any

import anyio

from logic.exceptions import AccessDeniedError, NotFoundError

BLUEPRINTS_ROOT: Path = Path(__file__).parent.parent / "blueprints"


class BlueprintManager:
    """Manages the narrative blueprint library: list, read, write, delete."""

    @staticmethod
    def _sanitize(path: str) -> Path:
        """Prevents directory traversal outside blueprints/."""
        root = BLUEPRINTS_ROOT.resolve()
        resolved = (root / path.strip("/")).resolve()
        if not str(resolved).startswith(str(root)):
            raise AccessDeniedError("ACCESS_DENIED: Path outside blueprints root")
        return resolved

    @staticmethod
    def _display_name(filename: str) -> str:
        return Path(filename).stem.replace("-", " ").replace("_", " ").title()

    @staticmethod
    async def list_blueprints() -> list[dict[str, Any]]:
        """Returns all .md blueprints organized by category (subfolder name)."""
        def _scan() -> list[dict[str, Any]]:
            if not BLUEPRINTS_ROOT.exists():
                return []
            results: list[dict[str, Any]] = []
            for category_entry in sorted(os.scandir(BLUEPRINTS_ROOT), key=lambda x: x.name):
                if not category_entry.is_dir() or category_entry.name.startswith("."):
                    continue
                for f in sorted(os.scandir(category_entry.path), key=lambda x: x.name):
                    if f.is_file() and f.name.endswith(".md"):
                        results.append({
                            "path": f"{category_entry.name}/{f.name}",
                            "name": BlueprintManager._display_name(f.name),
                            "category": category_entry.name,
                        })
            return results

        return await anyio.to_thread.run_sync(_scan)

    @staticmethod
    async def read_blueprint(path: str) -> str:
        """Returns the raw Markdown content of a blueprint."""
        file_path = BlueprintManager._sanitize(path)
        if not file_path.is_file() or file_path.suffix != ".md":
            raise NotFoundError("BLUEPRINT_NOT_FOUND")
        async with await anyio.open_file(file_path, mode="r", encoding="utf-8") as f:
            return await f.read()

    @staticmethod
    async def write_blueprint(category: str, filename: str, content: str) -> str:
        """Creates or overwrites a blueprint. Returns the relative path."""
        filename = filename.strip().lower().replace(" ", "-")
        if not filename.endswith(".md"):
            filename += ".md"
        category = category.strip().lower().replace(" ", "-")
        path = f"{category}/{filename}"
        file_path = BlueprintManager._sanitize(path)
        def _write() -> None:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
        await anyio.to_thread.run_sync(_write)
        return path

    @staticmethod
    async def delete_blueprint(path: str) -> None:
        """Deletes a blueprint file."""
        file_path = BlueprintManager._sanitize(path)
        if not file_path.is_file():
            raise NotFoundError("BLUEPRINT_NOT_FOUND")
        await anyio.to_thread.run_sync(os.remove, str(file_path))
