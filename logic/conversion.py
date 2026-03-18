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
...
    """

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>{industrial_css}</style>
    </head>
    <body class="prose">
        <div class="header">MD2FastPDF // DOCUMENT: {filename} // AEC_CLASS_SECURED</div>
        <div class="content">{html_body}</div>
    </body>
    </html>
    """

    # Send to Gotenberg with specific A4 and Scaling parameters
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Form data for Chromium module
        data = {
            "marginTop": "0",
            "marginBottom": "0",
            "marginLeft": "0",
            "marginRight": "0",
            "paperWidth": "8.27",  # A4 Width in inches
            "paperHeight": "11.69", # A4 Height in inches
            "scale": "1.0",
            "preferCSSPageSize": "true"
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
