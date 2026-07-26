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

from logic.relations import VOCABULARY_BY_INVERSE, VOCABULARY_BY_NAME, Entity
from logic.relations_index import RelationIndex


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
