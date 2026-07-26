"""
AEGIS_QUERY_TRANSLATION: server-side validation of an OracleClient.translate_query()
result (RF-11 step 4, docs/ANALISI-relazioni-query-nl.md §4.3).

Never trusts the model's output: `relation` must match a known VOCABULARY
name/inverse, and `entity` must resolve via RelationIndex.find_by_display_name()
(RF-11 step 2). Either failing degrades to unresolved (None) — the same
non-blocking philosophy as DomainViolation/dangling elsewhere in this feature,
never an exception.
"""
from dataclasses import dataclass
from typing import Optional

from fastapi import Request

from logic.files import DirectoryLister
from logic.relations import VOCABULARY_BY_INVERSE, VOCABULARY_BY_NAME, Entity, canonical_key
from logic.relations_index import RelationIndex

_FALLBACK_LABEL = "Traduzione non riuscita — risultati di ricerca testuale"
_SESSION_KEY = "archive_query_pending"


@dataclass(frozen=True)
class ResolvedQuery:
    """A translated query that resolved cleanly to exactly one entity and a
    known relation — ready to execute via RelationIndex.related()."""
    entity_key: str
    relation: str


@dataclass(frozen=True)
class Ambiguous:
    """The named entity matched more than one candidate — the caller must
    ask the user to disambiguate (RF-11.3, issue #18) rather than guess."""
    candidates: list[Entity]


def resolve_translated_query(raw: dict, index: RelationIndex) -> ResolvedQuery | Ambiguous | None:
    """Validates a raw translate_query() result against the real vocabulary
    and index. Returns None (unresolved, triggers the RF-11.4 fallback) for
    any malformed input, an invented relation, or an entity with zero
    matches — never raises."""
    if not isinstance(raw, dict) or raw.get("intent") != "relation_query":
        return None

    relation_name = raw.get("relation")
    if not isinstance(relation_name, str):
        return None
    relation_def = VOCABULARY_BY_NAME.get(relation_name) or VOCABULARY_BY_INVERSE.get(relation_name)
    if relation_def is None:
        return None

    entity_query = raw.get("entity")
    if not isinstance(entity_query, str):
        return None
    candidates = index.find_by_display_name(entity_query)
    if not candidates:
        return None
    if len(candidates) > 1:
        return Ambiguous(candidates)

    return ResolvedQuery(entity_key=candidates[0].key, relation=relation_name)


async def fallback_text_search(message: str) -> dict:
    """RF-11.4 fallback (issue #17), invoked by the caller when
    resolve_translated_query() returns None. Reuses DirectoryLister.search()
    as-is — no new search engine — over the original user message. Results
    are explicitly labeled as informal text matches, never as a structured
    relation-query answer, so the caller never mistakes one for the other."""
    results = await DirectoryLister.search(message)
    return {"kind": "fallback_search", "label": _FALLBACK_LABEL, "results": results}


def store_pending_disambiguation(request: Request, relation: str, candidates: list[Entity]) -> None:
    """Stashes an Ambiguous result in the session (RF-11.3, issue #18) so the
    next turn can resolve it, without ever touching disk (RF-11.5: the
    archive terminal has no message persistence, unlike COMMS). Only plain
    JSON-safe values are stored — Starlette's SessionMiddleware is a signed
    cookie, not a store for arbitrary Python objects."""
    request.session[_SESSION_KEY] = {
        "relation": relation,
        "candidates": [{"key": e.key, "display_name": e.display_name} for e in candidates],
    }


def pop_pending_disambiguation(request: Request) -> Optional[dict]:
    """Retrieves and clears any pending disambiguation for this session —
    always consumed on the next attempt, whether or not it resolves, so a
    stale disambiguation never lingers across unrelated later questions."""
    return request.session.pop(_SESSION_KEY, None)


def resolve_disambiguation_choice(pending: dict, choice: str) -> Optional[ResolvedQuery]:
    """Matches the user's follow-up reply against the stashed candidates
    (same canonical_key normalization used everywhere else for entity
    references). None if the reply doesn't match any candidate — the caller
    treats that the same as any other unresolved query (RF-11.4 fallback)."""
    choice_key = canonical_key(choice)
    for candidate in pending.get("candidates", []):
        if candidate["key"] == choice_key:
            return ResolvedQuery(entity_key=candidate["key"], relation=pending["relation"])
    return None
