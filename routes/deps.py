"""
AEGIS_IDENTITY_DEPS: FastAPI dependencies for authenticated routes.
"""
from fastapi import Depends, HTTPException, Request
from logic.auth import auth_service


def get_current_user(request: Request) -> str:
    """Returns the authenticated username from the session.
    Auth guard and root binding are handled by the auth middleware in main.py."""
    return request.session.get("username", "")


async def require_admin(username: str = Depends(get_current_user)) -> str:
    """Raises HTTP 403 if the current user does not have the 'admin' group."""
    record = await auth_service.get_user(username)
    if not record or "admin" not in record.groups:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    return username
