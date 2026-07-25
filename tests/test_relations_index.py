"""Async I/O tests for logic/relations_index.py — RelationIndexBuilder.build(),
RelationIndex query methods, and RelationIndexBuilder.reindex_file()."""
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


# ---------------------------------------------------------------------------
# related() — forward, inverse, symmetric (RF-4, RF-5)
# ---------------------------------------------------------------------------

class TestRelated:
    @pytest.mark.anyio
    async def test_forward_query(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()
        crew = {e.display_name for e in index.related("Beowulf", "crew")}
        assert crew == {"Kira Venn", "Tarn Mekel"}

    @pytest.mark.anyio
    async def test_inverse_query_by_inverse_name(self, archive_root: Path):
        # Kira Venn.md declares nothing — RF-5: still resolvable via the
        # inverse name, free from in_edges.
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()
        ships = index.related("Kira Venn", "serves_on")
        assert [e.display_name for e in ships] == ["Beowulf"]

    @pytest.mark.anyio
    async def test_symmetric_relation_visible_from_either_side(self, archive_root: Path):
        # Only Tarn Mekel.md declares hostile_to: [Kira Venn] — Kira must see
        # it too without declaring anything herself.
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()
        assert [e.display_name for e in index.related("Kira Venn", "hostile_to")] == ["Tarn Mekel"]
        assert [e.display_name for e in index.related("Tarn Mekel", "hostile_to")] == ["Kira Venn"]

    @pytest.mark.anyio
    async def test_symmetric_relation_not_double_counted_when_both_sides_declare(self, archive_root: Path):
        _write(archive_root, "A.md", "---\ntype: npc\nhostile_to: [B]\n---\n\nA.\n")
        _write(archive_root, "B.md", "---\ntype: npc\nhostile_to: [A]\n---\n\nB.\n")
        index = await RelationIndexBuilder().build()
        assert [e.display_name for e in index.related("A", "hostile_to")] == ["B"]

    @pytest.mark.anyio
    async def test_unknown_relation_name_returns_empty_list(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()
        assert index.related("Beowulf", "not_a_real_relation") == []

    @pytest.mark.anyio
    async def test_unknown_entity_returns_empty_list(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()
        assert index.related("Nobody", "crew") == []

    @pytest.mark.anyio
    async def test_entity_lookup_is_case_and_whitespace_insensitive(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()
        assert [e.display_name for e in index.related("  BEOWULF  ", "crew")] == ["Kira Venn", "Tarn Mekel"]

    @pytest.mark.anyio
    async def test_dangling_target_never_appears_in_related_result(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()
        crew = [e.display_name for e in index.related("Beowulf", "crew")]
        assert "Ghost Crewman" not in crew


# ---------------------------------------------------------------------------
# relations_of()
# ---------------------------------------------------------------------------

class TestRelationsOf:
    @pytest.mark.anyio
    async def test_aggregates_forward_and_inverse(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()
        beowulf_rel = index.relations_of("Beowulf")
        assert {e.display_name for e in beowulf_rel["crew"]} == {"Kira Venn", "Tarn Mekel"}

        kira_rel = index.relations_of("Kira Venn")
        assert [e.display_name for e in kira_rel["serves_on"]] == ["Beowulf"]
        assert [e.display_name for e in kira_rel["hostile_to"]] == ["Tarn Mekel"]

    @pytest.mark.anyio
    async def test_entity_with_no_relations_returns_empty_dict(self, archive_root: Path):
        _write(archive_root, "Lonely.md", "---\ntype: npc\n---\n\nNo relations at all.\n")
        index = await RelationIndexBuilder().build()
        assert index.relations_of("Lonely") == {}

    @pytest.mark.anyio
    async def test_unknown_entity_returns_empty_dict(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()
        assert index.relations_of("Nobody") == {}


# ---------------------------------------------------------------------------
# diagnostics()
# ---------------------------------------------------------------------------

class TestDiagnostics:
    @pytest.mark.anyio
    async def test_reports_dangling_and_collisions(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        _write(archive_root, "a/Manifest.md", "---\ntype: doc\n---\n\nA.\n")
        _write(archive_root, "b/Manifest.md", "---\ntype: doc\n---\n\nB.\n")
        index = await RelationIndexBuilder().build()
        diag = index.diagnostics()
        assert len(diag.dangling) == 1
        assert diag.dangling[0].reference == "ghost crewman"
        assert len(diag.key_collisions) == 1
        assert diag.key_collisions[0].key == "manifest"

    @pytest.mark.anyio
    async def test_reports_parse_warnings(self, archive_root: Path):
        _write(archive_root, "Bad.md", "---\ntype: ship\ncrew: 42\n---\n\nOK.\n")
        index = await RelationIndexBuilder().build()
        diag = index.diagnostics()
        assert len(diag.parse_warnings) == 1
        assert diag.parse_warnings[0].relation == "crew"

    @pytest.mark.anyio
    async def test_empty_vault_has_empty_diagnostics(self, archive_root: Path):
        index = await RelationIndexBuilder().build()
        diag = index.diagnostics()
        assert diag.dangling == [] and diag.key_collisions == [] and diag.parse_warnings == []


# ---------------------------------------------------------------------------
# reindex_file() — edit, delete, create (RF-6)
# ---------------------------------------------------------------------------

class TestReindexFile:
    @pytest.mark.anyio
    async def test_edit_replaces_only_that_files_edges(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()

        _write(archive_root, "ships/Beowulf.md", (
            "---\ntype: ship\ncrew: [Kira Venn]\n---\n\nRewritten.\n"
        ))
        builder = RelationIndexBuilder()
        await builder.reindex_file(index, Path("ships/Beowulf.md"))

        assert index.out_edges[("beowulf", "crew")] == ["kira venn"]
        # Tarn Mekel's own hostile_to edge (a different file) is untouched.
        assert index.out_edges[("tarn mekel", "hostile_to")] == ["kira venn"]
        assert index.entities["tarn mekel"].path == Path("npcs/Tarn Mekel.md")

    @pytest.mark.anyio
    async def test_passed_in_content_is_used_instead_of_rereading_disk(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()

        # Disk still has the original content (never rewritten) — only the
        # in-memory `content` argument reflects the "new" state.
        fresh_content = "---\ntype: ship\ncrew: [Kira Venn]\n---\n\nIn-memory only.\n"
        await RelationIndexBuilder().reindex_file(index, Path("ships/Beowulf.md"), fresh_content)

        assert index.out_edges[("beowulf", "crew")] == ["kira venn"]
        assert "tarn mekel" not in index.out_edges.get(("beowulf", "crew"), [])

    @pytest.mark.anyio
    async def test_edit_clears_old_dangling_reference(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()
        assert len(index.dangling) == 1  # Ghost Crewman

        _write(archive_root, "ships/Beowulf.md", (
            "---\ntype: ship\ncrew: [Kira Venn]\n---\n\nNo more ghost.\n"
        ))
        await RelationIndexBuilder().reindex_file(index, Path("ships/Beowulf.md"))
        assert index.dangling == []

    @pytest.mark.anyio
    async def test_edit_updates_entity_type(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()

        _write(archive_root, "ships/Beowulf.md", "---\ntype: derelict\n---\n\nAbandoned.\n")
        await RelationIndexBuilder().reindex_file(index, Path("ships/Beowulf.md"))
        assert index.entities["beowulf"].entity_type == "derelict"

    @pytest.mark.anyio
    async def test_new_edge_appears_after_edit(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()

        _write(archive_root, "npcs/Kira Venn.md", "---\ntype: npc\nowns: [Beowulf]\n---\n\nPilota.\n")
        await RelationIndexBuilder().reindex_file(index, Path("npcs/Kira Venn.md"))
        assert index.out_edges[("kira venn", "owns")] == ["beowulf"]

    @pytest.mark.anyio
    async def test_deleted_file_removes_its_entity(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()

        (archive_root / "npcs" / "Tarn Mekel.md").unlink()
        await RelationIndexBuilder().reindex_file(index, Path("npcs/Tarn Mekel.md"))
        assert "tarn mekel" not in index.entities

    @pytest.mark.anyio
    async def test_deleted_file_demotes_incoming_edges_to_dangling(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()
        assert index.out_edges[("beowulf", "crew")] == ["kira venn", "tarn mekel"]

        (archive_root / "npcs" / "Tarn Mekel.md").unlink()
        await RelationIndexBuilder().reindex_file(index, Path("npcs/Tarn Mekel.md"))

        assert "tarn mekel" not in index.out_edges.get(("beowulf", "crew"), [])
        assert any(d.reference == "tarn mekel" and d.relation == "crew" for d in index.dangling)

    @pytest.mark.anyio
    async def test_deleted_file_own_outgoing_edges_are_gone_not_dangling(self, archive_root: Path):
        # Tarn Mekel declared hostile_to: [Kira Venn] himself — once Tarn is
        # gone, that edge must vanish entirely, not become a dangling entry
        # attributed to a file that no longer exists.
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()

        (archive_root / "npcs" / "Tarn Mekel.md").unlink()
        await RelationIndexBuilder().reindex_file(index, Path("npcs/Tarn Mekel.md"))

        assert ("tarn mekel", "hostile_to") not in index.out_edges
        assert not any(d.origin_path == Path("npcs/Tarn Mekel.md") for d in index.dangling)

    @pytest.mark.anyio
    async def test_deletion_does_not_raise(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()
        (archive_root / "npcs" / "Tarn Mekel.md").unlink()
        await RelationIndexBuilder().reindex_file(index, Path("npcs/Tarn Mekel.md"))  # would raise if mishandled

    @pytest.mark.anyio
    async def test_reindexing_a_brand_new_file_adds_it(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()

        _write(archive_root, "ships/Zheng He.md", "---\ntype: ship\ncrew: [Kira Venn]\n---\n\nNew ship.\n")
        await RelationIndexBuilder().reindex_file(index, Path("ships/Zheng He.md"))

        assert "zheng he" in index.entities

    @pytest.mark.anyio
    async def test_reindexing_a_brand_new_file_edges_are_queryable(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()

        _write(archive_root, "ships/Zheng He.md", "---\ntype: ship\ncrew: [Kira Venn]\n---\n\nNew ship.\n")
        await RelationIndexBuilder().reindex_file(index, Path("ships/Zheng He.md"))

        served = {e.display_name for e in index.related("Kira Venn", "serves_on")}
        assert served == {"Beowulf", "Zheng He"}

    @pytest.mark.anyio
    async def test_other_files_by_path_entries_are_untouched(self, archive_root: Path):
        _seed_basic_vault(archive_root)
        index = await RelationIndexBuilder().build()
        tarn_edges_before = list(index.by_path[Path("npcs/Tarn Mekel.md")])

        _write(archive_root, "ships/Beowulf.md", "---\ntype: ship\ncrew: []\n---\n\nEmptied out.\n")
        await RelationIndexBuilder().reindex_file(index, Path("ships/Beowulf.md"))

        assert index.by_path[Path("npcs/Tarn Mekel.md")] == tarn_edges_before

    @pytest.mark.anyio
    async def test_reindexing_a_path_with_no_prior_state_is_a_no_op_safe_call(self, archive_root: Path):
        index = await RelationIndexBuilder().build()
        _write(archive_root, "Fresh.md", "---\ntype: doc\n---\n\nFirst time.\n")
        await RelationIndexBuilder().reindex_file(index, Path("Fresh.md"))
        assert "fresh" in index.entities
