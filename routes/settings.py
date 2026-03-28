import httpx
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from logic.templates import templates
from logic.settings import settings as app_settings
from typing import Optional, List

# AEGIS_SETTINGS_ROUTER: Operational environment configuration
router = APIRouter(tags=["Aegis Settings"])

async def list_ollama_models(url: str) -> List[str]:
    """Probes Ollama for available neural models, excluding embedding-only models."""
    EMBEDDING_KEYWORDS = ["embed", "bge", "nomic", "m3", "snowflake", "arctic", "mxbai"]
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(f"{url}/api/tags")
            if r.status_code == 200:
                data = r.json()
                all_models = [m['name'] for m in data.get('models', [])]
                # Filter out models that match embedding keywords
                return [
                    m for m in all_models 
                    if not any(kw in m.lower() for kw in EMBEDDING_KEYWORDS)
                ]
    except Exception:
        pass
    return []

@router.get("/settings", response_class=HTMLResponse)
async def get_settings(request: Request):
    """
    Renders the central Aegis settings dashboard.
    """
    current = app_settings.all
    neural_on = current.get('neural_link_enabled', True)
    available_models = await list_ollama_models(current.get('ollama_ip', '')) if neural_on else []
    
    context = {
        "request": request,
        "settings": current,
        "available_models": available_models
    }
    return templates.TemplateResponse(request=request, name="components/settings_modal.html", context=context)

@router.post("/settings/save", response_class=HTMLResponse)
async def save_settings(
    request: Request,
    neural_link_enabled: bool = Form(False),
    pdf_branding_enabled: bool = Form(False),
    ollama_ip: str = Form(""),
    gotenberg_ip: str = Form(""),
    model_neural_hint: str = Form(""),
    model_neural_scan: str = Form(""),
    model_mermaid_synthesis: str = Form("")
):
    """
    Persists updated operational parameters with data-loss prevention.
    """
    app_settings.set("neural_link_enabled", neural_link_enabled)
    app_settings.set("pdf_branding_enabled", pdf_branding_enabled)
    
    # Update IPs only if provided to prevent overwriting with empty strings from disabled fields
    if ollama_ip.strip():
        app_settings.set("ollama_ip", ollama_ip.strip())
    
    if gotenberg_ip.strip():
        app_settings.set("gotenberg_ip", gotenberg_ip.strip())

    # Protect existing model configuration from being wiped by disabled form fields
    current_models = app_settings.get("models", {})
    app_settings.set("models", {
        "neural_hint": model_neural_hint if model_neural_hint else current_models.get("neural_hint"),
        "neural_scan": model_neural_scan if model_neural_scan else current_models.get("neural_scan"),
        "mermaid_synthesis": model_mermaid_synthesis if model_mermaid_synthesis else current_models.get("mermaid_synthesis")
    })
    
    from fastapi import Response
    response = Response(content="""
    <div hx-swap-oob="innerHTML:#modal-container"></div>
    <div id="save-notification" hx-swap-oob="innerHTML" class="text-xs text-green-400 animate-pulse">
        >> SYNC_SUCCESS // PARAMETERS_STABILIZED
    </div>
    """)
    response.headers["HX-Trigger"] = "settings-updated"
    return response
