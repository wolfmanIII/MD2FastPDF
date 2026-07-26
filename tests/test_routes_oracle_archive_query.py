"""Integration tests for routes/oracle.py::oracle_archive_query (RF-11 step 7,
issue #19). Calls the route function directly (no TestClient/HTTP layer
needed — same pattern as tests/test_routes_graph_relations.py) against a real
RelationIndex built from a fixture vault, with OracleClient.translate_query
mocked (the network boundary already covered by tests/test_oracle.py).
"""
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from logic.oracle import oracle
from logic.relations_service import RelationGraphService
from routes.oracle import ArchiveQueryRequest, oracle_archive_query


def _write(root: Path, rel_path: str, content: str) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class _FakeRequest:
    """Duck-typed stand-in for fastapi.Request — only .session is touched."""
    def __init__(self):
        self.session: dict = {}


@pytest.fixture(autouse=True)
def _clear_cache():
    RelationGraphService.invalidate_all()
    yield
    RelationGraphService.invalidate_all()


@pytest.mark.anyio
async def test_resolved_query_returns_answer(archive_root: Path, monkeypatch: pytest.MonkeyPatch):
    _write(archive_root, "ships/Beowulf.md", "---\ntype: ship\ncrew: [Kira Venn]\n---\n\nMercantile.\n")
    _write(archive_root, "npcs/Kira Venn.md", "---\ntype: npc\n---\n\nPilota.\n")
    monkeypatch.setattr(oracle, "translate_query", AsyncMock(return_value={
        "intent": "relation_query", "entity": "Beowulf", "relation": "crew"
    }))

    response = await oracle_archive_query(ArchiveQueryRequest(message="equipaggio della Beowulf"), _FakeRequest())
    body = response.body.decode()
    assert '"kind":"answer"' in body.replace(" ", "")
    assert "Kira Venn" in body


@pytest.mark.anyio
async def test_ambiguous_entity_returns_disambiguate_and_stashes_session(archive_root: Path, monkeypatch: pytest.MonkeyPatch):
    _write(archive_root, "Progetto-Aran.md", "---\ntype: organization\n---\n\nProgetto.\n")
    _write(archive_root, "Aran-Echo.md", "---\ntype: ai\n---\n\nEco.\n")
    monkeypatch.setattr(oracle, "translate_query", AsyncMock(return_value={
        "intent": "relation_query", "entity": "Aran", "relation": "crew"
    }))

    request = _FakeRequest()
    response = await oracle_archive_query(ArchiveQueryRequest(message="qualcosa su Aran"), request)
    body = response.body.decode()
    assert '"kind":"disambiguate"' in body.replace(" ", "")
    assert "Progetto-Aran" in body and "Aran-Echo" in body
    assert "archive_query_pending" in request.session


@pytest.mark.anyio
async def test_disambiguation_followup_resolves_without_retranslating(archive_root: Path, monkeypatch: pytest.MonkeyPatch):
    _write(archive_root, "ships/Beowulf.md", "---\ntype: ship\ncrew: [Progetto-Aran]\n---\n\nMercantile.\n")
    _write(archive_root, "Progetto-Aran.md", "---\ntype: organization\n---\n\nProgetto.\n")
    _write(archive_root, "Aran-Echo.md", "---\ntype: ai\n---\n\nEco.\n")

    mock_translate = AsyncMock(return_value={
        "intent": "relation_query", "entity": "Aran", "relation": "serves_on"
    })
    monkeypatch.setattr(oracle, "translate_query", mock_translate)

    request = _FakeRequest()
    await oracle_archive_query(ArchiveQueryRequest(message="chi comanda Aran"), request)
    assert mock_translate.call_count == 1

    response = await oracle_archive_query(ArchiveQueryRequest(message="Progetto-Aran"), request)
    body = response.body.decode()
    assert '"kind":"answer"' in body.replace(" ", "")
    assert "Beowulf" in body
    # The follow-up matched a stashed candidate — no second translation call.
    assert mock_translate.call_count == 1
    assert "archive_query_pending" not in request.session


@pytest.mark.anyio
async def test_unresolved_translation_falls_back_to_text_search(archive_root: Path, monkeypatch: pytest.MonkeyPatch):
    _write(archive_root, "Manifesto-Segreto.md", "---\ntype: item\n---\n\nUn documento.\n")
    monkeypatch.setattr(oracle, "translate_query", AsyncMock(return_value={"intent": "unresolved"}))

    response = await oracle_archive_query(ArchiveQueryRequest(message="manifesto"), _FakeRequest())
    body = response.body.decode()
    assert '"kind":"fallback_search"' in body.replace(" ", "")
    assert "Manifesto-Segreto.md" in body
