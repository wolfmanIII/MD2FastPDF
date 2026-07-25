"""Async I/O tests for logic/relations_service.py — RelationGraphService."""
from pathlib import Path

import pytest

from logic.files import PathSanitizer
from logic.relations_service import RelationGraphService


def _write(root: Path, rel_path: str, content: str) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.fixture(autouse=True)
def _clear_cache():
    """Every test gets a clean service cache — state here is process-global."""
    RelationGraphService.invalidate_all()
    yield
    RelationGraphService.invalidate_all()


class TestGetIndex:
    @pytest.mark.anyio
    async def test_builds_index_lazily_on_first_call(self, archive_root: Path):
        _write(archive_root, "Beowulf.md", "---\ntype: ship\ncrew: [Kira Venn]\n---\n\nOK.\n")
        index = await RelationGraphService.get_index()
        assert "beowulf" in index.entities

    @pytest.mark.anyio
    async def test_second_call_returns_the_same_cached_instance(self, archive_root: Path):
        _write(archive_root, "Beowulf.md", "---\ntype: ship\n---\n\nOK.\n")
        first = await RelationGraphService.get_index()
        second = await RelationGraphService.get_index()
        assert first is second

    @pytest.mark.anyio
    async def test_cache_does_not_pick_up_new_files_without_reindex(self, archive_root: Path):
        _write(archive_root, "Beowulf.md", "---\ntype: ship\n---\n\nOK.\n")
        await RelationGraphService.get_index()
        _write(archive_root, "NewShip.md", "---\ntype: ship\n---\n\nAdded after first build.\n")
        index = await RelationGraphService.get_index()
        assert "newship" not in index.entities

    @pytest.mark.anyio
    async def test_different_roots_get_independent_indexes(self, tmp_path: Path):
        root_a = tmp_path / "user_a"
        root_b = tmp_path / "user_b"
        root_a.mkdir()
        root_b.mkdir()
        _write(root_a, "OnlyInA.md", "---\ntype: doc\n---\n\nA.\n")
        _write(root_b, "OnlyInB.md", "---\ntype: doc\n---\n\nB.\n")

        PathSanitizer.bind_request_root(root_a)
        index_a = await RelationGraphService.get_index()

        PathSanitizer.bind_request_root(root_b)
        index_b = await RelationGraphService.get_index()

        assert "onlyina" in index_a.entities
        assert "onlyina" not in index_b.entities
        assert "onlyinb" in index_b.entities
        assert "onlyinb" not in index_a.entities


class TestReindexFile:
    @pytest.mark.anyio
    async def test_updates_the_current_roots_cached_index(self, archive_root: Path):
        _write(archive_root, "Beowulf.md", "---\ntype: ship\ncrew: []\n---\n\nOK.\n")
        _write(archive_root, "Kira Venn.md", "---\ntype: npc\n---\n\nPilota.\n")
        index = await RelationGraphService.get_index()
        assert index.out_edges == {}

        _write(archive_root, "Beowulf.md", "---\ntype: ship\ncrew: [Kira Venn]\n---\n\nUpdated.\n")
        await RelationGraphService.reindex_file("Beowulf.md")

        refreshed = await RelationGraphService.get_index()
        assert refreshed.out_edges[("beowulf", "crew")] == ["kira venn"]
        assert refreshed is index  # same object, mutated in place

    @pytest.mark.anyio
    async def test_is_a_no_op_when_no_index_has_been_built_yet(self, archive_root: Path):
        _write(archive_root, "Beowulf.md", "---\ntype: ship\n---\n\nOK.\n")
        # No prior get_index() call — index for this root doesn't exist yet.
        await RelationGraphService.reindex_file("Beowulf.md")  # must not raise
        index = await RelationGraphService.get_index()
        assert "beowulf" in index.entities  # the eventual full build picks it up anyway

    @pytest.mark.anyio
    async def test_only_affects_the_current_root(self, tmp_path: Path):
        root_a = tmp_path / "user_a"
        root_b = tmp_path / "user_b"
        root_a.mkdir()
        root_b.mkdir()
        _write(root_a, "Ship.md", "---\ntype: ship\ncrew: []\n---\n\nA.\n")
        _write(root_b, "Ship.md", "---\ntype: ship\ncrew: []\n---\n\nB.\n")

        PathSanitizer.bind_request_root(root_a)
        await RelationGraphService.get_index()
        PathSanitizer.bind_request_root(root_b)
        index_b = await RelationGraphService.get_index()

        _write(root_a, "Ship.md", "---\ntype: ship\ncrew: [Kira Venn]\n---\n\nUpdated A only.\n")
        PathSanitizer.bind_request_root(root_a)
        await RelationGraphService.reindex_file("Ship.md")

        assert index_b.out_edges == {}  # root_b's cached index untouched


class TestReindexAll:
    @pytest.mark.anyio
    async def test_forces_a_fresh_build_reflecting_new_files(self, archive_root: Path):
        _write(archive_root, "Beowulf.md", "---\ntype: ship\n---\n\nOK.\n")
        await RelationGraphService.get_index()

        _write(archive_root, "NewShip.md", "---\ntype: ship\n---\n\nAdded.\n")
        index = await RelationGraphService.reindex_all()

        assert "newship" in index.entities

    @pytest.mark.anyio
    async def test_result_replaces_the_cache_for_get_index(self, archive_root: Path):
        _write(archive_root, "Beowulf.md", "---\ntype: ship\n---\n\nOK.\n")
        await RelationGraphService.get_index()
        _write(archive_root, "NewShip.md", "---\ntype: ship\n---\n\nAdded.\n")
        await RelationGraphService.reindex_all()

        cached = await RelationGraphService.get_index()
        assert "newship" in cached.entities
