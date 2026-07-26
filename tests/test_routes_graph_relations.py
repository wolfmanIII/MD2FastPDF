"""Tests for routes/graph.py::_build_relation_edges — projects the typed
relation index onto the graph view's node-id space (root-relative paths)."""
from pathlib import Path

import pytest

from logic.relations_index import RelationIndexBuilder
from routes.graph import _build_relation_edges


def _write(root: Path, rel_path: str, content: str) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestBuildRelationEdges:
    @pytest.mark.anyio
    async def test_single_resolved_relation(self, archive_root: Path):
        _write(archive_root, "ships/Beowulf.md", (
            "---\ntype: ship\ncrew: [Kira Venn]\n---\n\nMercantile Type-A.\n"
        ))
        _write(archive_root, "npcs/Kira Venn.md", "---\ntype: npc\n---\n\nPilota.\n")

        index = await RelationIndexBuilder().build()
        edges = _build_relation_edges(index)

        assert edges == [{
            "source": "ships/Beowulf.md",
            "target": "npcs/Kira Venn.md",
            "relation": "crew",
            "label": "Equipaggio",
        }]

    @pytest.mark.anyio
    async def test_symmetric_relation_declared_once_from_one_side(self, archive_root: Path):
        _write(archive_root, "npcs/A.md", "---\ntype: npc\nhostile_to: [B]\n---\n\nA.\n")
        _write(archive_root, "npcs/B.md", "---\ntype: npc\n---\n\nB.\n")

        index = await RelationIndexBuilder().build()
        edges = _build_relation_edges(index)

        # Declared only by A — must appear exactly once, not duplicated via in_edges.
        assert edges == [{
            "source": "npcs/A.md",
            "target": "npcs/B.md",
            "relation": "hostile_to",
            "label": "Ostile a",
        }]

    @pytest.mark.anyio
    async def test_no_relations_declared_returns_empty_list(self, archive_root: Path):
        _write(archive_root, "npcs/Solo.md", "---\ntype: npc\n---\n\nNessuna relazione.\n")

        index = await RelationIndexBuilder().build()
        assert _build_relation_edges(index) == []

    @pytest.mark.anyio
    async def test_dangling_reference_never_included(self, archive_root: Path):
        _write(archive_root, "npcs/A.md", "---\ntype: npc\nmentor_of: [Nessuno]\n---\n\nA.\n")

        index = await RelationIndexBuilder().build()
        assert index.dangling  # sanity: the reference really is dangling
        assert _build_relation_edges(index) == []
