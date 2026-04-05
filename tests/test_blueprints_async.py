"""Async I/O tests for logic/blueprints.py — BlueprintManager file operations."""
import pytest
from pathlib import Path

from logic.blueprints import BlueprintManager
from logic.exceptions import AccessDeniedError, NotFoundError


# ---------------------------------------------------------------------------
# list_blueprints
# ---------------------------------------------------------------------------

class TestListBlueprints:
    @pytest.mark.anyio
    async def test_returns_empty_when_root_missing(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("logic.blueprints._blueprints_root", lambda: tmp_path / "nonexistent")
        result = await BlueprintManager.list_blueprints()
        assert result == []

    @pytest.mark.anyio
    async def test_returns_blueprints_with_correct_fields(self, patch_blueprints_root: Path):
        cat = patch_blueprints_root / "narrative"
        cat.mkdir()
        (cat / "session-log.md").write_text("# Log")
        result = await BlueprintManager.list_blueprints()
        assert len(result) == 1
        assert result[0]["category"] == "narrative"
        assert result[0]["name"] == "Session Log"
        assert result[0]["path"] == "narrative/session-log.md"

    @pytest.mark.anyio
    async def test_skips_non_md_files(self, patch_blueprints_root: Path):
        cat = patch_blueprints_root / "tech"
        cat.mkdir()
        (cat / "data.txt").write_text("ignored")
        (cat / "spec.md").write_text("valid")
        result = await BlueprintManager.list_blueprints()
        assert len(result) == 1
        assert result[0]["name"] == "Spec"

    @pytest.mark.anyio
    async def test_skips_hidden_directories(self, patch_blueprints_root: Path):
        (patch_blueprints_root / ".hidden").mkdir()
        ((patch_blueprints_root / ".hidden") / "secret.md").write_text("x")
        result = await BlueprintManager.list_blueprints()
        assert result == []

    @pytest.mark.anyio
    async def test_multiple_categories_sorted(self, patch_blueprints_root: Path):
        for cat in ["tech", "narrative"]:
            d = patch_blueprints_root / cat
            d.mkdir()
            (d / "file.md").write_text("")
        result = await BlueprintManager.list_blueprints()
        categories = [r["category"] for r in result]
        assert categories == sorted(categories)


# ---------------------------------------------------------------------------
# read_blueprint
# ---------------------------------------------------------------------------

class TestReadBlueprint:
    @pytest.mark.anyio
    async def test_returns_content(self, patch_blueprints_root: Path):
        cat = patch_blueprints_root / "narrative"
        cat.mkdir()
        (cat / "npc.md").write_text("# NPC Profile")
        content = await BlueprintManager.read_blueprint("narrative/npc.md")
        assert content == "# NPC Profile"

    @pytest.mark.anyio
    async def test_missing_file_raises(self, patch_blueprints_root: Path):
        with pytest.raises(NotFoundError, match="BLUEPRINT_NOT_FOUND"):
            await BlueprintManager.read_blueprint("narrative/ghost.md")

    @pytest.mark.anyio
    async def test_traversal_raises(self, patch_blueprints_root: Path):
        with pytest.raises(AccessDeniedError, match="ACCESS_DENIED"):
            await BlueprintManager.read_blueprint("../../etc/passwd")


# ---------------------------------------------------------------------------
# write_blueprint
# ---------------------------------------------------------------------------

class TestWriteBlueprint:
    @pytest.mark.anyio
    async def test_creates_file(self, patch_blueprints_root: Path):
        rel = await BlueprintManager.write_blueprint("tech", "ship-spec", "# Ship")
        assert (patch_blueprints_root / rel).read_text() == "# Ship"

    @pytest.mark.anyio
    async def test_normalizes_filename(self, patch_blueprints_root: Path):
        rel = await BlueprintManager.write_blueprint("tech", "Ship Spec", "content")
        assert rel == "tech/ship-spec.md"

    @pytest.mark.anyio
    async def test_overwrites_existing(self, patch_blueprints_root: Path):
        cat = patch_blueprints_root / "tech"
        cat.mkdir()
        (cat / "spec.md").write_text("old")
        await BlueprintManager.write_blueprint("tech", "spec", "new")
        assert (cat / "spec.md").read_text() == "new"

    @pytest.mark.anyio
    async def test_creates_category_directory(self, patch_blueprints_root: Path):
        await BlueprintManager.write_blueprint("newcat", "doc", "body")
        assert (patch_blueprints_root / "newcat").is_dir()


# ---------------------------------------------------------------------------
# delete_blueprint
# ---------------------------------------------------------------------------

class TestDeleteBlueprint:
    @pytest.mark.anyio
    async def test_deletes_file(self, patch_blueprints_root: Path):
        cat = patch_blueprints_root / "narrative"
        cat.mkdir()
        target = cat / "old.md"
        target.write_text("bye")
        await BlueprintManager.delete_blueprint("narrative/old.md")
        assert not target.exists()

    @pytest.mark.anyio
    async def test_missing_raises(self, patch_blueprints_root: Path):
        with pytest.raises(NotFoundError, match="BLUEPRINT_NOT_FOUND"):
            await BlueprintManager.delete_blueprint("narrative/ghost.md")
