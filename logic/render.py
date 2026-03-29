import io
import os
import re
import zipfile
from typing import Optional

import httpx

from logic.exceptions import RenderError

# AEGIS_RENDER_PROTOCOL: Mermaid diagram extraction and PNG rasterization via Gotenberg
MERMAID_BLOCK_RE = re.compile(r"```mermaid\s*\n(.*?)\n```", re.DOTALL)
GOTENBERG_URL: str = os.getenv("GOTENBERG_URL", "http://localhost:3000")


def extract_mermaid_blocks(content: str) -> list[str]:
    """Extract raw Mermaid code blocks from Markdown content."""
    return MERMAID_BLOCK_RE.findall(content)


def _build_render_html(code: str) -> str:
    """Build a minimal HTML page that renders a single Mermaid diagram."""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        html, body {{
            margin: 0;
            padding: 24px;
            background: white;
            display: inline-block;
            width: max-content;
        }}
        .mermaid svg {{
            display: block;
        }}
    </style>
</head>
<body>
    <div class="mermaid">{code}</div>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: "default",
            securityLevel: "loose"
        }});
    </script>
</body>
</html>"""


async def render_mermaid_png(code: str, client: Optional[httpx.AsyncClient] = None) -> bytes:
    """Render a Mermaid code block to PNG via Gotenberg screenshot endpoint."""
    html = _build_render_html(code)
    _owned = client is None
    _client = client or httpx.AsyncClient(timeout=30.0)
    try:
        response = await _client.post(
            f"{GOTENBERG_URL}/forms/chromium/screenshot/html",
            files={"files": ("index.html", html.encode("utf-8"), "text/html")},
            data={"format": "png", "clip": "true", "waitDelay": "3s"},
        )
        response.raise_for_status()
        return response.content
    finally:
        if _owned:
            await _client.aclose()


async def render_mermaid_zip(
    content: str,
    base_name: str,
    client: Optional[httpx.AsyncClient] = None,
) -> bytes:
    """Render all Mermaid blocks in a document and package them as a ZIP archive."""
    blocks = extract_mermaid_blocks(content)
    if not blocks:
        raise RenderError("NO_MERMAID_BLOCKS_FOUND")

    buf = io.BytesIO()
    _owned = client is None
    _client = client or httpx.AsyncClient(timeout=30.0)
    try:
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, code in enumerate(blocks, 1):
                png = await render_mermaid_png(code, _client)
                zf.writestr(f"{base_name}_diagram_{i:02d}.png", png)
    finally:
        if _owned:
            await _client.aclose()

    return buf.getvalue()
