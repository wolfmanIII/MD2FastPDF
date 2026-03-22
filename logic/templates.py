from fastapi.templating import Jinja2Templates
from pathlib import Path

# AEGIS_TEMPLATE_CORE: Unified access to Jinja2 fragments
templates = Jinja2Templates(directory="templates")

def parent_path_filter(value: str) -> str:
    path = Path(value)
    return str(path.parent) if str(path.parent) != "." else "."

templates.env.filters["parent_path"] = parent_path_filter
