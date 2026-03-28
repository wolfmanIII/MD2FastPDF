from fastapi import APIRouter, Request, Body, Form
from typing import Optional
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from logic.oracle import generate_completion, generate_mermaid, summarize_document
from logic.templates import templates
from pydantic import BaseModel
import json
import markdown

from logic.conversion import CLEANER

import anyio
from logic.files import get_project_root

# AEGIS_ORACLE_ROUTER: Neural interface exposure
router = APIRouter(prefix="/api/oracle", tags=["Aegis Oracle"])

@router.get("/mermaid-modal", response_class=HTMLResponse)
async def get_mermaid_modal(request: Request):
    """
    AEGIS_MODAL: Returns the mermaid synthesis fragment.
    """
    return templates.TemplateResponse(request=request, name="components/oracle_mermaid_modal.html", context={})

class PromptRequest(BaseModel):
    prompt: str

class MermaidRequest(BaseModel):
    description: str

class SummarizeRequest(BaseModel):
    content: Optional[str] = None
    path: Optional[str] = None

@router.post("/complete")
async def oracle_complete(request: PromptRequest):
    """
    AEGIS_SSE_STREAM: Real-time neural completions for the editor.
    """
    from logic.oracle import oracle, PromptTemplates
    from logic.settings import settings as app_settings
    
    # AEGIS_LOCKOUT: Prevent unauthorized uplink if protocol disabled
    if not app_settings.get("neural_link_enabled", True):
        async def disabled_generator():
            yield "data: " + json.dumps({"token": "", "error": "NEURAL_LINK_DISABLED"}) + "\n\n"
        return StreamingResponse(disabled_generator(), media_type="text/event-stream")

    async def event_generator():
        # Inject tactical constraints for Ghost-Text
        async for token in oracle.stream_completion(
            request.prompt, 
            system=PromptTemplates.GHOST_SYSTEM,
            options={"num_predict": 300, "temperature": 0.4} # AEGIS_BUFF: Increased capacity for full phrase completions
        ):
            # SSE format: data: <payload>\n\n
            yield f"data: {json.dumps({'token': token})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/mermaid")
async def oracle_mermaid(request: MermaidRequest):
    """
    AEGIS_SYNTHESIS: Produces Mermaid syntax from natural language.
    """
    syntax = await generate_mermaid(request.description)
    return JSONResponse(content={"syntax": syntax})

@router.get("/summarize")
async def get_summarize_fallback():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/")

@router.post("/summarize", response_class=HTMLResponse)
async def oracle_summarize(request: Request, content: Optional[str] = Form(None), path: Optional[str] = Form(None)):
    """
    AEGIS_INTELLIGENCE: Returns rendered summary for HTMX injection.
    """
    if not content and path:
        full_path = get_project_root() / path.strip("/")
        if full_path.exists() and full_path.is_file():
            content = await anyio.Path(full_path).read_text()
    
    if not content:
        return HTMLResponse(content="<div class='neon-text-red'>ERROR: NO_CONTENT_UPLOADED</div>")

    summary_markdown = await summarize_document(content)
    
    # AEGIS_SURGICAL_CLEAN: Strip potential hallucinated div tags that break layout
    if summary_markdown:
        summary_markdown = summary_markdown.replace("</div>", "").replace("<div>", "")

    # Check for neural engine errors or empty responses
    if not summary_markdown or summary_markdown.startswith("ERROR:"):
        return templates.TemplateResponse(
            request=request, 
            name="components/oracle_summary_hud.html", 
            context={
                "summary_html": f"<div class='text-red-400 font-bold'>NEURAL_SCAN_FAILURE // {summary_markdown}</div>",
                "status": "AEGIS_RECOVERY_FAILED"
            }
        )

    # Pre-render markdown to HTML safely
    summary_html = markdown.markdown(
        summary_markdown,
        extensions=['fenced_code', 'tables']
    )
    summary_html = CLEANER.clean(summary_html) # Aegis Security Seal
    
    # Render using the dedicated component
    return templates.TemplateResponse(
        request=request, 
        name="components/oracle_summary_hud.html", 
        context={
            "summary_html": summary_html,
            "status": "AEGIS_SCAN_STABLE"
        }
    )
