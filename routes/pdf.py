from fastapi import APIRouter, Request, Response, Query
from fastapi.responses import HTMLResponse
import os
from pathlib import Path
from typing import Optional
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
        return templates.TemplateResponse(request=request, name="components/pdf_preview.html", context=context)

    return templates.TemplateResponse(request=request, name="shell.html", context=context)

from logic.settings import settings as app_settings

@router.get("/pdf/preview")
async def pdf_preview(path: str, header_footer: Optional[bool] = Query(None)):
    """
    Streams the PDF (converted or native).
    header_footer=true enables full branded header and footer. Defaults to global setting.
    """
    show_hf = header_footer if header_footer is not None else app_settings.get("pdf_branding_enabled", False)
    
    if str(path).lower().endswith(".pdf"):
        pdf_bytes = await read_file_bytes(path)
    else:
        content = await read_file_content(path)
        pdf_bytes = await convert_markdown_to_pdf(content, Path(path).name, show_header_footer=show_hf)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline"}
    )

@router.get("/pdf/download")
async def pdf_download(path: str, header_footer: Optional[bool] = Query(None)):
    """
    Downloads the PDF.
    header_footer=true enables full branded header and footer. Defaults to global setting.
    """
    show_hf = header_footer if header_footer is not None else app_settings.get("pdf_branding_enabled", False)

    if str(path).lower().endswith(".pdf"):
        pdf_bytes = await read_file_bytes(path)
        filename = Path(path).name
    else:
        content = await read_file_content(path)
        pdf_bytes = await convert_markdown_to_pdf(content, Path(path).name, show_header_footer=show_hf)
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
