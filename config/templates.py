import markdown as _md
import bleach
from fastapi.templating import Jinja2Templates
from pathlib import Path

# AEGIS_TEMPLATE_CORE: Unified access to Jinja2 fragments
templates = Jinja2Templates(directory="templates")


def parent_path_filter(value: str) -> str:
    path = Path(value)
    return str(path.parent) if str(path.parent) != "." else "."


_ALLOWED_TAGS: set = bleach.sanitizer.ALLOWED_TAGS | {
    "p", "pre", "code", "h1", "h2", "h3", "h4",
    "table", "thead", "tbody", "tr", "th", "td", "br", "hr",
}


def _render_markdown(value: str) -> str:
    raw = _md.markdown(value, extensions=["fenced_code", "tables"])
    return bleach.clean(raw, tags=_ALLOWED_TAGS, strip=True)


templates.env.filters["parent_path"] = parent_path_filter
templates.env.filters["render_md"] = _render_markdown
