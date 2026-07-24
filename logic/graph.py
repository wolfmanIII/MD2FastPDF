"""
AEGIS_GRAPH_PROTOCOL: Derives a document relationship graph from Markdown
cross-links (`[text](path.md)`) found in the active archive root.
"""
import logging
import re
from pathlib import Path
from typing import Optional, TypedDict
from urllib.parse import unquote

import anyio

from logic.exceptions import AegisError
from logic.files import DirectoryLister, PathSanitizer, read_text_at

logger = logging.getLogger("aegis.graph")

_MD_LINK = re.compile(r'\[([^\]]*)\]\(([^)]+\.md)\)', re.IGNORECASE)


class GraphNode(TypedDict):
    id: str
    label: str
    group: str


class GraphEdge(TypedDict):
    source: str
    target: str


class GraphData(TypedDict):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class ArchiveGraphBuilder:
    """Builds a node/edge graph from Markdown cross-links in the active archive root."""

    @staticmethod
    async def build() -> GraphData:
        root = PathSanitizer.get_root().resolve()
        md_files = await anyio.to_thread.run_sync(ArchiveGraphBuilder._scan_md_files, root)

        nodes: dict[str, GraphNode] = {}
        edges: list[GraphEdge] = []

        for file_path in md_files:
            rel_path = str(file_path.relative_to(root))
            nodes.setdefault(rel_path, ArchiveGraphBuilder._make_node(rel_path))

            try:
                content = await read_text_at(file_path)
            except (OSError, UnicodeDecodeError) as e:
                logger.warning("AEGIS_GRAPH: impossibile leggere %s — %s", rel_path, e)
                continue

            for _, target_ref in _MD_LINK.findall(content):
                target_rel = ArchiveGraphBuilder._resolve_link(file_path, target_ref, root)
                if target_rel is None or target_rel == rel_path:
                    continue
                nodes.setdefault(target_rel, ArchiveGraphBuilder._make_node(target_rel))
                edges.append({"source": rel_path, "target": target_rel})

        return {"nodes": list(nodes.values()), "edges": edges}

    @staticmethod
    def _scan_md_files(root: Path) -> list[Path]:
        return [entry["path"] for entry in DirectoryLister.scan_markdown_files(root)]

    @staticmethod
    def _make_node(rel_path: str) -> GraphNode:
        p = Path(rel_path)
        parent = str(p.parent)
        return {"id": rel_path, "label": p.stem, "group": "root" if parent == "." else parent}

    @staticmethod
    def _resolve_link(source_file: Path, target_ref: str, resolved_root: Path) -> Optional[str]:
        """Resolves a Markdown link target to a root-relative path, or None if it
        points outside the archive, to a hidden path, or to a non-existent file."""
        target_ref = target_ref.split("#", 1)[0].split("?", 1)[0].strip()
        if not target_ref or "://" in target_ref:
            return None
        target_ref = unquote(target_ref)

        base = resolved_root if target_ref.startswith("/") else source_file.parent
        candidate = (base / target_ref.lstrip("/")).resolve()

        if not str(candidate).startswith(str(resolved_root)):
            return None

        try:
            rel_str = str(candidate.relative_to(resolved_root))
            sanitized = PathSanitizer.resolve_and_sanitize(rel_str)
        except AegisError:
            return None

        if not sanitized.is_file():
            return None
        return str(sanitized.relative_to(resolved_root))
