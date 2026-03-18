import httpx
import anyio
import os
from typing import Optional
import markdown
from jinja2 import Environment, FileSystemLoader

GOTENBERG_URL = os.getenv("GOTENBERG_URL", "http://localhost:3000")

async def convert_markdown_to_pdf(markdown_content: str, filename: str) -> bytes:
    """
    Converts markdown content to PDF using Gotenberg.
    1. Converts MD to HTML with a basic layout and industrial CSS.
    2. Sends the HTML to Gotenberg for Chromium-based PDF generation.
    """
    # Convert MD to HTML
    html_body = markdown.markdown(
        markdown_content, 
        extensions=['fenced_code', 'tables', 'toc', 'attr_list']
    )
    
    # Professional Printable CSS for PDF
    industrial_css = """
    @page {
        size: A4;
        margin: 2cm;
    }
    body {
        font-family: 'Inter', -apple-system, sans-serif;
        color: #000000;
        line-height: 1.6;
        margin: 1cm;
        padding: 0;
        width: calc(100% - 2cm);
    }
    h1 { font-size: 24pt; color: #111827; border-bottom: 2px solid #e5e7eb; padding-bottom: 10pt; margin-top: 30pt; }
    h2 { font-size: 18pt; color: #111827; margin-top: 25pt; border-bottom: 1px solid #e5e7eb; }
    p { font-size: 11pt; margin-bottom: 12pt; text-align: justify; }
    code { font-family: 'Roboto Mono', monospace; background: #f3f4f6; color: #1f2937; padding: 0.2rem 0.4rem; border-radius: 4px; font-size: 0.85em; }
    pre { background: #f8fafc; color: #334155; padding: 1rem; border-radius: 4px; border: 1px solid #e2e8f0; overflow-x: auto; font-size: 0.85em; }
    pre code { background: transparent; padding: 0; color: inherit; border: none; }
    table { width: 100%; border-collapse: collapse; margin: 1.5rem 0; font-size: 0.9em; }
    th, td { border: 1px solid #cbd5e1; padding: 0.75rem; text-align: left; }
    th { background: #f1f5f9; font-weight: 600; color: #0f172a; }
    blockquote { border-left: 4px solid #cbd5e1; padding-left: 1rem; color: #475569; font-style: italic; margin-left: 0; }
    img { max-width: 100%; height: auto; border-radius: 4px; margin: 1rem 0; }
    """

    header_template = f"""
    <html>
      <head>
        <style>
          #header {{
            padding: 0;
            margin: 0 10pt;
            width: 100%;
            font-size: 8px;
            font-family: monospace;
            text-transform: uppercase;
            border-bottom: 1px solid #00f0ff;
            display: flex;
            justify-content: space-between;
            color: #64748b;
          }}
        </style>
      </head>
      <body>
        <div id="header">
          <span>MD2FastPDF // DOCUMENT: {filename}</span>
          <span>AEGIS // CLASS_SECURED</span>
        </div>
      </body>
    </html>
    """
    
    footer_template = """
    <html>
      <head>
        <style>
          #footer {{
            padding: 0;
            margin: 0 10pt;
            width: 100%;
            font-size: 8px;
            font-family: monospace;
            text-transform: uppercase;
            border-top: 1px solid #e5e7eb;
            display: flex;
            justify-content: space-between;
            color: #64748b;
          }}
        </style>
      </head>
      <body>
        <div id="footer">
          <span>OS_CORE_v2.0 // MD2FASTPDF_PROTOCOL</span>
          <span>PAGE <span class="pageNumber"></span> / <span class="totalPages"></span></span>
        </div>
      </body>
    </html>
    """

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>{industrial_css}</style>
    </head>
    <body class="prose">
        <div class="content">{html_body}</div>
    </body>
    </html>
    """

    # Send to Gotenberg
    async with httpx.AsyncClient(timeout=30.0) as client:
        data = {
            "marginTop": "0.75",
            "marginBottom": "0.75",
            "marginLeft": "0.75",
            "marginRight": "0.75",
            "paperWidth": "8.27",
            "paperHeight": "11.69",
            "scale": "1.0",
            "displayHeaderFooter": "true",
            "headerTemplate": header_template,
            "footerTemplate": footer_template,
            "printBackground": "true"
        }
        
        files = {
            "index.html": ("index.html", full_html.encode("utf-8"), "text/html")
        }
        
        response = await client.post(
            f"{GOTENBERG_URL}/forms/chromium/convert/html",
            data=data,
            files=files
        )
        
        if response.status_code != 200:
            raise Exception(f"Gotenberg error: {response.text}")
            
        return response.content
