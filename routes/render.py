from fastapi import APIRouter, Query, HTTPException, Request
from fastapi.responses import Response, HTMLResponse
from pathlib import Path

from logic.files import read_file_content
from logic.render import extract_mermaid_blocks, render_mermaid_png, render_mermaid_zip
from logic.templates import templates

# AEGIS_RENDER_ROUTER: Mermaid diagram rasterization pipeline
router = APIRouter(tags=["Aegis Render"])


@router.get("/render/mermaid/list", response_class=HTMLResponse)
async def mermaid_list(request: Request, path: str = Query(...)):
    """Return modal listing all Mermaid blocks in a document for individual PNG download."""
    content = await read_file_content(path)
    blocks = extract_mermaid_blocks(content)
    return templates.TemplateResponse(request, "components/mermaid_list_modal.html", {
        "path": path,
        "blocks": blocks,
    })


@router.get("/render/mermaid/png")
async def mermaid_png(
    path: str = Query(...),
    index: int = Query(0, ge=0),
):
    """Render a single Mermaid block from a document to PNG."""
    content = await read_file_content(path)
    blocks = extract_mermaid_blocks(content)
    if not blocks or index >= len(blocks):
        raise HTTPException(status_code=404, detail="MERMAID_BLOCK_NOT_FOUND")
    png = await render_mermaid_png(blocks[index])
    return Response(content=png, media_type="image/png")


@router.get("/render/mermaid/bulk")
async def mermaid_bulk(path: str = Query(...)):
    """Render all Mermaid blocks from a document and return as ZIP archive."""
    content = await read_file_content(path)
    base_name = Path(path).stem
    try:
        zip_bytes = await render_mermaid_zip(content, base_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{base_name}_diagrams.zip"'},
    )
