import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from logic.files import (
    list_directory_contents, read_file_content, write_file_content, 
    create_new_file, delete_file, get_recent_files, get_storage_stats,
    list_only_directories, set_project_root, get_project_root
)
from logic.conversion import convert_markdown_to_pdf
from pathlib import Path
from fastapi.responses import HTMLResponse, Response
import psutil

app = FastAPI(title="MD2FastPDF", description="Industrial Markdown Editor")

# Static files and templating
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Main entry point for the MD2FastPDF application.
    Renders the industrial dashboard.
    """
    # Get real system stats
    memory = psutil.virtual_memory()
    cpu_usage = psutil.cpu_percent()
    recent = await get_recent_files(5)
    storage = await get_storage_stats()
    
    context = {
        "request": request,
        "title": "MD2FastPDF // Terminal",
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
        return templates.TemplateResponse("components/dashboard.html", context)

    return templates.TemplateResponse("shell.html", context)

@app.get("/stats", response_class=HTMLResponse)
async def get_stats(request: Request):
    """
    Returns the system status fragment for live updates.
    """
    memory = psutil.virtual_memory()
    cpu_usage = psutil.cpu_percent()
    recent = await get_recent_files(5)
    storage = await get_storage_stats()
    
    return templates.TemplateResponse(
        request=request,
        name="components/stats_grid.html",
        context={
            "memory_usage": memory.percent,
            "cpu_usage": cpu_usage,
            "recent_files": recent,
            "storage": storage,
            "api_gateway": "CONNECTED",
            "root_name": get_project_root().name if get_project_root().name else "SYS_HOME",
            "full_root": str(get_project_root())
        }
    )

@app.get("/files", response_class=HTMLResponse)
async def list_files(request: Request, path: str = "."):
    """
    Returns an HTMX fragment containing the list of files in the requested path.
    """
    items = await list_directory_contents(path)
    
    # Generate breadcrumbs
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

@app.get("/create/form", response_class=HTMLResponse)
async def create_file_form(request: Request, path: str = "."):
    """
    Returns the file creation modal fragment.
    """
    return templates.TemplateResponse("components/create_modal.html", {
        "request": request,
        "path": path
    })

@app.get("/editor", response_class=HTMLResponse)
async def get_editor(request: Request, path: str):
    """
    Returns the EasyMDE editor fragment with file content.
    """
    content = await read_file_content(path)
    
    # Generate breadcrumbs for the parent path
    parent_path = str(Path(path).parent)
    parts = parent_path.split(os.sep) if parent_path != "." else []
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
        "content": content,
        "path": path,
        "filename": Path(path).name,
        "breadcrumbs": breadcrumbs,
        "component_template": "components/editor.html"
    }

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse("components/editor.html", context)

    return templates.TemplateResponse("shell.html", context)

@app.post("/save")
async def save_file(request: Request, path: str = Form(...), content: str = Form(...)):
    """
    Persists editor content to disk.
    Returns a success fragment or trigger.
    """
    await write_file_content(path, content)
    
    # Return a status message fragment
    return HTMLResponse(
        content='<span id="save-msg" class="text-[var(--neon-cyan)] font-bold text-[10px] tracking-widest uppercase mr-3" style="text-shadow: var(--neon-glow);">SYSTEM_UPDATED // SAVE_SUCCESSFUL</span><script>setTimeout(() => { let el = document.getElementById("save-msg"); if(el) el.remove(); }, 3000);</script>'
    )

@app.post("/create", response_class=HTMLResponse)
async def create_new_file_route(request: Request, path: str = Form("."), filename: str = Form("")):
    """
    Creates a new .md file and returns the updated file list.
    """
    if not filename.strip():
        # Handle empty filename gracefully by just returning the current list
        return await list_files(request, path)
        
    try:
        await create_new_file(path, filename)
    except HTTPException as e:
        # If file already exists or other error, we should ideally show it.
        # For now, let's just return the list.
        pass
        
    return await list_files(request, path)

@app.get("/delete/confirm", response_class=HTMLResponse)
async def delete_confirm(request: Request, path: str):
    """
    Returns the delete confirmation modal fragment.
    """
    filename = Path(path).name
    return templates.TemplateResponse("components/delete_modal.html", {
        "request": request,
        "path": path,
        "filename": filename
    })

@app.post("/delete", response_class=HTMLResponse)
async def perform_delete(request: Request, path: str = Form(...)):
    """
    Deletes the file and returns the updated file list for the parent directory.
    """
    target_path = Path(path)
    parent_dir = str(target_path.parent)
    await delete_file(path)
    # Return to the file list of the parent directory
    return await list_files(request, parent_dir)

@app.get("/pdf/view", response_class=HTMLResponse)
async def view_pdf(request: Request, path: str):
    """
    Renders the PDF preview container.
    """
    parent_path = str(Path(path).parent)
    parts = parent_path.split(os.sep) if parent_path != "." else []
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
        "path": path,
        "filename": Path(path).name,
        "breadcrumbs": breadcrumbs,
        "component_template": "components/pdf_preview.html"
    }

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse("components/pdf_preview.html", context)

    return templates.TemplateResponse("shell.html", context)

@app.get("/pdf/preview")
async def pdf_preview(path: str):
    """
    Streams the generated PDF for the browser object/iframe.
    """
    content = await read_file_content(path)
    pdf_bytes = await convert_markdown_to_pdf(content, Path(path).name)
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline"}
    )

@app.get("/pdf/download")
async def pdf_download(path: str):
    """
    Provides the PDF for download.
    """
    content = await read_file_content(path)
    pdf_bytes = await convert_markdown_to_pdf(content, Path(path).name)
    
    filename = Path(path).with_suffix(".pdf").name
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/root-picker", response_class=HTMLResponse)
async def root_picker(request: Request, path: str = ""):
    """
    Returns the root directory picker modal fragment.
    """
    directories = await list_only_directories(path)
    
    # Calculate parent path for "up" navigation
    parent_path = None
    if path and path != ".":
        parent = str(Path(path).parent)
        parent_path = parent if parent != "." else ""

    return templates.TemplateResponse("components/root_picker.html", {
        "request": request,
        "directories": directories,
        "current_path": path,
        "parent_path": parent_path
    })

@app.post("/root-picker/select", response_class=HTMLResponse)
async def select_root(request: Request, path: str = Form("")):
    """
    Sets the new project root and reloads the dashboard.
    """
    home = Path.home().resolve()
    new_root = home / path.strip("/")
    set_project_root(new_root)
    
    # After setting root, return to dashboard
    return await read_root(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
