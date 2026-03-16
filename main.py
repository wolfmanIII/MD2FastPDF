import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from logic.files import list_directory_contents, read_file_content, write_file_content
from pathlib import Path

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
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"title": "MD2FastPDF // Terminal"}
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
    
    return templates.TemplateResponse(
        request=request,
        name="components/file_list.html",
        context={
            "items": items,
            "current_path": path,
            "breadcrumbs": breadcrumbs
        }
    )

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

    return templates.TemplateResponse(
        request=request,
        name="components/editor.html",
        context={
            "content": content,
            "path": path,
            "filename": Path(path).name,
            "breadcrumbs": breadcrumbs
        }
    )

@app.post("/save")
async def save_file(request: Request, path: str = Form(...), content: str = Form(...)):
    """
    Persists editor content to disk.
    Returns a success fragment or trigger.
    """
    await write_file_content(path, content)
    
    # Return a status message fragment
    return HTMLResponse(
        content='<span class="text-green-500 font-mono text-xs uppercase animate-pulse">SISTEMA_AGGIORNATO // SALVATAGGIO_COMPLETATO</span>'
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
