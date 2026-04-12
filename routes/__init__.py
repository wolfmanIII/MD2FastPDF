import os


def build_breadcrumbs(path: str) -> list[dict]:
    """Builds breadcrumb navigation data from a relative filesystem path."""
    parts = path.split(os.sep) if path != "." else []
    breadcrumbs: list[dict] = [{"name": "ROOT", "path": "."}]
    accumulated: list[str] = []
    for part in parts:
        if part and part != ".":
            accumulated.append(part)
            breadcrumbs.append({"name": part.upper(), "path": os.sep.join(accumulated)})
    return breadcrumbs