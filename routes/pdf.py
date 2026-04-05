import os
from fastapi import APIRouter, Request, Response, Query
from fastapi.responses import HTMLResponse
from pathlib import Path
from typing import Optional
from config.templates import templates
from logic.files import read_file_content, read_file_bytes
from logic.conversion import convert_markdown_to_pdf
from config.settings import settings as app_settings
from routes import build_breadcrumbs

# AEGIS_CONVERSION_ROUTER: PDF and HTML processing pipeline
router = APIRouter(tags=["Aegis Conversion"])


async def _resolve_pdf_bytes(path: str, header_footer: Optional[bool]) -> bytes:
    """Resolves PDF bytes from a path — converts Markdown or passes native PDF through."""
    show_hf = header_footer if header_footer is not None else app_settings.get("pdf_branding_enabled", False)
    if str(path).lower().endswith(".pdf"):
        return await read_file_bytes(path)
    content = await read_file_content(path)
    return await convert_markdown_to_pdf(content, Path(path).name, show_header_footer=show_hf)


@router.get("/pdf/view", response_class=HTMLResponse)
async def view_pdf(request: Request, path: str):
    """
    Renders the PDF preview container.
    """
    parent_path = str(Path(path).parent)
    context = {
        "request": request,
        "path": path,
        "filename": Path(path).name,
        "breadcrumbs": build_breadcrumbs(parent_path),
        "is_pdf_file": str(path).lower().endswith(".pdf"),
        "component_template": "components/pdf_preview.html"
    }

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(request=request, name="components/pdf_preview.html", context=context)

    return templates.TemplateResponse(request=request, name="shell.html", context=context)


@router.get("/pdf/preview")
async def pdf_preview(path: str, header_footer: Optional[bool] = Query(None)):
    """
    Streams the PDF (converted or native).
    header_footer=true enables full branded header and footer. Defaults to global setting.
    """
    pdf_bytes = await _resolve_pdf_bytes(path, header_footer)
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
    pdf_bytes = await _resolve_pdf_bytes(path, header_footer)
    filename = Path(path).name if str(path).lower().endswith(".pdf") else Path(path).with_suffix(".pdf").name
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
