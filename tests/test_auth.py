"""Unit tests for logic/auth.py — UserRecord, UserStore._build_record, AuthService.bootstrap_admin."""
import pytest

from logic.auth import AuthService, UserRecord, UserStore


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


class _FakeSyncStore:
    def __init__(self, empty: bool):
        self._empty = empty
        self.saved: UserRecord | None = None

    def is_empty(self) -> bool:
        return self._empty

    def save_user_sync(self, record: UserRecord) -> None:
        self.saved = record


class _FakeSyncGroupStore:
    def __init__(self):
        self.ensured = False

    def ensure_admin_group_sync(self) -> None:
        self.ensured = True


class TestBootstrapAdmin:
    """No fixed weak default: AEGIS_ADMIN_PASSWORD if set, otherwise a random password."""

    def _make_service(self, tmp_path, monkeypatch, empty: bool = True):
        sync_store = _FakeSyncStore(empty)
        sync_group_store = _FakeSyncGroupStore()
        service = AuthService(store=None, sync_store=sync_store, sync_group_store=sync_group_store)
        monkeypatch.setattr(AuthService, "_default_root", lambda self, username: tmp_path / username)
        monkeypatch.setattr("logic.auth._ADMIN_PASSWORD_FILE", tmp_path / "admin_password.txt")
        return service, sync_store, sync_group_store

    def _set_env(self, monkeypatch, env_value: str | None) -> None:
        if env_value is None:
            monkeypatch.delenv("AEGIS_ADMIN_PASSWORD", raising=False)
        else:
            monkeypatch.setenv("AEGIS_ADMIN_PASSWORD", env_value)

    @pytest.mark.parametrize("env_value", ["custom-secret", None, ""])
    def test_password_resolution(self, tmp_path, monkeypatch, env_value):
        self._set_env(monkeypatch, env_value)
        service, sync_store, _ = self._make_service(tmp_path, monkeypatch)
        service.bootstrap_admin()
        if env_value:
            assert service._verify(env_value, sync_store.saved.password_hash)
        else:
            assert not service._verify("admin", sync_store.saved.password_hash)

    @pytest.mark.parametrize(
        "env_value,warning_expected", [(None, True), ("", True), ("custom-secret", False)]
    )
    def test_logs_warning_only_when_generated(self, tmp_path, monkeypatch, caplog, env_value, warning_expected):
        self._set_env(monkeypatch, env_value)
        service, _, _ = self._make_service(tmp_path, monkeypatch)
        with caplog.at_level("WARNING", logger="aegis.auth"):
            service.bootstrap_admin()
        assert ("AEGIS_ADMIN_PASSWORD non impostata" in caplog.text) == warning_expected

    def test_skips_creation_when_store_not_empty(self, tmp_path, monkeypatch):
        service, sync_store, group_store = self._make_service(tmp_path, monkeypatch, empty=False)
        service.bootstrap_admin()
        assert sync_store.saved is None
        assert group_store.ensured is True

    def test_persists_generated_password_to_file(self, tmp_path, monkeypatch):
        monkeypatch.delenv("AEGIS_ADMIN_PASSWORD", raising=False)
        service, sync_store, _ = self._make_service(tmp_path, monkeypatch)
        service.bootstrap_admin()
        password_file = tmp_path / "admin_password.txt"
        assert password_file.exists()
        saved_password = password_file.read_text().strip()
        assert saved_password
        assert service._verify(saved_password, sync_store.saved.password_hash)

    def test_does_not_persist_file_when_password_configured(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AEGIS_ADMIN_PASSWORD", "custom-secret")
        service, _, _ = self._make_service(tmp_path, monkeypatch)
        service.bootstrap_admin()
        assert not (tmp_path / "admin_password.txt").exists()
