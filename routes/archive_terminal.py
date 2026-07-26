"""
AEGIS_ARCHIVE_TERMINAL_ROUTER: the "Terminale Archivio" page view (RF-11 step 8,
issue #20). Distinct from routes/oracle.py's `/api/oracle/archive-query` JSON
endpoint (issue #19), which this page's client-side script calls directly —
and distinct from COMMS (routes/comms.py): no message persistence, this is a
query interface, not inter-operator messaging.
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from config.templates import templates

router = APIRouter(tags=["Aegis Archive Terminal"])


@router.get("/archive-terminal", response_class=HTMLResponse)
async def archive_terminal_view(request: Request):
    """Renders the Archive Terminal shell/fragment."""
    context = {
        "request": request,
        "component_template": "components/archive_terminal.html",
    }

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(request=request, name="components/archive_terminal.html", context=context)

    return templates.TemplateResponse(request=request, name="shell.html", context=context)
