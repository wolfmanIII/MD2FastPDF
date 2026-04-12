"""
AEGIS_BLUEPRINT_ROUTER: Template library API.
Gallery endpoints open to all authenticated users; write/delete require admin.
"""
import re
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

from logic.blueprints import BlueprintManager
from config.templates import templates
from routes.deps import require_admin

router = APIRouter(prefix="/blueprints", tags=["Aegis Blueprint"])


@router.get("/modal", response_class=HTMLResponse)
async def blueprint_modal(request: Request):
    """Gallery modal fragment — lists all blueprints grouped by category."""
    blueprints = await BlueprintManager.list_blueprints()
    response = templates.TemplateResponse(
        request,
        "components/blueprint_modal.html",
        {"categories": BlueprintManager.group_by_category(blueprints)},
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@router.get("/content")
async def blueprint_content(path: str):
    """Returns raw blueprint content as JSON for JS insertion into the editor."""
    content = await BlueprintManager.read_blueprint(path)
    return JSONResponse({"content": content})


@router.get("/placeholders")
async def blueprint_placeholders(path: str):
    """Extract unique uppercase placeholder tokens grouped by Markdown section.

    Returns {"sections": [{"heading": "SECTION NAME", "placeholders": [...]}]}.
    Only tokens matching \[[A-Z0-9 _/\.]+\] are collected. Duplicates are
    suppressed globally (first-occurrence wins). Sections with no qualifying
    placeholders are omitted.
    """
    content = await BlueprintManager.read_blueprint(path)
    sections = _extract_placeholder_sections(content)
    return JSONResponse({"sections": sections})


_PLACEHOLDER_RE = re.compile(r'\[([A-Z0-9 _/\.]+)\]')
_HEADING_RE = re.compile(r'^#{1,6}\s+(.+)$')


def _extract_placeholder_sections(content: str) -> list[dict]:
    """Parse blueprint lines, grouping found placeholders under their Markdown heading."""
    current_heading = "DOCUMENT"
    sections: dict[str, list[str]] = {}
    seen: set[str] = set()

    for line in content.splitlines():
        m = _HEADING_RE.match(line)
        if m:
            # Derive heading label: strip placeholders, punctuation, uppercase
            label = _PLACEHOLDER_RE.sub("", m.group(1)).strip(" —-/").upper()
            if label:
                current_heading = label
            # Placeholders on the heading line belong to the heading's own section
            for ph in _PLACEHOLDER_RE.findall(line):
                if ph not in seen:
                    seen.add(ph)
                    sections.setdefault(current_heading, []).append(ph)
        else:
            for ph in _PLACEHOLDER_RE.findall(line):
                if ph not in seen:
                    seen.add(ph)
                    sections.setdefault(current_heading, []).append(ph)

    return [{"heading": h, "placeholders": phs} for h, phs in sections.items() if phs]


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
        {"categories": BlueprintManager.group_by_category(blueprints), "blueprints": blueprints},
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
        {"categories": BlueprintManager.group_by_category(blueprints), "blueprints": blueprints, "saved": True},
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
        {"categories": BlueprintManager.group_by_category(blueprints), "blueprints": blueprints},
    )
