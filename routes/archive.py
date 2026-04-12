from fastapi import APIRouter, Request, Form, HTTPException, Response
from fastapi.responses import HTMLResponse
from pathlib import Path
from config.templates import templates
from logic.files import (
    list_directory_contents, create_new_file, delete_file, rename_file, search_files, read_file_bytes
)
from routes import build_breadcrumbs


# AEGIS_ARCHIVE_ROUTER: Operational file management
router = APIRouter(tags=["Aegis Archive"])

@router.get("/files", response_class=HTMLResponse)
async def list_files(request: Request, path: str = "."):
    """
    Returns the file list fragment for a given path.
    """
    items = await list_directory_contents(path)
    context = {
        "request": request,
        "items": items,
        "current_path": path,
        "breadcrumbs": build_breadcrumbs(path),
        "component_template": "components/file_list.html"
    }

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(request=request, name="components/file_list.html", context=context)
    
    return templates.TemplateResponse(request=request, name="shell.html", context=context)

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
    
    return templates.TemplateResponse(request=request, name="components/results_grid.html", context=context)

@router.get("/create/form", response_class=HTMLResponse)
async def create_file_form(request: Request, path: str = "."):
    """
    Returns the file creation modal fragment.
    """
    return templates.TemplateResponse(request=request, name="components/create_modal.html", context={
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
            content=f'<div class="neon-text font-bold text-[10px] tracking-widest uppercase mt-4">SYSTEM_ERROR // {e.detail}</div>',
            status_code=400
        )
        
    return await list_files(request, path)

@router.get("/delete/confirm", response_class=HTMLResponse)
async def delete_confirm(request: Request, path: str):
    """
    Returns the delete confirmation modal.
    """
    filename = Path(path).name
    return templates.TemplateResponse(request=request, name="components/delete_modal.html", context={
        "request": request,
        "path": path,
        "filename": filename
    })

@router.get("/rename/form", response_class=HTMLResponse)
async def rename_file_form(request: Request, path: str):
    return templates.TemplateResponse(request=request, name="components/rename_modal.html", context={
        "request": request,
        "path": path,
        "filename": Path(path).name
    })

@router.post("/rename", response_class=HTMLResponse)
async def perform_rename(request: Request, path: str = Form(...), new_name: str = Form(...)):
    target_path = Path(path)
    parent_dir = str(target_path.parent)
    try:
        await rename_file(path, new_name)
    except HTTPException as e:
        return HTMLResponse(
            content=f'<div class="text-red-400 font-bold text-[10px] tracking-widest uppercase mt-4">RENAME_ERROR // {e.detail}</div>',
            status_code=400
        )
    return await list_files(request, parent_dir)


@router.get("/tree", response_class=HTMLResponse)
async def file_tree_root(request: Request, active: str = ""):
    """Returns the filetree sidebar content (root level, lazy-loaded)."""
    items = await list_directory_contents(".")
    return templates.TemplateResponse(request=request, name="components/filetree_sidebar.html", context={
        "request": request,
        "items": items,
        "active_path": active,
    })


@router.get("/tree/expand", response_class=HTMLResponse)
async def file_tree_expand(request: Request, path: str = ".", active: str = ""):
    """Returns child nodes for a directory (lazy expand)."""
    items = await list_directory_contents(path)
    return templates.TemplateResponse(request=request, name="components/filetree_node.html", context={
        "request": request,
        "items": items,
        "parent_path": path,
        "active_path": active,
    })


@router.get("/files/raw")
async def get_raw_file(path: str):
    """
    Serves a raw file from the archive (images, assets, etc.).
    """
    try:
        content = await read_file_bytes(path)
        # Determine media type based on extension
        ext = Path(path).suffix.lower()
        media_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".webp": "image/webp",
            ".pdf": "application/pdf"
        }
        media_type = media_types.get(ext, "application/octet-stream")
        
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": "inline"}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"FILE_NOT_FOUND")


@router.post("/delete", response_class=HTMLResponse)
async def perform_delete(request: Request, path: str = Form(...)):
    """
    Deletes the file and returns to parent dir list.
    """
    target_path = Path(path)
    parent_dir = str(target_path.parent)
    await delete_file(path)
    return await list_files(request, parent_dir)
