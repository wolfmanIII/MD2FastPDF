from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
import os
from pathlib import Path
from logic.templates import templates
from logic.files import (
    list_directory_contents, create_new_file, delete_file, search_files
)

# AEGIS_ARCHIVE_ROUTER: Operational file management
router = APIRouter(tags=["Aegis Archive"])

@router.get("/files", response_class=HTMLResponse)
async def list_files(request: Request, path: str = "."):
    """
    Returns the file list fragment for a given path.
    """
    items = await list_directory_contents(path)
    
    # Breadcrumb Generation
    parts = path.split(os.sep) if path != "." else []
    breadcrumbs = [{"name": "ROOT", "path": "."}]
    accumulated_path = []
    
    for part in parts:
        if part and part != ".":
            accumulated_path.append(part)
            breadcrumbs.append({
                "name": part.upper(),
                "path": os.sep.join(accumulated_path)
            })
    
    context = {
        "request": request,
        "items": items,
        "current_path": path,
        "breadcrumbs": breadcrumbs,
        "component_template": "components/file_list.html"
    }

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse("components/file_list.html", context)
    
    return templates.TemplateResponse("shell.html", context)

@router.get("/files/search", response_class=HTMLResponse)
async def perform_search(request: Request, q: str = ""):
    """
    Performs a recursive search (if q) or root listing (if empty).
    """
    if not q.strip():
        items = await list_directory_contents(".")
    else:
        items = await search_files(q)
    
    context = {
        "request": request,
        "items": items,
        "current_path": ".",
        "breadcrumbs": [{"name": "SEARCH_RESULTS", "path": "."}],
        "searching": True,
        "query": q
    }
    
    return templates.TemplateResponse("components/results_grid.html", context)

@router.get("/create/form", response_class=HTMLResponse)
async def create_file_form(request: Request, path: str = "."):
    """
    Returns the file creation modal fragment.
    """
    return templates.TemplateResponse("components/create_modal.html", {
        "request": request,
        "path": path
    })

@router.post("/create", response_class=HTMLResponse)
async def create_new_file_route(request: Request, path: str = Form("."), filename: str = Form("")):
    """
    Creates a new .md file and re-renders the list.
    """
    if not filename.strip():
        return await list_files(request, path)
        
    try:
        await create_new_file(path, filename)
    except HTTPException as e:
        return HTMLResponse(
            content=f'<div class="text-[var(--neon-cyan)] font-bold text-[10px] tracking-widest uppercase mt-4" style="text-shadow: var(--neon-glow);">SYSTEM_ERROR // {e.detail}</div>',
            status_code=400
        )
        
    return await list_files(request, path)

@router.get("/delete/confirm", response_class=HTMLResponse)
async def delete_confirm(request: Request, path: str):
    """
    Returns the delete confirmation modal.
    """
    filename = Path(path).name
    return templates.TemplateResponse("components/delete_modal.html", {
        "request": request,
        "path": path,
        "filename": filename
    })

@router.post("/delete", response_class=HTMLResponse)
async def perform_delete(request: Request, path: str = Form(...)):
    """
    Deletes the file and returns to parent dir list.
    """
    target_path = Path(path)
    parent_dir = str(target_path.parent)
    await delete_file(path)
    return await list_files(request, parent_dir)
