from fastapi import APIRouter, Request, Form, Response
from fastapi.responses import HTMLResponse
from logic.templates import templates
from config.settings import settings as app_settings
from logic.oracle import oracle as neural_oracle
from typing import List

# AEGIS_SETTINGS_ROUTER: Operational environment configuration
router = APIRouter(tags=["Aegis Settings"])


@router.get("/settings", response_class=HTMLResponse)
async def get_settings(request: Request):
    """
    Renders the central Aegis settings dashboard.
    Model list is deferred to /settings/models to avoid blocking on Ollama.
    """
    context = {
        "request": request,
        "settings": app_settings.all,
    }
    return templates.TemplateResponse(request=request, name="components/settings_modal.html", context=context)


@router.get("/settings/models", response_class=HTMLResponse)
async def get_settings_models(request: Request):
    """
    Lazy-loaded fragment: probes Ollama for available models and returns the model select inputs.
    Decoupled from the main settings modal render to prevent blocking on slow/unavailable Ollama.
    """
    current = app_settings.all
    neural_on = current.get('neural_link_enabled', True)
    available_models = await neural_oracle.list_models() if neural_on else []

    context = {
        "request": request,
        "settings": current,
        "available_models": available_models,
    }
    return templates.TemplateResponse(request=request, name="components/settings_models.html", context=context)

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
    updates = {
        "neural_link_enabled": neural_link_enabled,
        "pdf_branding_enabled": pdf_branding_enabled,
    }

    # Update IPs only if provided to prevent overwriting with empty strings from disabled fields
    if ollama_ip.strip():
        updates["ollama_ip"] = ollama_ip.strip()

    if gotenberg_ip.strip():
        updates["gotenberg_ip"] = gotenberg_ip.strip()

    # Protect existing model configuration from being wiped by disabled form fields
    current_models = app_settings.get("models", {})
    updates["models"] = {
        "neural_hint": model_neural_hint if model_neural_hint else current_models.get("neural_hint"),
        "neural_scan": model_neural_scan if model_neural_scan else current_models.get("neural_scan"),
        "mermaid_synthesis": model_mermaid_synthesis if model_mermaid_synthesis else current_models.get("mermaid_synthesis")
    }

    await app_settings.batch_update(updates)

    response = Response(content="""
    <div hx-swap-oob="innerHTML:#modal-container"></div>
    <div id="save-notification" hx-swap-oob="innerHTML" class="text-xs text-green-400 animate-pulse">
        >> SYNC_SUCCESS // PARAMETERS_STABILIZED
    </div>
    """)
    response.headers["HX-Trigger"] = "settings-updated"
    return response
