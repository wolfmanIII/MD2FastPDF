"""
AEGIS_RELATIONS_PROTOCOL: typed entity relations declared in Markdown frontmatter.

Additive to the existing wikilink-free Markdown link graph (logic/graph.py):
frontmatter relations are structured data for queries, body links remain the
prose-level "mentions" a human reads. See docs/ANALISI-relazioni-tipizzate.md.

RelationDef / VOCABULARY: single declarative source of the allowed relation
vocabulary (§5.2). A frontmatter key not present here is ignored, never an
error — existing frontmatter usage must keep working unchanged.

Entity / Edge: value objects for the in-memory index (§5.3). Building the
index itself (scanning the archive, resolving targets, tracking dangling
references) is out of scope for this module — see the index builder.

extract_frontmatter: minimal YAML frontmatter reader. Distinct from
logic.comms.FrontmatterParser, which is scalar-only (str/bool, no lists) and
therefore unusable here: relation values are lists of entity references.

RelationParser: Protocol + FrontmatterRelationParser, the concrete
implementation producing unresolved Edge objects from a single file's already
-extracted frontmatter dict (target resolution against the full entity set
happens in a later pass, once all files are known).
"""
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import yaml

_log = logging.getLogger(__name__)


@dataclass(frozen=True)
class RelationDef:
    """Declares one relation type recognized in frontmatter."""
    name: str                  # frontmatter key
    inverse: str                # inverse relation name, for reverse queries (RF-5)
    label: str                  # human-readable label, for the UI
    domain: str | None = None   # allowed source entity type (RF-9, unused in Fase 1)
    range: str | None = None    # allowed target entity type (RF-9, unused in Fase 1)


VOCABULARY: tuple[RelationDef, ...] = (
    RelationDef("crew",        inverse="serves_on",  label="Equipaggio"),
    RelationDef("member_of",   inverse="has_member",  label="Membro di"),
    RelationDef("located_in",  inverse="contains",    label="Situato in"),
    RelationDef("hostile_to",  inverse="hostile_to",  label="Ostile a"),
    RelationDef("owns",        inverse="owned_by",    label="Possiede"),
)

VOCABULARY_BY_NAME: dict[str, RelationDef] = {r.name: r for r in VOCABULARY}


@dataclass(frozen=True)
class Entity:
    """A single addressable document in the relation index."""
    key: str                    # canonical lookup key (see canonical_key)
    display_name: str           # original file stem, for the UI
    path: Path
    entity_type: str | None     # frontmatter `type:`, if present
    mtime: float


@dataclass(frozen=True)
class Edge:
    """A single directed, typed relation between two entity keys."""
    source: str                 # Entity.key
    target: str                 # Entity.key — not guaranteed to exist yet
    relation: str                # RelationDef.name
    origin_path: Path            # file that declared this relation


_WIKILINK_RE = re.compile(r"^\[\[(.+)\]\]$")
_WHITESPACE_RE = re.compile(r"\s+")


def strip_wikilink(raw: str) -> str:
    """Removes an optional [[ ]] wrapping from a relation value."""
    stripped = raw.strip()
    match = _WIKILINK_RE.match(stripped)
    return match.group(1).strip() if match else stripped


def canonical_key(raw: str) -> str:
    """Normalizes an entity reference to its canonical index lookup key."""
    unwrapped = strip_wikilink(raw)
    collapsed = _WHITESPACE_RE.sub(" ", unwrapped).strip()
    return collapsed.casefold()


_FRONTMATTER_RE = re.compile(r"\A---[ \t]*\r?\n(.*?\r?\n)---[ \t]*\r?\n?", re.DOTALL)


def extract_frontmatter(content: str) -> dict | None:
    """Parses the leading YAML frontmatter block of a file's content.

    Returns None if there is no frontmatter, the YAML is malformed, or the
    parsed value is not a mapping — never raises. Callers must treat None as
    "no relations declared", not as an error condition (RF-3).
    """
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return None
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


class RelationParser(Protocol):
    """Extracts typed relation edges from a file's already-parsed frontmatter."""
    def parse(self, path: Path, frontmatter: dict) -> list[Edge]: ...


class FrontmatterRelationParser:
    """Default RelationParser: reads VOCABULARY keys from a frontmatter dict."""

    def parse(self, path: Path, frontmatter: dict) -> list[Edge]:
        source = canonical_key(path.stem)
        edges: list[Edge] = []
        for relation_def in VOCABULARY:
            if relation_def.name not in frontmatter:
                continue
            for raw_target in self._normalize_values(frontmatter[relation_def.name], path, relation_def.name):
                edges.append(Edge(
                    source=source,
                    target=canonical_key(raw_target),
                    relation=relation_def.name,
                    origin_path=path,
                ))
        return edges

    @staticmethod
    def _normalize_values(raw_value: object, path: Path, relation_name: str) -> list[str]:
        """A scalar string becomes a one-element list; a list is used as-is,
        skipping non-string items; any other type is ignored with a warning.
        """
        if isinstance(raw_value, str):
            return [raw_value]
        if isinstance(raw_value, list):
            values: list[str] = []
            for item in raw_value:
                if isinstance(item, str):
                    values.append(item)
                else:
                    _log.warning(
                        "AEGIS_RELATIONS // NON_STRING_LIST_ITEM // %s [%s]: %r",
                        path, relation_name, item,
                    )
            return values
        _log.warning(
            "AEGIS_RELATIONS // UNSUPPORTED_VALUE_TYPE // %s [%s]: %r",
            path, relation_name, raw_value,
        )
        return []
