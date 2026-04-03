"""
AEGIS_GROUPSPACE_ROUTER: Shared workspace access for group members.

Permission model enforced at logic layer (GroupSpaceAccess).
All routes require an authenticated user with group membership.
"""
from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from logic.auth import auth_service, group_store
from logic.groupspace import GroupSpaceAccess, GroupSpaceManager
from logic.templates import templates
from routes import build_breadcrumbs
from routes.deps import get_current_user

router = APIRouter(prefix="/group-space", tags=["Aegis GroupSpace"])


async def _get_user_groups(username: str) -> list[str]:
    record = await auth_service.get_user(username)
    return record.groups if record else []


@router.get("", response_class=HTMLResponse)
async def groupspace_hub(request: Request):
    """Hub: lists groups the current user belongs to."""
    username = get_current_user(request)
    user_groups = await _get_user_groups(username)
    all_groups = await group_store.list_groups()
    accessible = [g for g in all_groups if GroupSpaceAccess.has_access(g, user_groups)]
    context = {
        "groups": accessible,
        "component_template": "components/groupspace_hub.html",
    }
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(request, "components/groupspace_hub.html", context)
    return templates.TemplateResponse(request, "shell.html", context)


@router.get("/{group_name}/files", response_class=HTMLResponse)
async def groupspace_files(request: Request, group_name: str, path: str = ""):
    """File browser for a group workspace."""
    username = get_current_user(request)
    user_groups = await _get_user_groups(username)
    items = await GroupSpaceManager.list_contents(group_name, path, user_groups)
    read_only = GroupSpaceAccess.is_read_only(path or ".", user_groups)
    breadcrumbs = build_breadcrumbs(path)
    context = {
        "group_name": group_name,
        "path": path,
        "items": items,
        "read_only": read_only,
        "breadcrumbs": breadcrumbs,
        "component_template": "components/groupspace_browser.html",
    }
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(request, "components/groupspace_browser.html", context)
    return templates.TemplateResponse(request, "shell.html", context)


@router.get("/{group_name}/editor", response_class=HTMLResponse)
async def groupspace_editor(request: Request, group_name: str, path: str):
    """Editor view for a file in the group workspace."""
    username = get_current_user(request)
    user_groups = await _get_user_groups(username)
    content = await GroupSpaceManager.read_file(group_name, path, user_groups)
    read_only = GroupSpaceAccess.is_read_only(path, user_groups)
    breadcrumbs = build_breadcrumbs(str(Path(path).parent))
    context = {
        "group_name": group_name,
        "path": path,
        "filename": Path(path).name,
        "content": content,
        "read_only": read_only,
        "breadcrumbs": breadcrumbs,
        "component_template": "components/groupspace_editor.html",
    }
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(request, "components/groupspace_editor.html", context)
    return templates.TemplateResponse(request, "shell.html", context)


@router.post("/{group_name}/save", response_class=HTMLResponse)
async def groupspace_save(
    request: Request,
    group_name: str,
    path: str = Form(...),
    content: str = Form(...),
):
    """Saves a file in the group workspace. Enforces write permissions."""
    username = get_current_user(request)
    user_groups = await _get_user_groups(username)
    await GroupSpaceManager.write_file(group_name, path, content, user_groups)
    return HTMLResponse(
        content='<span id="gs-save-msg" class="neon-text font-bold text-[10px] tracking-widest uppercase mr-3">'
                'SYSTEM_UPDATED // SAVE_SUCCESSFUL</span>'
                '<script>setTimeout(() => { let el = document.getElementById("gs-save-msg"); if(el) el.remove(); }, 3000);</script>'
    )


@router.post("/{group_name}/create", response_class=HTMLResponse)
async def groupspace_create(
    request: Request,
    group_name: str,
    relative_dir: str = Form(default=""),
    filename: str = Form(...),
):
    """Creates a new file in the group workspace."""
    username = get_current_user(request)
    user_groups = await _get_user_groups(username)
    new_path = await GroupSpaceManager.create_file(group_name, relative_dir, filename, user_groups)
    items = await GroupSpaceManager.list_contents(group_name, relative_dir, user_groups)
    read_only = GroupSpaceAccess.is_read_only(relative_dir or ".", user_groups)
    breadcrumbs = build_breadcrumbs(relative_dir)
    return templates.TemplateResponse(
        request,
        "components/groupspace_browser.html",
        {
            "group_name": group_name,
            "path": relative_dir,
            "items": items,
            "read_only": read_only,
            "breadcrumbs": breadcrumbs,
            "new_path": new_path,
        },
    )


@router.post("/{group_name}/delete", response_class=HTMLResponse)
async def groupspace_delete(
    request: Request,
    group_name: str,
    path: str = Form(...),
    current_dir: str = Form(default=""),
):
    """Deletes a file from the group workspace."""
    username = get_current_user(request)
    user_groups = await _get_user_groups(username)
    await GroupSpaceManager.delete_file(group_name, path, user_groups)
    items = await GroupSpaceManager.list_contents(group_name, current_dir, user_groups)
    read_only = GroupSpaceAccess.is_read_only(current_dir or ".", user_groups)
    breadcrumbs = build_breadcrumbs(current_dir)
    return templates.TemplateResponse(
        request,
        "components/groupspace_browser.html",
        {
            "group_name": group_name,
            "path": current_dir,
            "items": items,
            "read_only": read_only,
            "breadcrumbs": breadcrumbs,
        },
    )
