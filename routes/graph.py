"""
AEGIS_GRAPH_ROUTER: Document relationship graph view — Markdown cross-links
(logic/graph.py) plus typed relation edges declared in frontmatter
(logic/relations_index.py), merged here into a single node-id space.
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from config.templates import templates
from logic.graph import ArchiveGraphBuilder
from logic.relations import VOCABULARY_BY_NAME
from logic.relations_index import RelationIndex
from logic.relations_service import RelationGraphService

router = APIRouter(tags=["Aegis Graph"])


def _build_relation_edges(index: RelationIndex) -> list[dict]:
    """Projects the typed relation index onto the same node-id space as
    ArchiveGraphBuilder (root-relative file paths) — both scan the same file
    set, so no new nodes are needed, only a second set of edges (issue #7,
    parts 1-2; does not touch logic/graph.py, per the issue's own scope).

    Iterates out_edges rather than related()/relations_of(): every declared
    relation appears in out_edges exactly once, regardless of whether it's
    symmetric, so no dedup step is needed here.
    """
    edges: list[dict] = []
    for (source_key, relation_name), target_keys in index.out_edges.items():
        source_entity = index.entities.get(source_key)
        relation_def = VOCABULARY_BY_NAME.get(relation_name)
        if source_entity is None or relation_def is None:
            continue
        for target_key in target_keys:
            target_entity = index.entities.get(target_key)
            if target_entity is None:
                continue
            edges.append({
                "source": str(source_entity.path),
                "target": str(target_entity.path),
                "relation": relation_name,
                "label": relation_def.label,
            })
    return edges


@router.get("/graph", response_class=HTMLResponse)
async def graph_view(request: Request):
    """Renders the document relationship graph view fragment/shell."""
    context = {
        "request": request,
        "component_template": "components/graph_view.html",
    }

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(request=request, name="components/graph_view.html", context=context)

    return templates.TemplateResponse(request=request, name="shell.html", context=context)


@router.get("/graph/data", response_class=JSONResponse)
async def graph_data(request: Request) -> JSONResponse:
    """Returns the archive's node/edge graph (Markdown cross-links), plus the
    typed relation edges declared in frontmatter, as JSON."""
    data = await ArchiveGraphBuilder.build()
    relation_index = await RelationGraphService.get_index()
    data["relation_edges"] = _build_relation_edges(relation_index)
    return JSONResponse(content=data)
