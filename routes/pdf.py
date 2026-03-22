from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse
import os
from pathlib import Path
from logic.templates import templates
from logic.files import read_file_content, read_file_bytes
from logic.conversion import convert_markdown_to_pdf

# AEGIS_CONVERSION_ROUTER: PDF and HTML processing pipeline
router = APIRouter(tags=["Aegis Conversion"])

@router.get("/pdf/view", response_class=HTMLResponse)
async def view_pdf(request: Request, path: str):
    """
    Renders the PDF preview container.
    """
    parent_path = str(Path(path).parent)
    parts = parent_path.split(os.sep) if parent_path != "." else []
    breadcrumbs = [{"name": "ROOT", "path": "."}]
    accumulated_path = []
    
    for part in parts:
        if part and part != ".":
            accumulated_path.append(part)
            breadcrumbs.append({
                "name": part.upper(),
                "path": os.sep.join(accumulated_path)
            })

    context = {
        "request": request,
        "path": path,
        "filename": Path(path).name,
        "breadcrumbs": breadcrumbs,
        "is_pdf_file": str(path).lower().endswith(".pdf"),
        "component_template": "components/pdf_preview.html"
    }

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse("components/pdf_preview.html", context)

    return templates.TemplateResponse("shell.html", context)

@router.get("/pdf/preview")
async def pdf_preview(path: str):
    """
    Streams the PDF (converted or native).
    """
    if str(path).lower().endswith(".pdf"):
        pdf_bytes = await read_file_bytes(path)
    else:
        content = await read_file_content(path)
        pdf_bytes = await convert_markdown_to_pdf(content, Path(path).name)
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline"}
    )

@router.get("/pdf/download")
async def pdf_download(path: str):
    """
    Downloads the PDF.
    """
    if str(path).lower().endswith(".pdf"):
        pdf_bytes = await read_file_bytes(path)
        filename = Path(path).name
    else:
        content = await read_file_content(path)
        pdf_bytes = await convert_markdown_to_pdf(content, Path(path).name)
        filename = Path(path).with_suffix(".pdf").name
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/html/view", response_class=HTMLResponse)
async def view_html(request: Request, path: str):
    """
    Directly serves an HTML file.
    """
    content = await read_file_content(path)
    return HTMLResponse(content=content)
