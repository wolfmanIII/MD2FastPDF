import httpx
import bleach
import base64
import mimetypes
import re
import logging
import unicodedata
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Optional, Callable, Protocol

import markdown
from pypdf import PdfReader, PdfWriter

_log = logging.getLogger(__name__)

from config.settings import settings
from logic.exceptions import ConversionError
from logic.relations import strip_frontmatter

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
            strip_frontmatter(content),
            extensions=['fenced_code', 'tables', 'attr_list', 'toc']
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


class PdfOutlineInjector:
    """Post-processes Gotenberg PDF output to inject a navigable bookmark outline."""

    _HEADING = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    _INLINE = re.compile(r'\*{1,3}([^*]+)\*{1,3}|`([^`]+)`|!?\[([^\]]*)\]\([^)]*\)')
    _SLUG_STRIP = re.compile(r'[^\w\s-]')
    _SLUG_SPACES = re.compile(r'[\s_-]+')

    def inject(self, pdf_bytes: bytes, markdown_content: str) -> bytes:
        headings = self._extract_headings(markdown_content)
        if not headings:
            return pdf_bytes
        try:
            return self._inject_outline(pdf_bytes, headings)
        except Exception:
            _log.warning("PDF outline injection failed — returning original PDF")
            return pdf_bytes

    def _extract_headings(self, content: str) -> list[tuple[int, str]]:
        # Frontmatter is metadata, never a heading source — a YAML comment line
        # (`# ...`) inside the block would otherwise match _HEADING and produce
        # a bogus bookmark for text that was never rendered into the PDF.
        return [
            (len(m.group(1)), self._clean(m.group(2)))
            for m in self._HEADING.finditer(strip_frontmatter(content))
        ]

    def _clean(self, text: str) -> str:
        return self._INLINE.sub(
            lambda m: m.group(1) or m.group(2) or m.group(3) or '', text
        ).strip()

    def _slugify(self, text: str) -> str:
        value = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        value = self._SLUG_STRIP.sub('', value).strip().lower()
        return self._SLUG_SPACES.sub('-', value)

    def _find_heading_y(self, page: object, heading_text: str) -> float | None:
        """Returns the Y coordinate in PDF user space for heading_text on the page.

        Applies CTM × TM to convert from text matrix coordinates to PDF user space:
        y_pdf = um[1]*tm[4] + um[3]*tm[5] + um[5]
        """
        chunks: list[tuple[str, float]] = []

        def visitor(text: str, um: object, tm: object, _fd: object, _fs: object) -> None:
            if text.strip() and um and tm:
                y_pdf = float(um[1]) * float(tm[4]) + float(um[3]) * float(tm[5]) + float(um[5])
                chunks.append((text, y_pdf))

        try:
            page.extract_text(visitor_text=visitor)  # type: ignore[attr-defined]
        except Exception:
            return None

        full_text = ''.join(c[0] for c in chunks)
        idx = full_text.lower().find(heading_text.lower())
        if idx == -1:
            return None

        pos = 0
        for text, y in chunks:
            if pos <= idx < pos + len(text):
                return y
            pos += len(text)
        return None

    def _locate(
        self,
        text: str,
        reader: PdfReader,
        page_texts: list[str],
        search_from: int,
    ) -> tuple[int | None, float | None]:
        for i in range(search_from, len(page_texts)):
            if text in page_texts[i] or text.lower() in page_texts[i].lower():
                y = self._find_heading_y(reader.pages[i], text)
                return i, y
        return None, None

    def _inject_outline(self, pdf_bytes: bytes, headings: list[tuple[int, str]]) -> bytes:
        from pypdf.generic import Fit

        reader = PdfReader(BytesIO(pdf_bytes))

        page_texts: list[str] = []
        for page in reader.pages:
            try:
                page_texts.append(page.extract_text() or "")
            except Exception:
                page_texts.append("")

        if not any(page_texts):
            _log.warning("PDF outline: no extractable text — returning original PDF")
            return pdf_bytes

        located: list[tuple[int, str, int, float | None]] = []
        search_from = 0
        for level, text in headings:
            page_num, top = self._locate(text, reader, page_texts, search_from)
            if page_num is not None:
                located.append((level, text, page_num, top))
                search_from = page_num

        if not located:
            return pdf_bytes

        writer = PdfWriter()
        writer.append(reader)

        stack: list[tuple[int, object]] = []
        for level, text, page_num, top in located:
            while stack and stack[-1][0] >= level:
                stack.pop()
            parent = stack[-1][1] if stack else None
            fit = Fit.xyz(left=None, top=top, zoom=None) if top is not None else None
            item = writer.add_outline_item(text, page_num, parent=parent, **({"fit": fit} if fit else {}))
            stack.append((level, item))

        output = BytesIO()
        writer.write(output)
        return output.getvalue()


class GotenbergClient:
    """Industrial HTTP gateway for the Gotenberg PDF Engine (Aegis Optimus)."""

    def __init__(
        self,
        url_provider: Callable[[], str],
        renderer: Optional[RendererProtocol] = None,
        builder: Optional[HtmlBuilderProtocol] = None,
        outline_injector: Optional[PdfOutlineInjector] = None,
    ):
        self._url_provider = url_provider
        self._renderer = renderer or MarkdownRenderer()
        self._builder = builder or PdfHtmlBuilder()
        self._outline_injector = outline_injector or PdfOutlineInjector()
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

        return self._outline_injector.inject(response.content, markdown_content)


# Global instance for app lifecycle management
gotenberg = GotenbergClient(
    url_provider=lambda: settings.get("gotenberg_ip", "http://localhost:3000"),
)

# Legacy Compatibility Entry Point
async def convert_markdown_to_pdf(markdown_content: str, filename: str, show_header_footer: bool = False, base_path: Optional[Path] = None) -> bytes:
    return await gotenberg.render_pdf(markdown_content, filename, show_header_footer, base_path=base_path)
