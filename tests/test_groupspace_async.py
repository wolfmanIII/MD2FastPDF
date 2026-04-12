"""Async I/O tests for logic/groupspace.py — GroupSpaceManager file operations."""
import pytest
from pathlib import Path

from logic.groupspace import GroupSpaceManager
from logic.exceptions import AccessDeniedError, NotFoundError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _group_dir(base: Path, group: str) -> Path:
    d = base / group
    d.mkdir(parents=True, exist_ok=True)
    return d


def _shared_dir(base: Path, group: str) -> Path:
    d = base / group / "shared"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# list_contents
# ---------------------------------------------------------------------------

class TestListContents:
    @pytest.mark.anyio
    async def test_returns_files_in_directory(self, patch_groupspace_base: Path):
        shared = _shared_dir(patch_groupspace_base, "crew")
        (shared / "log.md").write_text("content")
        result = await GroupSpaceManager.list_contents("crew", "shared", ["crew"])
        names = [r["name"] for r in result]
        assert "log.md" in names

    @pytest.mark.anyio
    async def test_dirs_listed_before_files(self, patch_groupspace_base: Path):
        shared = _shared_dir(patch_groupspace_base, "crew")
        (shared / "subdir").mkdir()
        (shared / "alpha.md").write_text("")
        result = await GroupSpaceManager.list_contents("crew", "shared", ["crew"])
        assert result[0]["is_dir"] is True

    @pytest.mark.anyio
    async def test_non_member_raises(self, patch_groupspace_base: Path):
        _group_dir(patch_groupspace_base, "crew")
        with pytest.raises(AccessDeniedError, match="ACCESS_DENIED"):
            await GroupSpaceManager.list_contents("crew", "", ["engineering"])

    @pytest.mark.anyio
    async def test_missing_directory_raises(self, patch_groupspace_base: Path):
        _group_dir(patch_groupspace_base, "crew")
        with pytest.raises(NotFoundError, match="DIRECTORY_NOT_FOUND"):
            await GroupSpaceManager.list_contents("crew", "nonexistent", ["crew"])

    @pytest.mark.anyio
    async def test_admin_can_list(self, patch_groupspace_base: Path):
        root = _group_dir(patch_groupspace_base, "crew")
        (root / "readme.md").write_text("")
        result = await GroupSpaceManager.list_contents("crew", "", ["admin"])
        assert any(r["name"] == "readme.md" for r in result)


# ---------------------------------------------------------------------------
# read_file
# ---------------------------------------------------------------------------

class TestReadFile:
    @pytest.mark.anyio
    async def test_returns_content(self, patch_groupspace_base: Path):
        shared = _shared_dir(patch_groupspace_base, "crew")
        (shared / "note.md").write_text("# Hello")
        content = await GroupSpaceManager.read_file("crew", "shared/note.md", ["crew"])
        assert content == "# Hello"

    @pytest.mark.anyio
    async def test_non_member_raises(self, patch_groupspace_base: Path):
        _shared_dir(patch_groupspace_base, "crew")
        with pytest.raises(AccessDeniedError):
            await GroupSpaceManager.read_file("crew", "shared/note.md", ["engineering"])

    @pytest.mark.anyio
    async def test_missing_file_raises(self, patch_groupspace_base: Path):
        _shared_dir(patch_groupspace_base, "crew")
        with pytest.raises(NotFoundError, match="FILE_NOT_FOUND"):
            await GroupSpaceManager.read_file("crew", "shared/ghost.md", ["crew"])


# ---------------------------------------------------------------------------
# write_file
# ---------------------------------------------------------------------------

class TestWriteFile:
    @pytest.mark.anyio
    async def test_admin_writes_in_root(self, patch_groupspace_base: Path):
        root = _group_dir(patch_groupspace_base, "crew")
        (root / "report.md").write_text("")
        await GroupSpaceManager.write_file("crew", "report.md", "updated", ["admin"])
        assert (root / "report.md").read_text() == "updated"

    @pytest.mark.anyio
    async def test_member_writes_in_shared(self, patch_groupspace_base: Path):
        shared = _shared_dir(patch_groupspace_base, "crew")
        (shared / "note.md").write_text("")
        await GroupSpaceManager.write_file("crew", "shared/note.md", "new content", ["crew"])
        assert (shared / "note.md").read_text() == "new content"

    @pytest.mark.anyio
    async def test_member_denied_in_root(self, patch_groupspace_base: Path):
        root = _group_dir(patch_groupspace_base, "crew")
        (root / "report.md").write_text("")
        with pytest.raises(AccessDeniedError, match="ACCESS_DENIED"):
            await GroupSpaceManager.write_file("crew", "report.md", "hacked", ["crew"])

    @pytest.mark.anyio
    async def test_admin_denied_in_shared(self, patch_groupspace_base: Path):
        shared = _shared_dir(patch_groupspace_base, "crew")
        (shared / "note.md").write_text("")
        with pytest.raises(AccessDeniedError, match="ACCESS_DENIED"):
            await GroupSpaceManager.write_file("crew", "shared/note.md", "x", ["admin"])


# ---------------------------------------------------------------------------
# create_file
# ---------------------------------------------------------------------------

class TestCreateFile:
    @pytest.mark.anyio
    async def test_creates_file_in_shared(self, patch_groupspace_base: Path):
        _shared_dir(patch_groupspace_base, "crew")
        rel = await GroupSpaceManager.create_file("crew", "shared", "new-doc.md", ["crew"])
        assert (patch_groupspace_base / "crew" / rel).exists()

    @pytest.mark.anyio
    async def test_auto_appends_md_extension(self, patch_groupspace_base: Path):
        _shared_dir(patch_groupspace_base, "crew")
        rel = await GroupSpaceManager.create_file("crew", "shared", "no-ext", ["crew"])
        assert rel.endswith(".md")

    @pytest.mark.anyio
    async def test_existing_file_raises(self, patch_groupspace_base: Path):
        shared = _shared_dir(patch_groupspace_base, "crew")
        (shared / "exists.md").write_text("")
        with pytest.raises(AccessDeniedError, match="FILE_ALREADY_EXISTS"):
            await GroupSpaceManager.create_file("crew", "shared", "exists.md", ["crew"])

    @pytest.mark.anyio
    async def test_member_denied_in_root(self, patch_groupspace_base: Path):
        _group_dir(patch_groupspace_base, "crew")
        with pytest.raises(AccessDeniedError, match="ACCESS_DENIED"):
            await GroupSpaceManager.create_file("crew", "", "doc.md", ["crew"])


# ---------------------------------------------------------------------------
# delete_file
# ---------------------------------------------------------------------------

class TestDeleteFile:
    @pytest.mark.anyio
    async def test_deletes_file(self, patch_groupspace_base: Path):
        shared = _shared_dir(patch_groupspace_base, "crew")
        target = shared / "old.md"
        target.write_text("bye")
        await GroupSpaceManager.delete_file("crew", "shared/old.md", ["crew"])
        assert not target.exists()

    @pytest.mark.anyio
    async def test_missing_file_raises(self, patch_groupspace_base: Path):
        _shared_dir(patch_groupspace_base, "crew")
        with pytest.raises(NotFoundError, match="FILE_NOT_FOUND"):
            await GroupSpaceManager.delete_file("crew", "shared/ghost.md", ["crew"])

    @pytest.mark.anyio
    async def test_member_denied_in_root(self, patch_groupspace_base: Path):
        root = _group_dir(patch_groupspace_base, "crew")
        (root / "admin-doc.md").write_text("")
        with pytest.raises(AccessDeniedError, match="ACCESS_DENIED"):
            await GroupSpaceManager.delete_file("crew", "admin-doc.md", ["crew"])
