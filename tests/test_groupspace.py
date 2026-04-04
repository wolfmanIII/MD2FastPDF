"""Unit tests for logic/groupspace.py — GroupSpaceAccess, GroupSpaceManager.sanitize."""
import pytest
from pathlib import Path

from logic.groupspace import GroupSpaceAccess, GroupSpaceManager
from logic.exceptions import AccessDeniedError


# ---------------------------------------------------------------------------
# GroupSpaceAccess
# ---------------------------------------------------------------------------

class TestHasAccess:
    def test_member_of_group_has_access(self):
        assert GroupSpaceAccess.has_access("crew", ["crew", "engineering"]) is True

    def test_admin_has_access_to_any_group(self):
        assert GroupSpaceAccess.has_access("crew", ["admin"]) is True

    def test_non_member_non_admin_denied(self):
        assert GroupSpaceAccess.has_access("crew", ["engineering"]) is False

    def test_empty_groups_denied(self):
        assert GroupSpaceAccess.has_access("crew", []) is False


class TestCanWrite:
    def test_admin_can_write_in_root(self):
        assert GroupSpaceAccess.can_write("docs/report.md", ["admin"]) is True

    def test_admin_cannot_write_in_shared(self):
        assert GroupSpaceAccess.can_write("shared/note.md", ["admin"]) is False

    def test_admin_cannot_write_in_shared_subdir(self):
        assert GroupSpaceAccess.can_write("shared/subdir/file.md", ["admin"]) is False

    def test_member_can_write_in_shared(self):
        assert GroupSpaceAccess.can_write("shared/note.md", ["crew"]) is True

    def test_member_can_write_in_shared_subdir(self):
        assert GroupSpaceAccess.can_write("shared/logs/entry.md", ["crew"]) is True

    def test_member_cannot_write_in_root(self):
        assert GroupSpaceAccess.can_write("docs/report.md", ["crew"]) is False

    def test_member_cannot_write_at_root_level(self):
        assert GroupSpaceAccess.can_write("readme.md", ["crew"]) is False


class TestIsReadOnly:
    def test_is_complement_of_can_write_admin_in_root(self):
        assert GroupSpaceAccess.is_read_only("docs/file.md", ["admin"]) is False

    def test_is_complement_of_can_write_member_in_shared(self):
        assert GroupSpaceAccess.is_read_only("shared/file.md", ["crew"]) is False

    def test_member_root_is_read_only(self):
        assert GroupSpaceAccess.is_read_only("docs/file.md", ["crew"]) is True

    def test_admin_shared_is_read_only(self):
        assert GroupSpaceAccess.is_read_only("shared/file.md", ["admin"]) is True


# ---------------------------------------------------------------------------
# GroupSpaceManager.sanitize
# ---------------------------------------------------------------------------

class TestSanitize:
    def test_valid_path_inside_group(self, patch_groupspace_base: Path):
        patch_groupspace_base.joinpath("mygroup").mkdir(parents=True, exist_ok=True)
        result = GroupSpaceManager.sanitize("mygroup", "shared/file.md")
        assert result.is_absolute()
        assert "mygroup" in str(result)
        assert "shared" in str(result)

    def test_traversal_raises(self, patch_groupspace_base: Path):
        with pytest.raises(AccessDeniedError, match="ACCESS_DENIED"):
            GroupSpaceManager.sanitize("mygroup", "../../etc/passwd")

    def test_hidden_path_raises(self, patch_groupspace_base: Path):
        with pytest.raises(AccessDeniedError, match="ACCESS_DENIED"):
            GroupSpaceManager.sanitize("mygroup", ".hidden/file.md")

    def test_leading_slash_stripped(self, patch_groupspace_base: Path):
        patch_groupspace_base.joinpath("mygroup").mkdir(parents=True, exist_ok=True)
        result = GroupSpaceManager.sanitize("mygroup", "/shared/file.md")
        assert result == GroupSpaceManager.sanitize("mygroup", "shared/file.md")
