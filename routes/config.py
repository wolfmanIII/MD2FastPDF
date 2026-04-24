"""
AEGIS_CONFIG_ROUTER: System environment and workspace configuration.
"""
import os
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse
from pathlib import Path

from config.settings import settings
from logic.auth import auth_service
from logic.exceptions import AccessDeniedError
from config.templates import templates
from logic.files import list_only_directories, set_project_root, list_directory_contents
from routes.deps import get_current_user

# AEGIS_CONFIG_ROUTER: System environment and workspace
router = APIRouter(tags=["Aegis Config"])

_ADMIN_USERNAME: str = "admin"


def _user_allowed_base(username: str) -> Path:
    """Returns the filesystem subtree the user is allowed to select as root.
    Admin: home directory. Others: ~/sc-archive/<username>."""
    if username == _ADMIN_USERNAME:
        return Path.home().resolve()
    base = Path(settings.get("workspace_base", str(Path.home() / "sc-archive")))
    return (base / username).resolve()


def _user_fs_base(username: str) -> Path:
    """Returns the root from which the picker browses. Always starts at home."""
    return Path.home().resolve()


def _workspace_rel(username: str) -> str | None:
    """Returns the user workspace path relative to home, or None for admin."""
    if username == _ADMIN_USERNAME:
        return None
    home = Path.home().resolve()
    allowed = _user_allowed_base(username)
    try:
        return str(allowed.relative_to(home))
    except ValueError:
        # workspace_base is outside home — treat as admin-level
        return None


@router.get("/root-picker", response_class=HTMLResponse)
async def root_picker(
    request: Request,
    path: str = "",
    username: str = Depends(get_current_user),
):
    """Workspace selection modal. Non-admin users are confined to their workspace root."""
    fs_base = _user_fs_base(username)
    ws_rel = _workspace_rel(username)

    if ws_rel is not None:
        # Clamp path: must equal or be under the user's workspace
        if not path or not (path == ws_rel or path.startswith(ws_rel + "/")):
            path = ws_rel

    directories = await list_only_directories(path, base=fs_base)

    parent_path = None if not (path and path != ".") else str(Path(path).parent)
    if parent_path == ".":
        parent_path = ""

    if ws_rel is not None:
        # Prevent navigating above workspace root
        if parent_path is not None and not (
            parent_path == ws_rel or parent_path.startswith(ws_rel + "/")
        ):
            parent_path = None

    # display_prefix: the absolute prefix shown in the UI before the relative current_path
    display_prefix = str(fs_base).rstrip("/") + "/"

    context = {
        "request": request,
        "directories": directories,
        "current_path": path,
        "parent_path": parent_path,
        "display_prefix": display_prefix,
    }

    if request.headers.get("HX-Target") == "root-picker-body":
        return templates.TemplateResponse(
            request=request, name="components/root_picker_body.html", context=context
        )

    return templates.TemplateResponse(
        request=request, name="components/root_picker.html", context=context
    )


@router.post("/root-picker/select", response_class=HTMLResponse)
async def select_root(
    request: Request,
    path: str = Form(""),
    username: str = Depends(get_current_user),
):
    """Applies the new workspace for the current user.
    Non-admin users are restricted to their allowed base directory."""
    fs_base = _user_fs_base(username)
    clean = path.strip("/")
    # Logical path: normpath prevents "../" traversal without following symlinks.
    # Confinement check runs on the logical path so symlinks pointing outside
    # fs_base are still reachable by all users.
    logical_root = Path(os.path.normpath(fs_base / clean)) if clean else fs_base

    allowed_base = _user_allowed_base(username)
    if not str(logical_root).startswith(str(allowed_base)):
        raise AccessDeniedError(
            f"ACCESS_DENIED: Root outside allowed workspace for '{username}'"
        )

    # resolve() here follows symlinks to get the real filesystem path for the root
    new_root = logical_root.resolve()
    set_project_root(new_root)
    await auth_service.update_user_root(username, new_root)

    items = await list_directory_contents(".")
    context = {
        "request": request,
        "items": items,
        "current_path": ".",
        "breadcrumbs": [{"name": "ROOT", "path": "."}],
    }
    return templates.TemplateResponse(
        request=request, name="components/file_list.html", context=context
    )
