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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Roboto+Mono&display=swap');
    body {
        font-family: 'Inter', sans-serif;
        color: #000000;
        line-height: 1.6;
        padding: 2cm;
    }
    h1, h2, h3, h4 { color: #111827; font-family: 'Inter', sans-serif; border-bottom: 1px solid #e5e7eb; padding-bottom: 0.3rem; margin-top: 2rem; font-weight: 700; }
    code { font-family: 'Roboto Mono', monospace; background: #f3f4f6; color: #1f2937; padding: 0.2rem 0.4rem; border-radius: 4px; font-size: 0.85em; }
    pre { background: #f8fafc; color: #334155; padding: 1rem; border-radius: 4px; border: 1px solid #e2e8f0; overflow-x: auto; font-size: 0.85em; }
    pre code { background: transparent; padding: 0; color: inherit; border: none; }
    table { width: 100%; border-collapse: collapse; margin: 1.5rem 0; font-size: 0.9em; }
    th, td { border: 1px solid #cbd5e1; padding: 0.75rem; text-align: left; }
    th { background: #f1f5f9; font-weight: 600; color: #0f172a; }
    blockquote { border-left: 4px solid #cbd5e1; padding-left: 1rem; color: #475569; font-style: italic; margin-left: 0; }
    img { max-width: 100%; height: auto; border-radius: 4px; margin: 1rem 0; }
    .header { font-size: 9px; text-transform: uppercase; color: #64748b; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.5cm; margin-bottom: 1cm; letter-spacing: 0.05em; font-family: 'Roboto Mono', monospace; }
    """

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>{industrial_css}</style>
    </head>
    <body>
        <div class="header">MD2FastPDF // DOCUMENT: {filename}</div>
        {html_body}
    </body>
    </html>
    """

    # Send to Gotenberg
    async with httpx.AsyncClient(timeout=30.0) as client:
        files = {
            "index.html": ("index.html", full_html.encode("utf-8"), "text/html")
        }
        
        # We use the Chromium engine for high fidelity
        # Documentation: https://gotenberg.dev/docs/modules/chromium#html
        response = await client.post(
            f"{GOTENBERG_URL}/forms/chromium/convert/html",
            files=files
        )
        
        if response.status_code != 200:
            raise Exception(f"Gotenberg error: {response.text}")
            
        return response.content
