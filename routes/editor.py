from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from pathlib import Path
from config.templates import templates
from logic.files import read_file_content, write_file_content
from routes import build_breadcrumbs

# AEGIS_EDITOR_ROUTER: Code and buffer management
router = APIRouter(tags=["Aegis Editor"])

@router.get("/editor", response_class=HTMLResponse)
async def get_editor(request: Request, path: str):
    """
    Returns the editor fragment (EasyMDE/Pure).
    """
    content = await read_file_content(path)
    context = {
        "request": request,
        "content": content,
        "path": path,
        "filename": Path(path).name,
        "breadcrumbs": build_breadcrumbs(str(Path(path).parent)),
        "component_template": "components/editor.html"
    }

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(request=request, name="components/editor.html", context=context)

    return templates.TemplateResponse(request=request, name="shell.html", context=context)

@router.post("/save")
async def save_file(request: Request, path: str = Form(...), content: str = Form(...)):
    """
    Saves the editor buffer to disk.
    """
    await write_file_content(path, content)
    
    return HTMLResponse(
        content='<span id="save-msg" class="neon-text font-bold text-[10px] tracking-widest uppercase mr-3">SYSTEM_UPDATED // SAVE_SUCCESSFUL</span><script>setTimeout(() => { let el = document.getElementById("save-msg"); if(el) el.remove(); }, 3000);</script>'
    )
