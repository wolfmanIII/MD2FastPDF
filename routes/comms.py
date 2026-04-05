"""
AEGIS_COMMS_ROUTER: Signal transmission and reception endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse

from logic.comms import comms_manager, CommsManager
from logic.auth import _store, auth_service
from config.templates import templates, _render_markdown
from routes.deps import get_current_user

router = APIRouter(prefix="/comms", tags=["Aegis Comms"])


@router.get("", response_class=HTMLResponse)
async def comms_hub(
    request: Request,
    tab: str = "inbound",
    username: str = Depends(get_current_user),
) -> HTMLResponse:
    """Main COMMS hub. Ensures comms folders exist for existing users."""
    await comms_manager.ensure_comms_folders(username)
    messages = await comms_manager.list_folder(username, tab)
    context = {
        "request": request,
        "tab": tab,
        "folder": tab,
        "messages": messages,
        "username": username,
        "title": "SC-ARCHIVE // COMMS",
        "component_template": "components/comms_hub.html",
    }
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request=request, name="components/comms_hub.html", context=context
        )
    return templates.TemplateResponse(
        request=request, name="shell.html", context=context
    )


@router.get("/inbound", response_class=HTMLResponse)
async def get_inbound(
    request: Request, username: str = Depends(get_current_user)
) -> HTMLResponse:
    messages = await comms_manager.list_folder(username, "inbound")
    return templates.TemplateResponse(
        request=request,
        name="components/comms_message_list.html",
        context={"request": request, "messages": messages, "folder": "inbound"},
    )


@router.get("/outbound", response_class=HTMLResponse)
async def get_outbound(
    request: Request, username: str = Depends(get_current_user)
) -> HTMLResponse:
    messages = await comms_manager.list_folder(username, "outbound")
    return templates.TemplateResponse(
        request=request,
        name="components/comms_message_list.html",
        context={"request": request, "messages": messages, "folder": "outbound"},
    )


@router.get("/staging", response_class=HTMLResponse)
async def get_staging(
    request: Request, username: str = Depends(get_current_user)
) -> HTMLResponse:
    messages = await comms_manager.list_folder(username, "staging")
    return templates.TemplateResponse(
        request=request,
        name="components/comms_message_list.html",
        context={"request": request, "messages": messages, "folder": "staging"},
    )


@router.get("/message", response_class=HTMLResponse)
async def read_message(
    request: Request,
    folder: str,
    filename: str,
    username: str = Depends(get_current_user),
) -> HTMLResponse:
    """Reads a single message and marks it as read."""
    message = await comms_manager.get_message(username, folder, filename)
    await comms_manager.mark_read(username, folder, filename)
    return templates.TemplateResponse(
        request=request,
        name="components/comms_message_reader.html",
        context={"request": request, "message": message, "folder": folder},
    )


@router.get("/compose", response_class=HTMLResponse)
async def compose_form(
    request: Request,
    reply_to: Optional[str] = None,
    username: str = Depends(get_current_user),
) -> HTMLResponse:
    """Compose modal. reply_to format: 'folder/filename'."""
    sender_record = await auth_service.get_user(username)
    sender_groups = sender_record.groups if sender_record else []
    all_users = await auth_service.list_users()
    allowed = CommsManager.allowed_recipients(username, sender_groups, all_users)
    original: Optional[object] = None
    if reply_to:
        parts = reply_to.split("/", 1)
        if len(parts) == 2:
            try:
                original = await comms_manager.get_message(username, parts[0], parts[1])
            except Exception:
                original = None
    return templates.TemplateResponse(
        request=request,
        name="components/comms_compose_modal.html",
        context={
            "request": request,
            "recipients": allowed,
            "original": original,
            "reply_to": reply_to,
        },
    )


@router.post("/preview", response_class=HTMLResponse)
async def preview_markdown(
    request: Request,
    body: str = Form(default=""),
) -> HTMLResponse:
    """Live Markdown preview fragment for the compose modal."""
    html = _render_markdown(body) if body.strip() else ""
    return templates.TemplateResponse(
        request=request,
        name="components/comms_preview.html",
        context={"request": request, "html": html},
    )


@router.post("/send", response_class=HTMLResponse)
async def send_message(
    request: Request,
    recipients: list[str] = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    username: str = Depends(get_current_user),
) -> HTMLResponse:
    sender_record = await auth_service.get_user(username)
    sender_groups = sender_record.groups if sender_record else []
    all_users = await auth_service.list_users()
    allowed = CommsManager.allowed_recipients(username, sender_groups, all_users)
    recipient_str = "ALL" if recipients == ["ALL"] else ",".join(recipients)
    await comms_manager.send_message(username, recipient_str, subject, body, allowed)
    messages = await comms_manager.list_folder(username, "outbound")
    return templates.TemplateResponse(
        request=request,
        name="components/comms_message_list.html",
        context={
            "request": request,
            "messages": messages,
            "folder": "outbound",
            "notification": ">> SIGNAL_TRANSMITTED // DELIVERY_CONFIRMED",
        },
    )


@router.post("/draft/save", response_class=HTMLResponse)
async def save_draft(
    request: Request,
    recipients: list[str] = Form(default=[]),
    subject: str = Form(default=""),
    body: str = Form(default=""),
    draft_filename: str = Form(default=""),
    username: str = Depends(get_current_user),
) -> HTMLResponse:
    recipient_str = ",".join(recipients) if recipients else ""
    await comms_manager.save_draft(
        username, recipient_str, subject, body, draft_filename or None
    )
    return HTMLResponse(
        content='<div class="text-[10px] neon-text tracking-widest">▶ BUFFER_SECURED // DRAFT_RETAINED</div>'
    )


@router.post("/draft/send", response_class=HTMLResponse)
async def send_draft(
    request: Request,
    draft_filename: str = Form(...),
    username: str = Depends(get_current_user),
) -> HTMLResponse:
    sender_record = await auth_service.get_user(username)
    sender_groups = sender_record.groups if sender_record else []
    all_users = await auth_service.list_users()
    allowed = CommsManager.allowed_recipients(username, sender_groups, all_users)
    await comms_manager.promote_draft(username, draft_filename, allowed)
    messages = await comms_manager.list_folder(username, "outbound")
    return templates.TemplateResponse(
        request=request,
        name="components/comms_message_list.html",
        context={
            "request": request,
            "messages": messages,
            "folder": "outbound",
            "notification": ">> BUFFER_FLUSHED // SIGNAL_TRANSMITTED",
        },
    )


@router.post("/delete", response_class=HTMLResponse)
async def delete_message(
    request: Request,
    folder: str = Form(...),
    filename: str = Form(...),
    username: str = Depends(get_current_user),
) -> HTMLResponse:
    await comms_manager.delete_message(username, folder, filename)
    messages = await comms_manager.list_folder(username, folder)
    return templates.TemplateResponse(
        request=request,
        name="components/comms_message_list.html",
        context={
            "request": request,
            "messages": messages,
            "folder": folder,
            "notification": ">> SIGNAL_PURGED // RECORD_EXPUNGED",
        },
    )


@router.get("/unread-count", response_class=HTMLResponse)
async def unread_count_badge(
    request: Request,
    username: str = Depends(get_current_user),
) -> HTMLResponse:
    """Polled every 30s from navbar for unread badge + toast trigger."""
    count = await comms_manager.count_unread(username)
    return templates.TemplateResponse(
        request=request,
        name="components/comms_unread_badge.html",
        context={"request": request, "count": count},
    )
