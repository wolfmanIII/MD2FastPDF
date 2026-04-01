"""
AEGIS_ADMIN_ROUTER: Admin panel — user and group management.
All endpoints require the 'admin' group via require_admin dependency.
"""
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse

from logic.auth import auth_service, group_store, user_store
from logic.exceptions import AuthError, GroupError
from logic.templates import templates
from routes.deps import require_admin

router = APIRouter(prefix="/admin", tags=["Aegis Admin"])


def _group_members(groups: list[str], users: list) -> dict[str, int]:
    return {g: sum(1 for u in users if g in u.groups) for g in groups}


@router.get("", response_class=HTMLResponse)
async def admin_panel(
    request: Request,
    username: str = Depends(require_admin),
):
    """Admin hub. Renders panel with user list as default tab."""
    users = await auth_service.list_users()
    groups = await group_store.list_groups()
    return templates.TemplateResponse(
        request,
        "components/admin_panel.html",
        {"users": users, "groups": groups},
    )


@router.get("/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    username: str = Depends(require_admin),
):
    """User list fragment."""
    users = await auth_service.list_users()
    groups = await group_store.list_groups()
    return templates.TemplateResponse(
        request,
        "components/admin_user_list.html",
        {"users": users, "groups": groups},
    )


@router.get("/users/create", response_class=HTMLResponse)
async def admin_user_create_modal(
    request: Request,
    username: str = Depends(require_admin),
):
    """Create user modal."""
    groups = await group_store.list_groups()
    return templates.TemplateResponse(
        request,
        "components/admin_user_modal.html",
        {"groups": groups, "mode": "create", "error": None},
    )


@router.post("/users/create", response_class=HTMLResponse)
async def admin_user_create(
    request: Request,
    username: str = Depends(require_admin),
    new_username: str = Form(...),
    password: str = Form(...),
    groups: list[str] = Form(default=[]),
):
    """Creates a new user. Always returns updated user list (error shown inline in list)."""
    error = None
    try:
        await auth_service.create_user(new_username, password, groups)
    except AuthError as e:
        error = e.detail
    users = await auth_service.list_users()
    all_groups = await group_store.list_groups()
    return templates.TemplateResponse(
        request,
        "components/admin_user_list.html",
        {"users": users, "groups": all_groups, "error": error},
    )


@router.get("/users/{target}/edit", response_class=HTMLResponse)
async def admin_user_edit_modal(
    request: Request,
    target: str,
    username: str = Depends(require_admin),
):
    """Edit user groups modal."""
    user = await auth_service.get_user(target)
    if user is None:
        raise HTTPException(status_code=404, detail="USER_NOT_FOUND")
    groups = await group_store.list_groups()
    return templates.TemplateResponse(
        request,
        "components/admin_user_modal.html",
        {"user": user, "groups": groups, "mode": "edit", "error": None},
    )


@router.post("/users/{target}/edit", response_class=HTMLResponse)
async def admin_user_edit(
    request: Request,
    target: str,
    username: str = Depends(require_admin),
    groups: list[str] = Form(default=[]),
):
    """Updates user groups. Returns updated user list."""
    error = None
    try:
        await auth_service.update_user_groups(target, groups)
    except AuthError as e:
        error = e.detail
    users = await auth_service.list_users()
    all_groups = await group_store.list_groups()
    return templates.TemplateResponse(
        request,
        "components/admin_user_list.html",
        {"users": users, "groups": all_groups, "error": error},
    )


@router.post("/users/{target}/delete", response_class=HTMLResponse)
async def admin_user_delete(
    request: Request,
    target: str,
    username: str = Depends(require_admin),
):
    """Deletes a user (cannot delete 'admin'). Returns updated user list."""
    error = None
    try:
        await auth_service.delete_user(target)
    except AuthError as e:
        error = e.detail
    users = await auth_service.list_users()
    all_groups = await group_store.list_groups()
    return templates.TemplateResponse(
        request,
        "components/admin_user_list.html",
        {"users": users, "groups": all_groups, "error": error},
    )


@router.get("/groups", response_class=HTMLResponse)
async def admin_groups(
    request: Request,
    username: str = Depends(require_admin),
):
    """Group list fragment."""
    groups = await group_store.list_groups()
    users = await auth_service.list_users()
    return templates.TemplateResponse(
        request,
        "components/admin_group_list.html",
        {"groups": groups, "group_members": _group_members(groups, users)},
    )


@router.get("/groups/create", response_class=HTMLResponse)
async def admin_group_create_modal(
    request: Request,
    username: str = Depends(require_admin),
):
    """Create group modal."""
    return templates.TemplateResponse(
        request,
        "components/admin_group_modal.html",
        {"error": None},
    )


@router.post("/groups/create", response_class=HTMLResponse)
async def admin_group_create(
    request: Request,
    username: str = Depends(require_admin),
    group_name: str = Form(...),
):
    """Creates a new group. Always returns updated group list (error shown inline)."""
    error = None
    try:
        await group_store.create_group(group_name.strip().lower())
    except GroupError as e:
        error = e.detail
    groups = await group_store.list_groups()
    users = await auth_service.list_users()
    return templates.TemplateResponse(
        request,
        "components/admin_group_list.html",
        {"groups": groups, "group_members": _group_members(groups, users), "error": error},
    )


@router.post("/groups/{name}/delete", response_class=HTMLResponse)
async def admin_group_delete(
    request: Request,
    name: str,
    username: str = Depends(require_admin),
):
    """Deletes a group. Blocked if any user is assigned to it."""
    error = None
    try:
        await group_store.delete_group(name, user_store)
    except GroupError as e:
        error = e.detail
    groups = await group_store.list_groups()
    users = await auth_service.list_users()
    return templates.TemplateResponse(
        request,
        "components/admin_group_list.html",
        {"groups": groups, "group_members": _group_members(groups, users), "error": error},
    )
