from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from pathlib import Path
from logic.templates import templates
from logic.files import list_only_directories, set_project_root, list_directory_contents

# AEGIS_CONFIG_ROUTER: System environment and workspace
router = APIRouter(tags=["Aegis Config"])

@router.get("/root-picker", response_class=HTMLResponse)
async def root_picker(request: Request, path: str = ""):
    """
    Workspace selection modal.
    """
    directories = await list_only_directories(path)
    parent_path = None if not (path and path != ".") else str(Path(path).parent)
    if parent_path == ".": parent_path = ""

    context = {
        "request": request,
        "directories": directories,
        "current_path": path,
        "parent_path": parent_path
    }
    
    if request.headers.get("HX-Target") == "root-picker-body":
        return templates.TemplateResponse("components/root_picker_body.html", context)

    return templates.TemplateResponse("components/root_picker.html", context)

@router.post("/root-picker/select", response_class=HTMLResponse)
async def select_root(request: Request, path: str = Form("")):
    """
    Applies the new workspace and reloads the archive.
    """
    home = Path.home().resolve()
    new_root = home / path.strip("/")
    set_project_root(new_root)
    
    # Internal reload of the dashboard logic for HTMX
    items = await list_directory_contents(".")
    context = {
        "request": request,
        "items": items,
        "current_path": ".",
        "breadcrumbs": [{"name": "ROOT", "path": "."}],
        "component_template": "components/file_list.html"
    }
    return templates.TemplateResponse("components/file_list.html", context)
