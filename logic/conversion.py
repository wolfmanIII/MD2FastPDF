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
    
    # Industrial CSS for PDF
    industrial_css = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=Roboto+Mono&display=swap');
    body {
        font-family: 'Inter', sans-serif;
        color: #18181b;
        line-height: 1.6;
        padding: 2cm;
    }
    h1, h2, h3 { color: #7c3aed; font-family: 'Inter', sans-serif; border-bottom: 1px solid #e4e4e7; padding-bottom: 0.3rem; margin-top: 1.5rem; }
    code { font-family: 'Roboto Mono', monospace; background: #f4f4f5; padding: 0.2rem 0.4rem; border-radius: 4px; font-size: 0.9em; }
    pre { background: #18181b; color: #f4f4f5; padding: 1rem; border-radius: 6px; overflow-x: auto; }
    pre code { background: transparent; padding: 0; color: inherit; }
    table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
    th, td { border: 1px solid #e4e4e7; padding: 0.75rem; text-align: left; }
    th { background: #f9fafb; font-weight: bold; }
    blockquote { border-left: 4px solid #7c3aed; padding-left: 1rem; color: #71717a; font-style: italic; }
    img { max-width: 100%; height: auto; }
    .header { font-size: 10px; text-transform: uppercase; color: #a1a1aa; border-bottom: 1px solid #e4e4e7; margin-bottom: 1cm; }
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
