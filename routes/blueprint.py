"""
AEGIS_BLUEPRINT_ROUTER: Template library API.
Gallery endpoints open to all authenticated users; write/delete require admin.
"""
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse

from logic.blueprints import BlueprintManager
from logic.templates import templates
from routes.deps import require_admin

router = APIRouter(prefix="/blueprints", tags=["Aegis Blueprint"])


def _group_by_category(blueprints: list) -> dict[str, list]:
    categories: dict[str, list] = {}
    for bp in blueprints:
        categories.setdefault(bp["category"], []).append(bp)
    return categories


@router.get("/modal", response_class=HTMLResponse)
async def blueprint_modal(request: Request):
    """Gallery modal fragment — lists all blueprints grouped by category."""
    blueprints = await BlueprintManager.list_blueprints()
    return templates.TemplateResponse(
        request,
        "components/blueprint_modal.html",
        {"categories": _group_by_category(blueprints)},
    )


@router.get("/content")
async def blueprint_content(path: str):
    """Returns raw blueprint content as JSON for JS insertion into the editor."""
    content = await BlueprintManager.read_blueprint(path)
    return JSONResponse({"content": content})


@router.get("/admin", response_class=HTMLResponse)
async def blueprint_admin(
    request: Request,
    username: str = Depends(require_admin),
):
    """Admin management fragment."""
    blueprints = await BlueprintManager.list_blueprints()
    return templates.TemplateResponse(
        request,
        "components/blueprint_admin.html",
        {"categories": _group_by_category(blueprints), "blueprints": blueprints},
    )


@router.post("/save", response_class=HTMLResponse)
async def blueprint_save(
    request: Request,
    category: str = Form(...),
    filename: str = Form(...),
    content: str = Form(...),
    username: str = Depends(require_admin),
):
    """Creates or overwrites a blueprint. Returns updated admin fragment."""
    await BlueprintManager.write_blueprint(category, filename, content)
    blueprints = await BlueprintManager.list_blueprints()
    return templates.TemplateResponse(
        request,
        "components/blueprint_admin.html",
        {"categories": _group_by_category(blueprints), "blueprints": blueprints, "saved": True},
    )


@router.post("/delete", response_class=HTMLResponse)
async def blueprint_delete(
    request: Request,
    path: str = Form(...),
    username: str = Depends(require_admin),
):
    """Deletes a blueprint. Returns updated admin fragment."""
    await BlueprintManager.delete_blueprint(path)
    blueprints = await BlueprintManager.list_blueprints()
    return templates.TemplateResponse(
        request,
        "components/blueprint_admin.html",
        {"categories": _group_by_category(blueprints), "blueprints": blueprints},
    )
