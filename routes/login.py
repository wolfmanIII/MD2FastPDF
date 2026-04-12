"""
AEGIS_IDENTITY_ROUTER: Login, logout, and session management endpoints.
"""
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from logic.auth import auth_service
from logic.exceptions import AuthError
from config.templates import templates
from routes.deps import get_current_user

# AEGIS_AUTH_ROUTER: Identity and session control
router = APIRouter(tags=["Aegis Auth"])


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Renders the login page. Passes a one-shot error message from the session if present."""
    error = request.session.pop("login_error", None)
    return templates.TemplateResponse(request, "layouts/login.html", {"error": error})


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    """Authenticates credentials, opens a session, and redirects to the dashboard."""
    try:
        record = await auth_service.authenticate(username, password)
        request.session["username"] = username
        request.session["is_admin"] = "admin" in record.groups
        return RedirectResponse(url="/", status_code=302)
    except AuthError:
        request.session["login_error"] = "INVALID_CREDENTIALS"
        return RedirectResponse(url="/login", status_code=302)


@router.post("/logout")
async def logout(request: Request):
    """Clears the session and redirects to the login page."""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


@router.post("/auth/password", response_class=HTMLResponse)
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    username: str = Depends(get_current_user),
):
    """Changes the password for the currently authenticated user."""
    try:
        await auth_service.authenticate(username, current_password)
    except AuthError:
        return HTMLResponse(
            '<div id="pw-notification" class="text-xs font-mono text-red-400 animate-pulse">'
            '!! CURRENT_PASSWORD_INVALID !!'
            '</div>'
        )
    if len(new_password) < 4:
        return HTMLResponse(
            '<div id="pw-notification" class="text-xs font-mono text-red-400 animate-pulse">'
            '!! PASSWORD_TOO_SHORT: MIN 4 CHARS !!'
            '</div>'
        )
    await auth_service.change_password(username, new_password)
    return HTMLResponse(
        '<div id="pw-notification" class="text-xs font-mono text-green-400 animate-pulse">'
        '>> ACCESS_KEY_ROTATED // RE-LOGIN_REQUIRED'
        '</div>'
    )
