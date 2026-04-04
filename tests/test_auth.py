"""Unit tests for logic/auth.py — UserRecord, UserStore._build_record."""
from logic.auth import UserRecord, UserStore


class TestUserRecord:
    def _make(self, groups=None) -> UserRecord:
        return UserRecord("alice", "hash123", "/home/alice", groups or [])

    def test_to_dict_has_correct_keys(self):
        rec = self._make(["crew"])
        d = rec.to_dict()
        assert set(d.keys()) == {"password_hash", "root", "groups"}

    def test_to_dict_values(self):
        rec = self._make(["crew", "admin"])
        d = rec.to_dict()
        assert d["password_hash"] == "hash123"
        assert d["root"] == "/home/alice"
        assert d["groups"] == ["crew", "admin"]

    def test_to_dict_empty_groups(self):
        rec = self._make([])
        assert rec.to_dict()["groups"] == []


class TestUserStoreBuildRecord:
    _store = UserStore()

    def test_builds_correct_record(self):
        entry = {"password_hash": "h", "root": "/home/bob", "groups": ["crew"]}
        rec = self._store._build_record("bob", entry)
        assert rec.username == "bob"
        assert rec.password_hash == "h"
        assert rec.root == "/home/bob"
        assert rec.groups == ["crew"]

    def test_missing_groups_defaults_to_empty_list(self):
        # Backwards compatibility: old users.json entries have no 'groups' key
        entry = {"password_hash": "h", "root": "/home/bob"}
        rec = self._store._build_record("bob", entry)
        assert rec.groups == []

    def test_empty_groups_preserved(self):
        entry = {"password_hash": "h", "root": "/home/bob", "groups": []}
        rec = self._store._build_record("bob", entry)
        assert rec.groups == []
