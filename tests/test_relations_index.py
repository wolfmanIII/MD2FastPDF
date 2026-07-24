"""Async I/O tests for logic/relations_index.py — RelationIndexBuilder.build()."""
from pathlib import Path

import pytest

from logic.relations_index import RelationIndexBuilder


def _write(root: Path, rel_path: str, content: str) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Fixture vault: 3 entities, known relations, one dangling reference.
# ---------------------------------------------------------------------------

def _seed_basic_vault(root: Path) -> None:
    _write(root, "ships/Beowulf.md", (
        "---\n"
        "type: ship\n"
        "crew: [Kira Venn, Tarn Mekel, Ghost Crewman]\n"
        "---\n\n"
        "Mercantile Type-A.\n"
    ))
    _write(root, "npcs/Kira Venn.md", (
        "---\n"
        "type: npc\n"
        "---\n\n"
        "Pilota.\n"
    ))
    _write(root, "npcs/Tarn Mekel.md", (
        "---\n"
        "type: npc\n"
        "hostile_to: [Kira Venn]\n"
        "---\n\n"
        "Ingegnere scontroso.\n"
    ))


class TestBasicVault:
    @pytest.mark.anyio
    async def test_all_three_entities_indexed(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()
        assert set(index.entities) == {"beowulf", "kira venn", "tarn mekel"}

    @pytest.mark.anyio
    async def test_entity_type_read_from_frontmatter(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()
        assert index.entities["beowulf"].entity_type == "ship"
        assert index.entities["kira venn"].entity_type == "npc"

    @pytest.mark.anyio
    async def test_entity_display_name_and_path(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()
        kira = index.entities["kira venn"]
        assert kira.display_name == "Kira Venn"
        assert kira.path == Path("npcs/Kira Venn.md")

    @pytest.mark.anyio
    async def test_entity_mtime_is_populated(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()
        assert index.entities["beowulf"].mtime > 0

    @pytest.mark.anyio
    async def test_resolved_edges_in_out_edges(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()
        assert sorted(index.out_edges[("beowulf", "crew")]) == ["kira venn", "tarn mekel"]

    @pytest.mark.anyio
    async def test_inverse_query_free_without_target_declaring_anything(self, archive_root: Path):
        # Kira Venn.md declares no relations at all — RF-5: the inverse edge
        # must still exist, populated in the same pass as out_edges.
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()
        assert index.in_edges[("kira venn", "crew")] == ["beowulf"]

    @pytest.mark.anyio
    async def test_symmetric_relation_produces_single_out_and_in_entry(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()
        assert index.out_edges[("tarn mekel", "hostile_to")] == ["kira venn"]
        assert index.in_edges[("kira venn", "hostile_to")] == ["tarn mekel"]
        # not duplicated anywhere else
        assert ("kira venn", "hostile_to") not in index.out_edges

    @pytest.mark.anyio
    async def test_by_path_tracks_edges_for_their_origin_file(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()
        beowulf_edges = index.by_path[Path("ships/Beowulf.md")]
        assert {e.relation for e in beowulf_edges} == {"crew"}
        assert len(beowulf_edges) == 3  # Kira, Tarn, and the dangling Ghost Crewman


# ---------------------------------------------------------------------------
# Dangling references (RF-7)
# ---------------------------------------------------------------------------

class TestDangling:
    @pytest.mark.anyio
    async def test_unresolved_reference_recorded_as_dangling(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()
        assert len(index.dangling) == 1
        d = index.dangling[0]
        assert d.reference == "ghost crewman"
        assert d.relation == "crew"
        assert d.origin_path == Path("ships/Beowulf.md")

    @pytest.mark.anyio
    async def test_dangling_reference_absent_from_out_edges(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()
        assert "ghost crewman" not in index.out_edges[("beowulf", "crew")]

    @pytest.mark.anyio
    async def test_dangling_does_not_create_a_phantom_entity(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()
        assert "ghost crewman" not in index.entities

    @pytest.mark.anyio
    async def test_no_exception_propagates(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        # Would raise on its own if dangling resolution were mishandled.
        await RelationIndexBuilder().build()


# ---------------------------------------------------------------------------
# Key collisions
# ---------------------------------------------------------------------------

class TestKeyCollisions:
    @pytest.mark.anyio
    async def test_same_stem_in_different_folders_is_a_collision(self, archive_root: Path):
        _write(archive_root, "a/Manifest.md", "---\ntype: doc\n---\n\nA.\n")
        _write(archive_root, "b/Manifest.md", "---\ntype: doc\n---\n\nB.\n")
        index = await RelationIndexBuilder().build()
        assert len(index.key_collisions) == 1
        assert index.key_collisions[0].key == "manifest"

    @pytest.mark.anyio
    async def test_collision_does_not_block_indexing_of_other_files(self, archive_root: Path):
        _write(archive_root, "a/Manifest.md", "---\ntype: doc\n---\n\nA.\n")
        _write(archive_root, "b/Manifest.md", "---\ntype: doc\n---\n\nB.\n")
        _write(archive_root, "Beowulf.md", "---\ntype: ship\n---\n\nOK.\n")
        index = await RelationIndexBuilder().build()
        assert "beowulf" in index.entities

    @pytest.mark.anyio
    async def test_exactly_one_entity_survives_a_collision(self, archive_root: Path):
        _write(archive_root, "a/Manifest.md", "---\ntype: doc\n---\n\nA.\n")
        _write(archive_root, "b/Manifest.md", "---\ntype: doc\n---\n\nB.\n")
        index = await RelationIndexBuilder().build()
        assert list(index.entities).count("manifest") == 1


# ---------------------------------------------------------------------------
# Robustness — never raise, always skip and warn
# ---------------------------------------------------------------------------

class TestRobustness:
    @pytest.mark.anyio
    async def test_non_markdown_files_are_ignored(self, archive_root: Path):
        _write(archive_root, "notes.txt", "not markdown")
        index = await RelationIndexBuilder().build()
        assert index.entities == {}

    @pytest.mark.anyio
    async def test_skip_dirs_are_not_scanned(self, archive_root: Path):
        _write(archive_root, ".git/HIDDEN.md", "---\ntype: doc\n---\n\nShould not be seen.\n")
        index = await RelationIndexBuilder().build()
        assert index.entities == {}

    @pytest.mark.anyio
    async def test_unreadable_binary_file_is_skipped_not_raised(self, archive_root: Path):
        bad = archive_root / "Corrupt.md"
        bad.write_bytes(b"\xff\xfe\x00\x00not valid utf-8 \x80\x81")
        _write(archive_root, "Beowulf.md", "---\ntype: ship\n---\n\nOK.\n")
        index = await RelationIndexBuilder().build()
        assert "corrupt" not in index.entities
        assert "beowulf" in index.entities

    @pytest.mark.anyio
    async def test_frontmatter_without_relations_produces_no_edges(self, archive_root: Path):
        _write(archive_root, "Beowulf.md", "---\ntype: ship\ntitle: The Beowulf\n---\n\nOK.\n")
        index = await RelationIndexBuilder().build()
        assert index.out_edges == {}
        assert index.dangling == []

    @pytest.mark.anyio
    async def test_file_without_frontmatter_still_becomes_an_entity(self, archive_root: Path):
        _write(archive_root, "Notes.md", "Just prose, no frontmatter at all.\n")
        index = await RelationIndexBuilder().build()
        assert "notes" in index.entities
        assert index.entities["notes"].entity_type is None

    @pytest.mark.anyio
    async def test_non_string_entity_type_is_ignored(self, archive_root: Path):
        _write(archive_root, "Beowulf.md", "---\ntype: [not, a, string]\n---\n\nOK.\n")
        index = await RelationIndexBuilder().build()
        assert index.entities["beowulf"].entity_type is None

    @pytest.mark.anyio
    async def test_empty_vault_produces_empty_index(self, archive_root: Path):
        index = await RelationIndexBuilder().build()
        assert index.entities == {}
        assert index.out_edges == {}
        assert index.in_edges == {}
        assert index.dangling == []
        assert index.key_collisions == []
