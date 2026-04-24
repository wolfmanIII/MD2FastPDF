import httpx
import bleach
import base64
import mimetypes
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable, Protocol

import markdown

from config.settings import settings
from logic.exceptions import ConversionError

# AEGIS_PERFORMANCE_LAYER: Load industrial PDF stylesheet once at module init
_CSS_PATH = Path(__file__).parent.parent / "static" / "css" / "pdf-industrial.css"
INDUSTRIAL_CSS: str = _CSS_PATH.read_text(encoding="utf-8")

CLEANER = bleach.Cleaner(
    tags={
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'pre', 'code', 'table',
        'thead', 'tbody', 'tr', 'td', 'th', 'img', 'br', 'hr', 'blockquote',
        'ul', 'ol', 'li', 'em', 'strong', 'del', 'a', 'div', 'span'
    },
    attributes={
        '*': ['class', 'id'],
        'img': ['src', 'alt', 'title'],
        'a': ['href', 'title']
    }
)


class PageScaffolding(Protocol):
    """Defines PDF page header and footer HTML fragments."""
    @property
    def header(self) -> str: ...
    @property
    def footer(self) -> str: ...


class RendererProtocol(Protocol):
    """Converts raw Markdown content to sanitized HTML."""
    def render(self, content: str, base_path: Optional[Path] = None) -> str: ...


class HtmlBuilderProtocol(Protocol):
    """Wraps an HTML body fragment into a complete HTML document."""
    def wrap(self, html_body: str) -> str: ...


@dataclass
class DetailedScaffolding:
    """Full branded header and footer for high-detail PDF output."""
    filename_display: str

    @property
    def header(self) -> str:
        return f"""
        <div style="width: 100%; font-size: 8px; font-family: monospace; text-transform: uppercase; margin: 0 0.5in;">
            <table style="width: 100%;">
                <tr>
                    <td style="text-align: left; color: #64748b;">SC-ARCHIVE // {self.filename_display}</td>
                    <td style="text-align: right; color: #64748b;">AEGIS // SECURED</td>
                </tr>
            </table>
        </div>
        """

    @property
    def footer(self) -> str:
        return """
        <div style="width: 100%; font-size: 8px; font-family: monospace; text-transform: uppercase; margin: 0 0.5in; color: #64748b;">
            <table style="width: 100%;">
                <tr>
                    <td style="text-align: left;">OS_CORE_v2.0 // SC-ARCHIVE_PROTOCOL</td>
                    <td style="text-align: right;">PAGE <span class="pageNumber"></span> / <span class="totalPages"></span></td>
                </tr>
            </table>
        </div>
        """


class MinimalScaffolding:
    """Page-number-only footer for unbranded PDF output."""

    @property
    def header(self) -> str:
        return ""

    @property
    def footer(self) -> str:
        return """
        <div style="width: 100%; font-size: 8px; font-family: monospace; margin: 0 0.5in; color: #64748b; text-align: right;">
            <span class="pageNumber"></span> / <span class="totalPages"></span>
        </div>
        """


class MarkdownRenderer:
    """Converts Markdown source to sanitized HTML with image embedding support."""

    def render(self, content: str, base_path: Optional[Path] = None) -> str:
        raw_html = markdown.markdown(
            content,
            extensions=['fenced_code', 'tables', 'attr_list']
        )
        sanitized_html = CLEANER.clean(raw_html)
        sanitized_html = self._strip_md_links(sanitized_html)

        if base_path:
            return self._embed_images(sanitized_html, base_path)
        return sanitized_html

    def _strip_md_links(self, html: str) -> str:
        """Replaces <a href="*.md"> with plain text — .md links are broken in PDF context."""
        return re.sub(
            r'<a [^>]*href="[^"]+\.md[^"]*"[^>]*>(.*?)</a>',
            r'\1',
            html,
            flags=re.DOTALL
        )

    def _embed_images(self, html: str, base_path: Path) -> str:
        """Finds relative image paths and embeds them as Base64 data URLs."""
        from logic.files import PathSanitizer
        
        def replacer(match):
            full_tag = match.group(0)
            prefix = match.group(1)
            src = match.group(2)
            suffix = match.group(3)
            
            if src.startswith(('http', 'data:', '/')):
                return full_tag
                
            try:
                # Security: Resolve relative to base_path, then verify root isolation
                img_disk_path = (base_path / src).resolve()
                if not str(img_disk_path).startswith(str(PathSanitizer.get_root())):
                    return full_tag
                    
                if img_disk_path.is_file():
                    with open(img_disk_path, "rb") as f:
                        data = f.read()
                        encoded = base64.b64encode(data).decode('utf-8')
                        mime, _ = mimetypes.guess_type(str(img_disk_path))
                        mime = mime or "image/png"
                        return f'{prefix}data:{mime};base64,{encoded}{suffix}'
            except Exception:
                pass
            return full_tag

        return re.sub(r'(<img [^>]*src=")([^"]+)(")', replacer, html)


class PdfHtmlBuilder:
    """Assembles the final HTML document for Gotenberg rendering."""

    def wrap(self, html_body: str) -> str:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>{INDUSTRIAL_CSS}</style>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/default.min.css">
            <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
            <script>
                document.addEventListener('DOMContentLoaded', async function() {{
                    try {{
                        if (typeof hljs !== 'undefined') hljs.highlightAll();
                        mermaid.initialize({{ startOnLoad: false, theme: 'default', securityLevel: 'loose' }});
                        const blocks = document.querySelectorAll('pre code.language-mermaid');
                        if (blocks.length > 0) {{
                            blocks.forEach(function(b) {{
                                const d = document.createElement('div');
                                d.className = 'mermaid'; d.textContent = b.textContent;
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


class GotenbergClient:
    """Industrial HTTP gateway for the Gotenberg PDF Engine (Aegis Optimus)."""

    def __init__(
        self,
        url_provider: Callable[[], str],
        renderer: Optional[RendererProtocol] = None,
        builder: Optional[HtmlBuilderProtocol] = None,
    ):
        self._url_provider = url_provider
        self._renderer = renderer or MarkdownRenderer()
        self._builder = builder or PdfHtmlBuilder()
        self.client = httpx.AsyncClient(
            timeout=60.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )

    async def shutdown(self):
        await self.client.aclose()

    async def health_check(self) -> tuple[bool, str]:
        """Probes Gotenberg /health endpoint. Returns (ok, status_string)."""
        url = self._url_provider()
        try:
            r = await self.client.get(f"{url}/health", timeout=3.0)
            ok = r.status_code == 200
            return ok, "ONLINE" if ok else "DEGRADED"
        except Exception:
            return False, "OFFLINE"

    async def render_pdf(self, markdown_content: str, filename: str, show_header_footer: bool = False, base_path: Optional[Path] = None) -> bytes:
        """Converts markdown to PDF with sanitization and industrial styling."""
        url = self._url_provider()
        html_body = self._renderer.render(markdown_content, base_path=base_path)
        _name = filename if len(filename) < 40 else filename[:37] + "..."

        scaffolding: PageScaffolding = DetailedScaffolding(_name) if show_header_footer else MinimalScaffolding()
        full_html = self._builder.wrap(html_body)

        data = {
            "marginTop": "0.75", "marginBottom": "0.75", "marginLeft": "0.5", "marginRight": "0.5",
            "paperWidth": "8.27", "paperHeight": "11.69", "scale": "1.0",
            "printBackground": "true", "waitDelay": "5s"
        }

        files = {
            "index.html": ("index.html", full_html.encode("utf-8"), "text/html"),
            "footer.html": ("footer.html", scaffolding.footer.encode("utf-8"), "text/html"),
        }
        if show_header_footer:
            files["header.html"] = ("header.html", scaffolding.header.encode("utf-8"), "text/html")

        response = await self.client.post(
            f"{url}/forms/chromium/convert/html",
            data=data,
            files=files
        )

        if response.status_code != 200:
            raise ConversionError(f"GOTENBERG_ERROR: {response.text}")

        return response.content


# Global instance for app lifecycle management
gotenberg = GotenbergClient(
    url_provider=lambda: settings.get("gotenberg_ip", "http://localhost:3000"),
)

# Legacy Compatibility Entry Point
async def convert_markdown_to_pdf(markdown_content: str, filename: str, show_header_footer: bool = False, base_path: Optional[Path] = None) -> bytes:
    return await gotenberg.render_pdf(markdown_content, filename, show_header_footer, base_path=base_path)
