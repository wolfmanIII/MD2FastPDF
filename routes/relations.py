"""
AEGIS_RELATIONS_ROUTER: typed relation queries and diagnostics over the
active archive's frontmatter-declared relations (docs/ANALISI-relazioni-tipizzate.md).
"""
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse

from config.templates import templates
from logic.relations import VOCABULARY, Entity, canonical_key
from logic.relations_service import RelationGraphService

router = APIRouter(tags=["Aegis Relations"])

_LABELS: dict[str, str] = {r.name: r.label for r in VOCABULARY} | {r.inverse: r.label for r in VOCABULARY}


def _serialize_entity(entity: Entity) -> dict:
    """Custom shape (not jsonable_encoder): renames entity_type -> type and
    drops mtime, an internal reindex-bookkeeping field with no API meaning."""
    return {
        "key": entity.key,
        "display_name": entity.display_name,
        "path": str(entity.path),
        "type": entity.entity_type,
    }


@router.get("/api/entities/{key}/relations", response_class=JSONResponse)
async def get_entity_relations(key: str) -> JSONResponse:
    """RF-4, RF-5 — all relations of an entity, forward and inverse."""
    index = await RelationGraphService.get_index()
    relations = index.relations_of(key)
    return JSONResponse(content={
        relation_name: [_serialize_entity(e) for e in entities]
        for relation_name, entities in relations.items()
    })


@router.get("/api/entities/{key}/relations/{relation}", response_class=JSONResponse)
async def get_entity_relation(key: str, relation: str) -> JSONResponse:
    """RF-4 — a single named relation (accepts either its name or its inverse)."""
    index = await RelationGraphService.get_index()
    entities = index.related(key, relation)
    return JSONResponse(content=[_serialize_entity(e) for e in entities])


@router.get("/api/diagnostics/relations", response_class=JSONResponse)
async def get_relations_diagnostics() -> JSONResponse:
    """RF-7 — dangling references, key collisions, parse warnings."""
    diagnostics = (await RelationGraphService.get_index()).diagnostics()
    return JSONResponse(content=jsonable_encoder(diagnostics))


@router.post("/api/index/reindex", response_class=JSONResponse)
async def reindex_relations_index() -> JSONResponse:
    """Forces a full rebuild of the current root's relation index."""
    index = await RelationGraphService.reindex_all()
    return JSONResponse(content={"status": "ok", "entity_count": len(index.entities)})


@router.get("/relations/panel", response_class=HTMLResponse)
async def relations_panel(request: Request, path: str) -> HTMLResponse:
    """HTML fragment: the 'relations' section for the entity at `path`,
    consumed by the editor view. Server-rendered (not the JSON API above) to
    stay consistent with the rest of the app's HTMX/Jinja2 convention."""
    entity_key = canonical_key(Path(path).stem)
    index = await RelationGraphService.get_index()
    relations = index.relations_of(entity_key)

    context = {
        "request": request,
        "relations": relations,
        "labels": _LABELS,
    }
    return templates.TemplateResponse(request=request, name="components/entity_relations.html", context=context)
