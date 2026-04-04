"""Shared fixtures for SC-ARCHIVE unit tests."""
import pytest
from pathlib import Path


@pytest.fixture()
def tmp_workspace(tmp_path: Path) -> Path:
    """Isolated workspace_base directory for tests that resolve user paths."""
    base = tmp_path / "sc-archive"
    base.mkdir()
    return base


@pytest.fixture()
def patch_groupspace_base(tmp_workspace: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Patches logic.groupspace._workspace_base to return tmp_workspace."""
    monkeypatch.setattr("logic.groupspace._workspace_base", lambda: tmp_workspace)
    return tmp_workspace


@pytest.fixture()
def patch_blueprints_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Patches logic.blueprints.BLUEPRINTS_ROOT to an isolated tmp directory."""
    root = tmp_path / "blueprints"
    root.mkdir()
    monkeypatch.setattr("logic.blueprints.BLUEPRINTS_ROOT", root)
    return root


@pytest.fixture()
def patch_comms_base(tmp_workspace: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Patches logic.comms._workspace_base to return tmp_workspace."""
    monkeypatch.setattr("logic.comms._workspace_base", lambda: tmp_workspace)
    return tmp_workspace
