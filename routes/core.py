from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse
import psutil
from logic.templates import templates
from logic.files import get_recent_files, get_storage_stats, get_project_root

# AEGIS_CORE_ROUTER: Central dashboard and system telemetry
router = APIRouter(tags=["Aegis Core"])

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Main entry point for the MD2FastPDF application.
    Renders the industrial dashboard.
    """
    memory = psutil.virtual_memory()
    cpu_usage = psutil.cpu_percent()
    recent = await get_recent_files(10)
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
    
    return templates.TemplateResponse("shell.html", context)
