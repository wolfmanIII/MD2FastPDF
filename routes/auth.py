"""
AEGIS_IDENTITY_ROUTER: Login, logout, and session management endpoints.
"""
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from logic.auth import auth_service
from logic.exceptions import AuthError
from logic.templates import templates

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
        auth_service.authenticate(username, password)
        request.session["username"] = username
        return RedirectResponse(url="/", status_code=302)
    except AuthError:
        request.session["login_error"] = "INVALID_CREDENTIALS"
        return RedirectResponse(url="/login", status_code=302)


@router.post("/logout")
async def logout(request: Request):
    """Clears the session and redirects to the login page."""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)
