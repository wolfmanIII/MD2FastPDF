"""
AEGIS_RELATIONS_INDEX: two-pass, in-memory construction of the typed relation
graph declared in Markdown frontmatter. See logic/relations.py for the
vocabulary and per-file parsing, docs/ANALISI-relazioni-tipizzate.md for the
full design (§5.3-§5.5).

Pass 1 walks the active archive root and populates `entities` from every
Markdown file's frontmatter. Pass 2 resolves the (unresolved-target) Edge
objects produced by RelationParser against the now-complete entity set —
necessary because a file can reference an entity not yet read in pass 1.
Unresolved references are recorded in `dangling`, never raised (RF-7).

The index is entirely derived and rebuildable — never the source of truth
(§3 non-goals: no database, no persisted state). Query methods (related,
relations_of, diagnostics) and incremental reindexing are a later layer, not
this module's concern.
"""
import logging
from dataclasses import dataclass, field
from pathlib import Path

import anyio

from logic.files import DirectoryLister, PathSanitizer, read_text_at
from logic.relations import (
    Edge,
    Entity,
    FrontmatterRelationParser,
    RelationParser,
    canonical_key,
    extract_frontmatter,
)

_log = logging.getLogger(__name__)


@dataclass(frozen=True)
class DanglingReference:
    """A relation value that did not resolve to a known entity key."""
    origin_path: Path
    relation: str
    reference: str  # canonical key that failed to resolve


@dataclass(frozen=True)
class KeyCollision:
    """Two files normalize to the same entity key. The first one seen wins;
    this records the one that was ignored (§5.4 — resolved properly by RF-10,
    not before)."""
    key: str
    kept_path: Path
    ignored_path: Path


@dataclass
class RelationIndex:
    """In-memory lookup structures for the typed relation graph.

    out_edges/in_edges only ever contain edges whose target resolved to a
    known entity. by_path tracks every edge originating from a file —
    resolved or dangling — so a future incremental reindex can find and drop
    them without a full rescan. Mutation happens exclusively through the
    methods below — RelationIndexBuilder is the only external caller, but the
    API is public because building the index is inherently a multi-step
    process the builder drives from outside this class.
    """
    entities: dict[str, Entity] = field(default_factory=dict)
    out_edges: dict[tuple[str, str], list[str]] = field(default_factory=dict)
    in_edges: dict[tuple[str, str], list[str]] = field(default_factory=dict)
    by_path: dict[Path, list[Edge]] = field(default_factory=dict)
    dangling: list[DanglingReference] = field(default_factory=list)
    key_collisions: list[KeyCollision] = field(default_factory=list)

    def register_entity(self, entity: Entity) -> None:
        """Adds entity, or records a KeyCollision if its key is already taken
        by a different file — the first one seen wins (§5.4)."""
        existing = self.entities.get(entity.key)
        if existing is not None and existing.path != entity.path:
            self.key_collisions.append(KeyCollision(entity.key, existing.path, entity.path))
            return
        self.entities[entity.key] = entity

    def record_resolved(self, edge: Edge) -> None:
        self.out_edges.setdefault((edge.source, edge.relation), []).append(edge.target)
        self.in_edges.setdefault((edge.target, edge.relation), []).append(edge.source)
        self._track_by_path(edge)

    def record_dangling(self, edge: Edge) -> None:
        self.dangling.append(DanglingReference(edge.origin_path, edge.relation, edge.target))
        self._track_by_path(edge)

    def _track_by_path(self, edge: Edge) -> None:
        self.by_path.setdefault(edge.origin_path, []).append(edge)


class RelationIndexBuilder:
    """Builds a RelationIndex via a two-pass scan of the active archive root."""

    def __init__(self, parser: RelationParser | None = None) -> None:
        self._parser: RelationParser = parser or FrontmatterRelationParser()

    async def build(self) -> RelationIndex:
        root = PathSanitizer.get_root().resolve()
        md_files = await anyio.to_thread.run_sync(DirectoryLister.scan_markdown_files, root)

        index = RelationIndex()
        parsed_edges: list[Edge] = []

        # Pass 1: read every file once, populate entities.
        for entry in md_files:
            file_path = entry["path"]
            rel_path = file_path.relative_to(root)
            try:
                content = await read_text_at(file_path)
            except (OSError, UnicodeDecodeError) as e:
                _log.warning("AEGIS_RELATIONS // UNREADABLE_FILE // %s — %s", rel_path, e)
                continue

            frontmatter = extract_frontmatter(content)
            entity_type = frontmatter.get("type") if frontmatter else None
            if not isinstance(entity_type, str):
                entity_type = None

            stem = rel_path.stem
            entity = Entity(
                key=canonical_key(stem),
                display_name=stem,
                path=rel_path,
                entity_type=entity_type,
                mtime=entry["mtime"],
            )
            index.register_entity(entity)

            if frontmatter is not None:
                parsed_edges.extend(self._parser.parse(rel_path, frontmatter))

        # Pass 2: resolve targets now that `entities` is complete.
        for edge in parsed_edges:
            if edge.target in index.entities:
                index.record_resolved(edge)
            else:
                index.record_dangling(edge)

        return index
