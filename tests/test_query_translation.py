"""Tests for logic/query_translation.py — resolve_translated_query() (RF-11 step 4).

Pure/no Ollama: fixed JSON dicts against a real RelationIndex built from a
small fixture vault.
"""
from pathlib import Path

import pytest

from logic.query_translation import Ambiguous, ResolvedQuery, fallback_text_search, resolve_translated_query
from logic.relations_index import RelationIndexBuilder


def _write(root: Path, rel_path: str, content: str) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _seed_vault(root: Path) -> None:
    _write(root, "ships/Beowulf.md", "---\ntype: ship\ncrew: [Kira Venn]\n---\n\nMercantile.\n")
    _write(root, "npcs/Kira Venn.md", "---\ntype: npc\n---\n\nPilota.\n")
    _write(root, "Progetto-Aran.md", "---\ntype: organization\n---\n\nProgetto.\n")
    _write(root, "Aran-Echo.md", "---\ntype: ai\n---\n\nEco.\n")


@pytest.mark.anyio
async def test_valid_relation_and_unique_entity_resolves(archive_root: Path):
    _seed_vault(archive_root)
    index = await RelationIndexBuilder().build()
    result = resolve_translated_query({"intent": "relation_query", "entity": "Beowulf", "relation": "crew"}, index)
    assert result == ResolvedQuery(entity_key="beowulf", relation="crew")


@pytest.mark.anyio
async def test_relation_by_inverse_name_resolves(archive_root: Path):
    _seed_vault(archive_root)
    index = await RelationIndexBuilder().build()
    result = resolve_translated_query({"intent": "relation_query", "entity": "Kira", "relation": "serves_on"}, index)
    assert result == ResolvedQuery(entity_key="kira venn", relation="serves_on")


@pytest.mark.anyio
async def test_invented_relation_is_unresolved(archive_root: Path):
    _seed_vault(archive_root)
    index = await RelationIndexBuilder().build()
    result = resolve_translated_query({"intent": "relation_query", "entity": "Beowulf", "relation": "not_a_real_relation"}, index)
    assert result is None


@pytest.mark.anyio
async def test_entity_with_no_matches_is_unresolved(archive_root: Path):
    _seed_vault(archive_root)
    index = await RelationIndexBuilder().build()
    result = resolve_translated_query({"intent": "relation_query", "entity": "Nobody", "relation": "crew"}, index)
    assert result is None


@pytest.mark.anyio
async def test_ambiguous_entity_returns_all_candidates(archive_root: Path):
    _seed_vault(archive_root)
    index = await RelationIndexBuilder().build()
    result = resolve_translated_query({"intent": "relation_query", "entity": "Aran", "relation": "crew"}, index)
    assert isinstance(result, Ambiguous)
    assert {e.display_name for e in result.candidates} == {"Progetto-Aran", "Aran-Echo"}


@pytest.mark.anyio
async def test_explicit_unresolved_intent_returns_none(archive_root: Path):
    _seed_vault(archive_root)
    index = await RelationIndexBuilder().build()
    assert resolve_translated_query({"intent": "unresolved"}, index) is None


@pytest.mark.anyio
async def test_missing_intent_returns_none(archive_root: Path):
    _seed_vault(archive_root)
    index = await RelationIndexBuilder().build()
    assert resolve_translated_query({"entity": "Beowulf", "relation": "crew"}, index) is None


@pytest.mark.anyio
async def test_non_dict_raw_returns_none(archive_root: Path):
    _seed_vault(archive_root)
    index = await RelationIndexBuilder().build()
    assert resolve_translated_query([], index) is None


@pytest.mark.anyio
async def test_non_string_relation_returns_none(archive_root: Path):
    _seed_vault(archive_root)
    index = await RelationIndexBuilder().build()
    result = resolve_translated_query({"intent": "relation_query", "entity": "Beowulf", "relation": 42}, index)
    assert result is None


@pytest.mark.anyio
async def test_non_string_entity_returns_none(archive_root: Path):
    _seed_vault(archive_root)
    index = await RelationIndexBuilder().build()
    result = resolve_translated_query({"intent": "relation_query", "entity": None, "relation": "crew"}, index)
    assert result is None


# ---------------------------------------------------------------------------
# fallback_text_search() — RF-11 step 5, issue #17
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_fallback_search_finds_matching_filename(archive_root: Path):
    _seed_vault(archive_root)
    result = await fallback_text_search("beowulf")
    assert result["kind"] == "fallback_search"
    assert result["label"] == "Traduzione non riuscita — risultati di ricerca testuale"
    assert [r["name"] for r in result["results"]] == ["Beowulf.md"]


@pytest.mark.anyio
async def test_fallback_search_no_match_returns_empty_results(archive_root: Path):
    _seed_vault(archive_root)
    result = await fallback_text_search("nessuna corrispondenza possibile xyz")
    assert result["results"] == []
