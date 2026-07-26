import json
import anyio
from fastapi import APIRouter, Request, Body, Form
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse, RedirectResponse
from typing import Optional
from pydantic import BaseModel
from logic.oracle import generate_completion, generate_mermaid, summarize_document, oracle, PromptTemplates
from config.settings import settings as app_settings
from config.templates import templates
from logic.conversion import MarkdownRenderer
from logic.files import get_project_root
from logic.query_translation import (
    Ambiguous,
    ResolvedQuery,
    fallback_text_search,
    pop_pending_disambiguation,
    resolve_disambiguation_choice,
    resolve_translated_query,
    store_pending_disambiguation,
)
from logic.relations_service import RelationGraphService
from routes.relations import serialize_entity

_md_renderer = MarkdownRenderer()

# AEGIS_ORACLE_ROUTER: Neural interface exposure
router = APIRouter(prefix="/api/oracle", tags=["Aegis Oracle"])


@router.get("/mermaid-modal", response_class=HTMLResponse)
async def get_mermaid_modal(request: Request):
    """
    AEGIS_MODAL: Returns the mermaid synthesis fragment.
    """
    neural_on = app_settings.get("neural_link_enabled", True)
    return templates.TemplateResponse(
        request=request,
        name="components/oracle_mermaid_modal.html",
        context={"neural_on": neural_on}
    )


class PromptRequest(BaseModel):
    prompt: str


class MermaidRequest(BaseModel):
    description: str


class SummarizeRequest(BaseModel):
    content: Optional[str] = None
    path: Optional[str] = None


class ArchiveQueryRequest(BaseModel):
    message: str


@router.post("/complete")
async def oracle_complete(request: PromptRequest):
    """
    AEGIS_SSE_STREAM: Real-time neural completions for the editor.
    """
    # AEGIS_LOCKOUT: Prevent unauthorized uplink if protocol disabled
    if not app_settings.get("neural_link_enabled", True):
        async def disabled_generator():
            yield "data: " + json.dumps({"token": "", "error": "NEURAL_LINK_DISABLED"}) + "\n\n"
        return StreamingResponse(disabled_generator(), media_type="text/event-stream")

    async def event_generator():
        # Inject tactical constraints for Ghost-Text
        async for token in oracle.stream_completion(
            f"[CONTEXT_START]\n{request.prompt}\n[CONTEXT_END]\n[TASK]: Continue correctly from the end of the context.",
            system=PromptTemplates.GHOST_SYSTEM,
            options={"num_predict": 500, "temperature": 0.3}  # AEGIS_BUFF: Extra space for full sentence closures
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

    summary_html = _md_renderer.render(summary_markdown)

    # Render using the dedicated component
    return templates.TemplateResponse(
        request=request,
        name="components/oracle_summary_hud.html",
        context={
            "summary_html": summary_html,
            "status": "AEGIS_SCAN_STABLE"
        }
    )


@router.post("/archive-query", response_class=JSONResponse)
async def oracle_archive_query(payload: ArchiveQueryRequest, request: Request) -> JSONResponse:
    """
    AEGIS_ARCHIVE_TERMINAL: translates a natural-language message into a
    structured RelationIndex query (RF-11, docs/ANALISI-relazioni-query-nl.md
    §4.7, issue #19). Never a chatbot — every response is either a structured
    answer grounded in RelationIndex data, an explicit disambiguation
    request, or a plain-text search fallback, never freely generated prose
    about the campaign (RF-11 non-obiettivi).
    """
    index = await RelationGraphService.get_index()
    message = payload.message.strip()

    pending = pop_pending_disambiguation(request)
    resolved = resolve_disambiguation_choice(pending, message) if pending else None

    if resolved is None:
        raw = await oracle.translate_query(message)
        resolved = resolve_translated_query(raw, index)

    if isinstance(resolved, Ambiguous):
        store_pending_disambiguation(request, resolved.relation, resolved.candidates)
        return JSONResponse(content={
            "kind": "disambiguate",
            "candidates": [serialize_entity(e) for e in resolved.candidates],
        })

    if isinstance(resolved, ResolvedQuery):
        entities = index.related(resolved.entity_key, resolved.relation)
        return JSONResponse(content={
            "kind": "answer",
            "relation": resolved.relation,
            "results": [serialize_entity(e) for e in entities],
        })

    fallback = await fallback_text_search(message)
    return JSONResponse(content=fallback)
