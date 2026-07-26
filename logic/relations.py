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
    name: str                              # frontmatter key
    inverse: str                            # inverse relation name, for reverse queries (RF-5)
    label: str                              # human-readable label for the forward direction, for the UI
    inverse_label: str                      # human-readable label for the reverse direction, for the UI
    domain: tuple[str, ...] | None = None   # allowed source entity types (RF-9). None = unconstrained.
    range: tuple[str, ...] | None = None    # allowed target entity types (RF-9). None = unconstrained.


VOCABULARY: tuple[RelationDef, ...] = (
    RelationDef("crew",          inverse="serves_on",       label="Equipaggio",   inverse_label="Equipaggio di",
                domain=("ship",), range=("npc",)),
    RelationDef("member_of",     inverse="has_member",       label="Membro di",    inverse_label="Membri",
                domain=("npc", "organization"), range=("organization",)),
    # No domain/range: too generic a spatial-containment relation to constrain
    # on today's observed types alone — real usage already spans location,
    # ai, ship and item, and a perfectly legitimate future case (an npc
    # located_in a location) isn't represented yet either.
    RelationDef("located_in",    inverse="contains",         label="Situato in",   inverse_label="Contiene"),
    RelationDef("hostile_to",    inverse="hostile_to",       label="Ostile a",     inverse_label="Ostile a",  # simmetrica
                domain=("npc",), range=("npc",)),
    RelationDef("owns",          inverse="owned_by",         label="Possiede",     inverse_label="Posseduto da",
                domain=("npc",), range=("ship", "location", "drone", "item")),
    # Added after analyzing real campaign content (Protocollo_SIGMA) — each
    # recurs across several NPC sheets, not a theoretical/speculative addition.
    RelationDef("owes_debt_to",  inverse="creditor_of",      label="Debitore di",  inverse_label="Creditore di",
                domain=("npc", "organization"), range=("npc", "organization")),
    RelationDef("reports_to",    inverse="has_subordinate",  label="Risponde a",   inverse_label="Subordinati",
                domain=("npc",), range=("npc",)),
    RelationDef("allied_with",   inverse="allied_with",      label="Alleato di",   inverse_label="Alleato di",  # simmetrica
                domain=("npc",), range=("npc",)),
    RelationDef("mentor_of",     inverse="student_of",       label="Mentore di",   inverse_label="Allievo di",
                domain=("npc",), range=("npc",)),
    # Grounded in a real 34-file scene archive (Protocollo_SIGMA/Scene/) —
    # domain="scene" only takes effect once those files adopt `type: scene`
    # in frontmatter (none do yet); until then it's simply never checked
    # (RF-9: a missing type is never a violation).
    RelationDef("npcs",          inverse="scenes",           label="NPC coinvolti", inverse_label="Scene",
                domain=("scene",), range=("npc",)),
)

VOCABULARY_BY_NAME: dict[str, RelationDef] = {r.name: r for r in VOCABULARY}
VOCABULARY_BY_INVERSE: dict[str, RelationDef] = {r.inverse: r for r in VOCABULARY}


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


@dataclass(frozen=True)
class ParseWarning:
    """A frontmatter relation value that couldn't be interpreted, surfaced
    structurally for diagnostics() in addition to the log line (RF-7)."""
    origin_path: Path
    relation: str
    message: str


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


def strip_frontmatter(content: str) -> str:
    """Returns content with its leading frontmatter block removed, if
    present — untouched otherwise. The block is metadata, not prose: it must
    never reach a Markdown-to-HTML/PDF renderer, which would otherwise show
    it as a literal `<hr>` plus garbled paragraphs/headings. Strips the
    delimited block syntactically even if the YAML inside doesn't parse —
    rendering shouldn't care whether the metadata itself is well-formed."""
    match = _FRONTMATTER_RE.match(content)
    return content[match.end():] if match else content


class RelationParser(Protocol):
    """Extracts typed relation edges from a file's already-parsed frontmatter."""
    def parse(self, path: Path, frontmatter: dict, warnings: list[ParseWarning] | None = None) -> list[Edge]: ...


class FrontmatterRelationParser:
    """Default RelationParser: reads VOCABULARY keys from a frontmatter dict."""

    def parse(self, path: Path, frontmatter: dict, warnings: list[ParseWarning] | None = None) -> list[Edge]:
        source = canonical_key(path.stem)
        edges: list[Edge] = []
        for relation_def in VOCABULARY:
            if relation_def.name not in frontmatter:
                continue
            values = self._normalize_values(frontmatter[relation_def.name], path, relation_def.name, warnings)
            for raw_target in values:
                edges.append(Edge(
                    source=source,
                    target=canonical_key(raw_target),
                    relation=relation_def.name,
                    origin_path=path,
                ))
        return edges

    @classmethod
    def _normalize_values(
        cls,
        raw_value: object,
        path: Path,
        relation_name: str,
        warnings: list[ParseWarning] | None,
    ) -> list[str]:
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
                    cls._warn(path, relation_name, "NON_STRING_LIST_ITEM", f"non-string list item: {item!r}", warnings)
            return values
        cls._warn(path, relation_name, "UNSUPPORTED_VALUE_TYPE", f"unsupported value type: {raw_value!r}", warnings)
        return []

    @staticmethod
    def _warn(path: Path, relation_name: str, tag: str, message: str, warnings: list[ParseWarning] | None) -> None:
        _log.warning("AEGIS_RELATIONS // %s // %s [%s]: %s", tag, path, relation_name, message)
        if warnings is not None:
            warnings.append(ParseWarning(path, relation_name, message))
