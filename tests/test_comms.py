"""Unit tests for logic/comms.py — FrontmatterParser, MessageRecord, CommsManager."""
import pytest

from logic.comms import FrontmatterParser, MessageRecord, CommsManager
from logic.exceptions import CommsError


# ---------------------------------------------------------------------------
# FrontmatterParser
# ---------------------------------------------------------------------------

class TestFrontmatterParserParse:
    def test_valid_returns_meta_and_body(self):
        raw = "---\nid: abc\nfrom: alice\n---\n\nHello body"
        result = FrontmatterParser.parse(raw)
        assert result is not None
        meta, body = result
        assert meta["id"] == "abc"
        assert meta["from"] == "alice"
        assert body == "Hello body"

    def test_bool_true_parsed(self):
        raw = "---\nread: true\n---\n"
        meta, _ = FrontmatterParser.parse(raw)
        assert meta["read"] is True

    def test_bool_false_parsed(self):
        raw = "---\nread: false\n---\n"
        meta, _ = FrontmatterParser.parse(raw)
        assert meta["read"] is False

    def test_missing_opening_delimiter_returns_none(self):
        assert FrontmatterParser.parse("id: abc\n---\nbody") is None

    def test_missing_closing_delimiter_returns_none(self):
        assert FrontmatterParser.parse("---\nid: abc\nbody") is None

    def test_empty_body(self):
        raw = "---\nid: x\n---\n"
        meta, body = FrontmatterParser.parse(raw)
        assert body == ""

    def test_body_preserves_content(self):
        raw = "---\nid: x\n---\n\nLine 1\nLine 2"
        _, body = FrontmatterParser.parse(raw)
        assert "Line 1" in body
        assert "Line 2" in body


class TestFrontmatterParserSerialize:
    def test_roundtrip(self):
        meta = {"id": "abc", "from": "alice", "read": False}
        body = "Test body"
        serialized = FrontmatterParser.serialize(meta, body)
        parsed = FrontmatterParser.parse(serialized)
        assert parsed is not None
        result_meta, result_body = parsed
        assert result_meta["id"] == "abc"
        assert result_meta["from"] == "alice"
        assert result_meta["read"] is False
        assert result_body == body

    def test_bool_serialized_as_lowercase(self):
        content = FrontmatterParser.serialize({"read": True}, "")
        assert "read: true" in content

    def test_starts_and_ends_with_delimiter(self):
        content = FrontmatterParser.serialize({"k": "v"}, "body")
        assert content.startswith("---")
        assert "---" in content[3:]


# ---------------------------------------------------------------------------
# MessageRecord
# ---------------------------------------------------------------------------

class TestMessageRecordRecipients:
    def test_single_recipient(self):
        rec = MessageRecord("id", "alice", "bob", "subj", "ts", False, "body", "f.md")
        assert rec.recipients == ["bob"]

    def test_multiple_recipients_stripped(self):
        rec = MessageRecord("id", "alice", "bob , carol , dave", "subj", "ts", False, "body", "f.md")
        assert rec.recipients == ["bob", "carol", "dave"]

    def test_all_not_expanded(self):
        rec = MessageRecord("id", "alice", "ALL", "subj", "ts", False, "body", "f.md")
        assert rec.recipients == ["ALL"]


# ---------------------------------------------------------------------------
# CommsManager — static/pure methods
# ---------------------------------------------------------------------------

class FakeUser:
    def __init__(self, username: str, groups: list[str]):
        self.username = username
        self.groups = groups


class TestAllowedRecipients:
    def _users(self):
        return [
            FakeUser("admin", ["admin"]),
            FakeUser("alice", ["crew"]),
            FakeUser("bob", ["crew"]),
            FakeUser("carol", ["engineering"]),
        ]

    def test_admin_sees_all_others(self):
        result = CommsManager.allowed_recipients("admin", ["admin"], self._users())
        assert set(result) == {"alice", "bob", "carol"}

    def test_member_sees_shared_group_and_admin(self):
        result = CommsManager.allowed_recipients("alice", ["crew"], self._users())
        assert "bob" in result       # same group
        assert "admin" in result     # admin always reachable
        assert "carol" not in result # different group, not admin

    def test_sender_excluded_from_results(self):
        result = CommsManager.allowed_recipients("alice", ["crew"], self._users())
        assert "alice" not in result

    def test_no_shared_group_no_admin_excluded(self):
        result = CommsManager.allowed_recipients("carol", ["engineering"], self._users())
        assert "admin" in result
        assert "alice" not in result
        assert "bob" not in result


class TestExpandRecipients:
    _manager = CommsManager()
    _allowed = ["alice", "bob", "carol"]

    def test_all_expands_to_allowed_excluding_sender(self):
        result = self._manager._expand_recipients("ALL", self._allowed, "alice")
        assert set(result) == {"bob", "carol"}

    def test_explicit_valid_recipients(self):
        result = self._manager._expand_recipients("bob,carol", self._allowed, "alice")
        assert result == ["bob", "carol"]

    def test_forbidden_recipient_raises(self):
        with pytest.raises(CommsError, match="RECIPIENT_NOT_ALLOWED"):
            self._manager._expand_recipients("mallory", self._allowed, "alice")

    def test_all_case_insensitive(self):
        result = self._manager._expand_recipients("all", self._allowed, "alice")
        assert "alice" not in result


class TestSlugify:
    def test_special_chars_become_underscores(self):
        assert CommsManager._slugify("Hello World!") == "hello_world"

    def test_max_32_chars(self):
        long = "a" * 40
        assert len(CommsManager._slugify(long)) <= 32

    def test_empty_returns_msg(self):
        assert CommsManager._slugify("") == "msg"
        assert CommsManager._slugify("!!!") == "msg"

    def test_lowercase(self):
        assert CommsManager._slugify("UPPER") == "upper"
