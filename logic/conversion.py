import httpx
import bleach
from dataclasses import dataclass
from typing import Optional, Callable, Protocol

import markdown

from logic.settings import settings

# AEGIS_PERFORMANCE_LAYER: Industrial PDF assets
INDUSTRIAL_CSS = """
@page { size: A4; margin: 2cm; }
body { font-family: 'Inter', -apple-system, sans-serif; color: #000000; line-height: 1.6; margin: 1cm; padding: 0; width: calc(100% - 2cm); }
h1 { font-size: 24pt; color: #111827; border-bottom: 2px solid #e5e7eb; padding-bottom: 10pt; margin-top: 30pt; }
h2 { font-size: 18pt; color: #111827; margin-top: 25pt; border-bottom: 1px solid #e5e7eb; }
p { font-size: 11pt; margin-bottom: 12pt; text-align: justify; }
ul, ol { margin-bottom: 12pt; padding-left: 20pt; }
ul { list-style-type: disc; }
ol { list-style-type: decimal; }
li { margin-bottom: 4pt; font-size: 11pt; }
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
    def render(self, content: str) -> str: ...


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
    """Converts Markdown source to sanitized HTML."""

    def render(self, content: str) -> str:
        raw_html = markdown.markdown(
            content,
            extensions=['fenced_code', 'tables', 'attr_list']
        )
        return CLEANER.clean(raw_html)


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

    async def render_pdf(self, markdown_content: str, filename: str, show_header_footer: bool = False) -> bytes:
        """Converts markdown to PDF with sanitization and industrial styling."""
        url = self._url_provider()
        html_body = self._renderer.render(markdown_content)
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
            raise Exception(f"GOTENBERG_ERROR: {response.text}")

        return response.content


# Global instance for app lifecycle management
gotenberg = GotenbergClient(
    url_provider=lambda: settings.get("gotenberg_ip", "http://localhost:3000"),
)

# Legacy Compatibility Entry Point
async def convert_markdown_to_pdf(markdown_content: str, filename: str, show_header_footer: bool = False) -> bytes:
    return await gotenberg.render_pdf(markdown_content, filename, show_header_footer)
