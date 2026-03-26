from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse
import psutil
import httpx
import os
from logic.templates import templates
from logic.files import get_recent_files, get_storage_stats, get_project_root

GOTENBERG_URL: str = os.getenv("GOTENBERG_URL", "http://localhost:3000")
OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")

# AEGIS_CORE_ROUTER: Central dashboard and system telemetry
router = APIRouter(tags=["Aegis Core"])

@router.get("/services/status", response_class=HTMLResponse)
async def services_status(request: Request):
    """
    Probes Gotenberg and Ollama health endpoints and returns a status fragment.
    """
    async with httpx.AsyncClient(timeout=3.0) as client:
        # Gotenberg: GET /health
        try:
            r = await client.get(f"{GOTENBERG_URL}/health")
            gotenberg_ok = r.status_code == 200
            gotenberg_status = "ONLINE" if gotenberg_ok else "DEGRADED"
        except Exception:
            gotenberg_ok = False
            gotenberg_status = "OFFLINE"

        # Ollama: GET /api/tags
        try:
            r = await client.get(f"{OLLAMA_URL}/api/tags")
            ollama_ok = r.status_code == 200
            ollama_status = "ONLINE" if ollama_ok else "DEGRADED"
            if ollama_ok:
                data = r.json()
                ollama_models = [m["name"] for m in data.get("models", [])]
            else:
                ollama_models = []
        except Exception:
            ollama_ok = False
            ollama_status = "OFFLINE"
            ollama_models = []

    context = {
        "request": request,
        "gotenberg_status": gotenberg_status,
        "gotenberg_ok": gotenberg_ok,
        "gotenberg_url": GOTENBERG_URL,
        "ollama_status": ollama_status,
        "ollama_ok": ollama_ok,
        "ollama_models": ollama_models,
        "ollama_url": OLLAMA_URL,
    }
    return templates.TemplateResponse(request=request, name="components/services_status.html", context=context)


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Main entry point for the MD2FastPDF application.
    Renders the industrial dashboard.
    """
    memory = psutil.virtual_memory()
    cpu_usage = psutil.cpu_percent()
    recent = await get_recent_files(5)
    storage = await get_storage_stats()
    
    context = {
        "request": request,
        "title": "SC-ARCHIVE // Terminal",
        "memory_usage": memory.percent,
        "cpu_usage": cpu_usage,
        "recent_files": recent,
        "storage": storage,
        "api_gateway": "CONNECTED",
        "root_name": get_project_root().name if get_project_root().name else "SYS_HOME",
        "full_root": str(get_project_root()),
        "component_template": "components/dashboard.html"
    }
    
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(request=request, name="components/dashboard.html", context=context)
    
    return templates.TemplateResponse(request=request, name="shell.html", context=context)
