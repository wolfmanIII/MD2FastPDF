"""Unit tests for logic/blueprints.py — BlueprintManager pure methods."""
import pytest
from pathlib import Path

from logic.blueprints import BlueprintManager
from logic.exceptions import AccessDeniedError


# ---------------------------------------------------------------------------
# BlueprintManager._sanitize
# ---------------------------------------------------------------------------

class TestSanitize:
    def test_valid_path_returned(self, patch_blueprints_root: Path):
        result = BlueprintManager._sanitize("narrative/session-log.md")
        assert result.is_absolute()
        assert str(patch_blueprints_root) in str(result)

    def test_traversal_raises(self, patch_blueprints_root: Path):
        with pytest.raises(AccessDeniedError, match="ACCESS_DENIED"):
            BlueprintManager._sanitize("../../etc/passwd")

    def test_leading_slash_stripped(self, patch_blueprints_root: Path):
        r1 = BlueprintManager._sanitize("narrative/file.md")
        r2 = BlueprintManager._sanitize("/narrative/file.md")
        assert r1 == r2


# ---------------------------------------------------------------------------
# BlueprintManager._display_name
# ---------------------------------------------------------------------------

class TestDisplayName:
    def test_hyphens_replaced_with_spaces(self):
        assert BlueprintManager._display_name("session-log.md") == "Session Log"

    def test_underscores_replaced_with_spaces(self):
        assert BlueprintManager._display_name("npc_profile.md") == "Npc Profile"

    def test_title_case_applied(self):
        assert BlueprintManager._display_name("planet-description.md") == "Planet Description"

    def test_extension_stripped(self):
        name = BlueprintManager._display_name("ship-description.md")
        assert ".md" not in name


# ---------------------------------------------------------------------------
# BlueprintManager.group_by_category
# ---------------------------------------------------------------------------

class TestGroupByCategory:
    def test_groups_correctly(self):
        bps = [
            {"path": "narrative/a.md", "name": "A", "category": "narrative"},
            {"path": "narrative/b.md", "name": "B", "category": "narrative"},
            {"path": "tech/c.md", "name": "C", "category": "tech"},
        ]
        result = BlueprintManager.group_by_category(bps)
        assert set(result.keys()) == {"narrative", "tech"}
        assert len(result["narrative"]) == 2
        assert len(result["tech"]) == 1

    def test_empty_list_returns_empty_dict(self):
        assert BlueprintManager.group_by_category([]) == {}

    def test_single_category(self):
        bps = [{"path": "a/x.md", "name": "X", "category": "a"}]
        result = BlueprintManager.group_by_category(bps)
        assert list(result.keys()) == ["a"]
        assert result["a"][0]["name"] == "X"
