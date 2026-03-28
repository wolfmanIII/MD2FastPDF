import psutil
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from config.settings import settings
from logic.templates import templates
from logic.files import get_recent_files, get_storage_stats, get_project_root
from logic.conversion import gotenberg
from logic.oracle import oracle as neural_oracle

# AEGIS_CORE_ROUTER: Central dashboard and system telemetry
router = APIRouter(tags=["Aegis Core"])


def _system_context() -> dict:
    """Returns system telemetry fields shared by dashboard and stats endpoints."""
    memory = psutil.virtual_memory()
    root = get_project_root()
    return {
        "memory_usage": memory.percent,
        "cpu_usage": psutil.cpu_percent(),
        "api_gateway": "CONNECTED",
        "root_name": root.name or "SYS_HOME",
        "full_root": str(root),
    }


@router.get("/services/status", response_class=HTMLResponse)
async def services_status(request: Request):
    """
    Probes Gotenberg and Ollama health endpoints and returns a status fragment.
    """
    gotenberg_ok, gotenberg_status = await gotenberg.health_check()
    ollama = await neural_oracle.service_status()

    context = {
        "request": request,
        "gotenberg_status": gotenberg_status,
        "gotenberg_ok": gotenberg_ok,
        "gotenberg_url": settings.get("gotenberg_ip"),
        "ollama_status": ollama["status"],
        "ollama_ok": ollama["ok"],
        "ollama_chat_models": ollama["chat_models"],
        "ollama_embed_models": ollama["embed_models"],
        "ollama_url": settings.get("ollama_ip"),
    }
    return templates.TemplateResponse(request=request, name="components/services_status.html", context=context)


@router.get("/stats", response_class=HTMLResponse)
async def get_stats(request: Request):
    """
    Returns the real-time system statistics fragment for HTMX polling.
    """
    return templates.TemplateResponse(
        request=request,
        name="components/stats_grid.html",
        context={"request": request, **_system_context()},
    )


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Main entry point for the MD2FastPDF application.
    Renders the industrial dashboard.
    """
    recent = await get_recent_files(5)
    storage = await get_storage_stats()

    context = {
        "request": request,
        "title": "SC-ARCHIVE // Terminal",
        **_system_context(),
        "recent_files": recent,
        "storage": storage,
        "component_template": "components/dashboard.html",
    }

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(request=request, name="components/dashboard.html", context=context)

    return templates.TemplateResponse(request=request, name="shell.html", context=context)