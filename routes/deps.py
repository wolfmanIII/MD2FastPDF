"""
AEGIS_IDENTITY_DEPS: FastAPI dependencies for authenticated routes.
"""
from fastapi import Request


def get_current_user(request: Request) -> str:
    """Returns the authenticated username from the session.
    Auth guard and root binding are handled by the auth middleware in main.py."""
    return request.session.get("username", "")
