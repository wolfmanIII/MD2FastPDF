"""
AEGIS_GRAPH_ROUTER: Document relationship graph view (Obsidian-style).
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from config.templates import templates
from logic.graph import ArchiveGraphBuilder

router = APIRouter(tags=["Aegis Graph"])


@router.get("/graph", response_class=HTMLResponse)
async def graph_view(request: Request):
    """Renders the document relationship graph view fragment/shell."""
    context = {
        "request": request,
        "component_template": "components/graph_view.html",
    }

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(request=request, name="components/graph_view.html", context=context)

    return templates.TemplateResponse(request=request, name="shell.html", context=context)


@router.get("/graph/data", response_class=JSONResponse)
async def graph_data(request: Request) -> JSONResponse:
    """Returns the archive's node/edge graph (Markdown cross-links) as JSON."""
    data = await ArchiveGraphBuilder.build()
    return JSONResponse(content=data)
