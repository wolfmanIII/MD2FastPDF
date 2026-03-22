import httpx
import anyio
import os
import bleach
from typing import Optional
import markdown
from jinja2 import Environment, FileSystemLoader

# AEGIS_PERFORMANCE_LAYER: Pre-allocated resources for fast PDF processing
GOTENBERG_URL = os.getenv("GOTENBERG_URL", "http://localhost:3000")

# 1. Industrial CSS (Pre-cached)
INDUSTRIAL_CSS = """
@page { size: A4; margin: 2cm; }
body { font-family: 'Inter', -apple-system, sans-serif; color: #000000; line-height: 1.6; margin: 1cm; padding: 0; width: calc(100% - 2cm); }
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
.mermaid { background: white; padding: 1rem; border-radius: 8px; margin: 1.5rem 0; text-align: center; border: 1px solid #e2e8f0; }
"""

# 2. Bleach Policy (Pre-compiled)
CLEANER = bleach.Cleaner(
    tags={
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'pre', 'code', 'table', 
        'thead', 'tbody', 'tr', 'td', 'th', 'img', 'br', 'hr', 'blockquote',
        'ul', 'ol', 'li', 'em', 'strong', 'del', 'a', 'div', 'span'
    },
    attributes={
        '*': ['class', 'id', 'style'],
        'img': ['src', 'alt', 'title'],
        'a': ['href', 'title']
    }
)

# 3. Persistent Client Connection Pool
_http_client = httpx.AsyncClient(timeout=60.0, limits=httpx.Limits(max_keepalive_connections=5, max_connections=10))

async def convert_markdown_to_pdf(markdown_content: str, filename: str) -> bytes:
    """
    Converts markdown content to PDF using Gotenberg (Aegis Optimus Path).
    """
    # Fast Markdown Render
    raw_html = markdown.markdown(
        markdown_content, 
        extensions=['fenced_code', 'tables', 'attr_list'] # Removed 'toc' for speed unless strictly needed
    )
    
    # Fast Sanitization (using pre-compiled cleaner)
    html_body = CLEANER.clean(raw_html)

    _name = filename if len(filename) < 40 else filename[:37] + "..."
    
    header_html = f"""
    <div style="width: 100%; font-size: 8px; font-family: monospace; text-transform: uppercase; margin: 0 0.5in;">
        <table style="width: 100%;">
            <tr>
                <td style="text-align: left; color: #64748b;">SC-ARCHIVE // {_name}</td>
                <td style="text-align: right; color: #64748b;">AEGIS // SECURED</td>
            </tr>
        </table>
    </div>
    """
    
    footer_html = """
    <div style="width: 100%; font-size: 8px; font-family: monospace; text-transform: uppercase; margin: 0 0.5in; color: #64748b;">
        <table style="width: 100%;">
            <tr>
                <td style="text-align: left;">OS_CORE_v2.0 // SC-ARCHIVE_PROTOCOL</td>
                <td style="text-align: right;">PAGE <span class="pageNumber"></span> / <span class="totalPages"></span></td>
            </tr>
        </table>
    </div>
    """

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>{INDUSTRIAL_CSS}</style>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
        <script>
            document.addEventListener('DOMContentLoaded', async function() {{
                try {{
                    mermaid.initialize({{ startOnLoad: false, theme: 'default', securityLevel: 'loose' }});
                    const blocks = document.querySelectorAll('pre code.language-mermaid');
                    if (blocks.length > 0) {{
                        blocks.forEach(function(b) {{
                            const d = document.createElement('div');
                            d.className = 'mermaid';
                            d.textContent = b.textContent;
                            b.parentElement.parentElement.replaceChild(d, b.parentElement);
                        }});
                        await mermaid.run();
                    }}
                }} catch (err) {{ }}
            }});
        </script>
    </head>
    <body class="prose"><div class="content">{html_body}</div></body>
    </html>
    """

    # Send to Gotenberg (Aegis Optimus Connection)
    # Reusing global _http_client to avoid connection overhead
    data = {
        "marginTop": "0.75", "marginBottom": "0.75", "marginLeft": "0.5", "marginRight": "0.5",
        "paperWidth": "8.27", "paperHeight": "11.69", "scale": "1.0",
        "printBackground": "true", "waitDelay": "5s"
    }
    
    files = {
        "index.html": ("index.html", full_html.encode("utf-8"), "text/html"),
        "header.html": ("header.html", header_html.encode("utf-8"), "text/html"),
        "footer.html": ("footer.html", footer_html.encode("utf-8"), "text/html")
    }
    
    response = await _http_client.post(
        f"{GOTENBERG_URL}/forms/chromium/convert/html",
        data=data,
        files=files
    )
    
    if response.status_code != 200:
        raise Exception(f"Gotenberg error: {response.text}")
        
    return response.content
