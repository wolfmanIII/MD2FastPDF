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

_LABELS: dict[str, str] = {r.name: r.label for r in VOCABULARY} | {r.inverse: r.inverse_label for r in VOCABULARY} | {
    "_scenes": "Scene",
}

# npcs:/organizations: are also used, in real campaign data, by non-scene
# files (NPC sheets, lore docs) to mean "associated with this" rather than
# "appears in this scene" — both land in the same "scenes"/"scenes_org"
# inverse under the neutral "Riferimenti" label (see logic/relations.py).
# Now that scene files carry `type: scene`, genuine scene sources can be told
# apart from the rest — pull them into their own "Scene" bucket instead of
# leaving them undifferentiated among references that aren't scenes at all.
_SCENE_INVERSE_KEYS = frozenset({"scenes", "scenes_org"})


def _split_scene_references(relations: dict[str, list[Entity]]) -> dict[str, list[Entity]]:
    """Pulls `type: scene` sources out of the scenes/scenes_org inverse groups
    into a synthetic "_scenes" bucket, presentation-only (the JSON relation
    API and RelationIndex.relations_of stay untouched — this only affects the
    HTML panel's grouping)."""
    result = dict(relations)
    scene_entities: list[Entity] = []
    for key in _SCENE_INVERSE_KEYS:
        entities = result.get(key)
        if not entities:
            continue
        others = [e for e in entities if e.entity_type != "scene"]
        scene_entities.extend(e for e in entities if e.entity_type == "scene")
        if others:
            result[key] = others
        else:
            del result[key]
    if scene_entities:
        result["_scenes"] = scene_entities
    return result


def serialize_entity(entity: Entity) -> dict:
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
        relation_name: [serialize_entity(e) for e in entities]
        for relation_name, entities in relations.items()
    })


@router.get("/api/entities/{key}/relations/{relation}", response_class=JSONResponse)
async def get_entity_relation(key: str, relation: str) -> JSONResponse:
    """RF-4 — a single named relation (accepts either its name or its inverse)."""
    index = await RelationGraphService.get_index()
    entities = index.related(key, relation)
    return JSONResponse(content=[serialize_entity(e) for e in entities])


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
    relations = _split_scene_references(index.relations_of(entity_key))

    context = {
        "request": request,
        "relations": relations,
        "labels": _LABELS,
    }
    return templates.TemplateResponse(request=request, name="components/entity_relations.html", context=context)
