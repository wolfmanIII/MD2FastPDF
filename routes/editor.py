from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
import os
from pathlib import Path
from logic.templates import templates
from logic.files import read_file_content, write_file_content

# AEGIS_EDITOR_ROUTER: Code and buffer management
router = APIRouter(tags=["Aegis Editor"])

@router.get("/editor", response_class=HTMLResponse)
async def get_editor(request: Request, path: str):
    """
    Returns the editor fragment (EasyMDE/Pure).
    """
    content = await read_file_content(path)
    
    # Breadcrumbs
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

@router.post("/save")
async def save_file(request: Request, path: str = Form(...), content: str = Form(...)):
    """
    Saves the editor buffer to disk.
    """
    await write_file_content(path, content)
    
    return HTMLResponse(
        content='<span id="save-msg" class="text-[var(--neon-cyan)] font-bold text-[10px] tracking-widest uppercase mr-3" style="text-shadow: var(--neon-glow);">SYSTEM_UPDATED // SAVE_SUCCESSFUL</span><script>setTimeout(() => { let el = document.getElementById("save-msg"); if(el) el.remove(); }, 3000);</script>'
    )
