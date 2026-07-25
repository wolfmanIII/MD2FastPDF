"""
AEGIS_RELATIONS_INDEX: two-pass, in-memory construction of the typed relation
graph declared in Markdown frontmatter, plus queries and incremental reindex.
See logic/relations.py for the vocabulary and per-file parsing,
docs/ANALISI-relazioni-tipizzate.md for the full design (§5.3-§5.7).

Pass 1 walks the active archive root and populates `entities` from every
Markdown file's frontmatter. Pass 2 resolves the (unresolved-target) Edge
objects produced by RelationParser against the now-complete entity set —
necessary because a file can reference an entity not yet read in pass 1.
Unresolved references are recorded in `dangling`, never raised (RF-7).

related()/relations_of() are RelationIndex's read path; register_entity()/
record_resolved()/record_dangling() are its write path, driven by
RelationIndexBuilder during build() (full scan) or reindex_file() (a single
file, no rescan — RF-6). The index is entirely derived and rebuildable —
never the source of truth (§3 non-goals: no database, no persisted state).

Known limitation: reindex_file() only re-resolves edges *declared by* the
reindexed file. A dangling reference from another file that pointed at this
file before it existed is not retroactively resolved just because this file
now exists — it stays dangling until the *referencing* file is itself
reindexed (or the whole index is rebuilt via build()). Not exercised by any
current caller; documented here so it isn't mistaken for a bug later.
"""
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import anyio

from logic.exceptions import AegisError
from logic.files import DirectoryLister, PathSanitizer, read_text_at
from logic.relations import (
    VOCABULARY,
    VOCABULARY_BY_INVERSE,
    VOCABULARY_BY_NAME,
    Edge,
    Entity,
    FrontmatterRelationParser,
    ParseWarning,
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


@dataclass(frozen=True)
class Diagnostics:
    """Snapshot of everything that didn't cleanly resolve (§5.7, RF-7)."""
    dangling: list[DanglingReference]
    key_collisions: list[KeyCollision]
    parse_warnings: list[ParseWarning]


class RelationGraphIndex(Protocol):
    """Read-only query surface over a built relation index (§5.7)."""
    def related(self, entity: str, relation: str) -> list[Entity]: ...
    def relations_of(self, entity: str) -> dict[str, list[Entity]]: ...
    def diagnostics(self) -> Diagnostics: ...


@dataclass
class RelationIndex:
    """In-memory lookup structures for the typed relation graph, plus the
    query methods over them (RelationGraphIndex).

    out_edges/in_edges only ever contain edges whose target resolved to a
    known entity. by_path tracks every edge originating from a file —
    resolved or dangling — so reindex_file can find and drop them without a
    full rescan. Mutation happens exclusively through the methods below —
    RelationIndexBuilder is the only external caller, but the API is public
    because building/reindexing is inherently driven from outside this class.
    """
    entities: dict[str, Entity] = field(default_factory=dict)
    out_edges: dict[tuple[str, str], list[str]] = field(default_factory=dict)
    in_edges: dict[tuple[str, str], list[str]] = field(default_factory=dict)
    by_path: dict[Path, list[Edge]] = field(default_factory=dict)
    dangling: list[DanglingReference] = field(default_factory=list)
    key_collisions: list[KeyCollision] = field(default_factory=list)
    parse_warnings: list[ParseWarning] = field(default_factory=list)

    # -- write path ----------------------------------------------------

    def register_entity(self, entity: Entity) -> None:
        """Adds entity, or records a KeyCollision if its key is already taken
        by a different file — the first one seen wins (§5.4). Registering the
        same path again (a re-save) is an update, not a collision."""
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

    def record_parse_warning(self, warning: ParseWarning) -> None:
        self.parse_warnings.append(warning)

    def drop_path(self, path: Path) -> None:
        """Removes every edge, dangling reference, and parse warning that
        originated from `path` — the first step of reindexing a single file
        (RF-6), whether it was edited or deleted. Does not touch `entities`:
        callers decide separately whether the entity at `path` survives."""
        for edge in self.by_path.pop(path, []):
            self._discard_resolved(edge)
        self.dangling = [d for d in self.dangling if d.origin_path != path]
        self.parse_warnings = [w for w in self.parse_warnings if w.origin_path != path]

    def remove_entity_at_path(self, path: Path) -> None:
        """Drops the entity registered at `path` (if any) and demotes every
        edge that targeted it to dangling — used when a file is deleted
        (RF-6). Call drop_path(path) first to clear its own outgoing edges."""
        removed_key = next((key for key, entity in self.entities.items() if entity.path == path), None)
        if removed_key is None:
            return
        del self.entities[removed_key]

        for relation_def in VOCABULARY:
            source_keys = self.in_edges.pop((removed_key, relation_def.name), [])
            for source_key in source_keys:
                self._discard_from_dict(self.out_edges, (source_key, relation_def.name), removed_key)
                source_entity = self.entities.get(source_key)
                origin_path = source_entity.path if source_entity else path
                self.dangling.append(DanglingReference(origin_path, relation_def.name, removed_key))

    def _track_by_path(self, edge: Edge) -> None:
        self.by_path.setdefault(edge.origin_path, []).append(edge)

    def _discard_resolved(self, edge: Edge) -> None:
        """Removes edge from out_edges/in_edges if it's there; a no-op for a
        dangling edge, which was never added to either."""
        self._discard_from_dict(self.out_edges, (edge.source, edge.relation), edge.target)
        self._discard_from_dict(self.in_edges, (edge.target, edge.relation), edge.source)

    @staticmethod
    def _discard_from_dict(edges: dict[tuple[str, str], list[str]], key: tuple[str, str], value: str) -> None:
        """Removes `value` from edges[key], deleting the entry if it empties."""
        values = edges.get(key)
        if values and value in values:
            values.remove(value)
            if not values:
                del edges[key]

    # -- read path (RelationGraphIndex) ---------------------------------

    def related(self, entity: str, relation: str) -> list[Entity]:
        """Follows `relation` forward or backward from `entity` — accepts
        either its declared VOCABULARY name or its inverse name (RF-5).
        Returns [] if the entity or relation doesn't resolve; never raises."""
        return self._related_by_key(canonical_key(entity), relation)

    def _related_by_key(self, entity_key: str, relation: str) -> list[Entity]:
        """Same as related(), given an already-canonical entity key — avoids
        re-normalizing the same key on every VOCABULARY entry in relations_of()."""
        relation_def = VOCABULARY_BY_NAME.get(relation)

        if relation_def is None:
            # `relation` might be an inverse name (e.g. "serves_on" for "crew").
            relation_def = VOCABULARY_BY_INVERSE.get(relation)
            if relation_def is None:
                return []
            keys = self.in_edges.get((entity_key, relation_def.name), [])
            return self._resolve_keys(keys)

        keys = list(self.out_edges.get((entity_key, relation_def.name), []))
        if relation_def.inverse == relation_def.name:
            # Symmetric relation: the other direction is equally valid, but
            # don't double-count a neighbor already found via out_edges.
            keys += [k for k in self.in_edges.get((entity_key, relation_def.name), []) if k not in keys]
        return self._resolve_keys(keys)

    def relations_of(self, entity: str) -> dict[str, list[Entity]]:
        """All relations of an entity, forward and inverse, keyed by the name
        a caller would pass back into related()."""
        entity_key = canonical_key(entity)
        result: dict[str, list[Entity]] = {}
        for relation_def in VOCABULARY:
            forward = self._related_by_key(entity_key, relation_def.name)
            if forward:
                result[relation_def.name] = forward
            if relation_def.inverse != relation_def.name:
                backward = self._related_by_key(entity_key, relation_def.inverse)
                if backward:
                    result[relation_def.inverse] = backward
        return result

    def diagnostics(self) -> Diagnostics:
        return Diagnostics(
            dangling=list(self.dangling),
            key_collisions=list(self.key_collisions),
            parse_warnings=list(self.parse_warnings),
        )

    def _resolve_keys(self, keys: list[str]) -> list[Entity]:
        return [self.entities[k] for k in keys if k in self.entities]


class RelationIndexBuilder:
    """Builds a RelationIndex via a two-pass scan of the active archive root,
    and incrementally reindexes single files against an already-built one."""

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
            index.register_entity(self._build_entity(rel_path, frontmatter, entry["mtime"]))

            if frontmatter is not None:
                file_warnings: list[ParseWarning] = []
                parsed_edges.extend(self._parser.parse(rel_path, frontmatter, file_warnings))
                for warning in file_warnings:
                    index.record_parse_warning(warning)

        # Pass 2: resolve targets now that `entities` is complete.
        for edge in parsed_edges:
            if edge.target in index.entities:
                index.record_resolved(edge)
            else:
                index.record_dangling(edge)

        return index

    async def reindex_file(self, index: RelationIndex, path: Path) -> None:
        """Invalidates and rebuilds every edge originating from `path` (root-
        relative), without rescanning the archive (RF-6). If the file no
        longer exists, drops its entity and demotes incoming edges to
        dangling. All other files' entities/edges are left untouched."""
        index.drop_path(path)

        try:
            absolute_path = PathSanitizer.resolve_and_sanitize(str(path))
        except AegisError:
            index.remove_entity_at_path(path)
            return

        def _stat_if_exists() -> float | None:
            return absolute_path.stat().st_mtime if absolute_path.is_file() else None

        mtime = await anyio.to_thread.run_sync(_stat_if_exists)
        if mtime is None:
            index.remove_entity_at_path(path)
            return

        try:
            content = await read_text_at(absolute_path)
        except (OSError, UnicodeDecodeError) as e:
            _log.warning("AEGIS_RELATIONS // UNREADABLE_FILE // %s — %s", path, e)
            index.remove_entity_at_path(path)
            return

        frontmatter = extract_frontmatter(content)
        index.register_entity(self._build_entity(path, frontmatter, mtime))

        if frontmatter is None:
            return

        file_warnings: list[ParseWarning] = []
        for edge in self._parser.parse(path, frontmatter, file_warnings):
            if edge.target in index.entities:
                index.record_resolved(edge)
            else:
                index.record_dangling(edge)
        for warning in file_warnings:
            index.record_parse_warning(warning)

    @staticmethod
    def _build_entity(rel_path: Path, frontmatter: dict | None, mtime: float) -> Entity:
        entity_type = frontmatter.get("type") if frontmatter else None
        if not isinstance(entity_type, str):
            entity_type = None
        stem = rel_path.stem
        return Entity(
            key=canonical_key(stem),
            display_name=stem,
            path=rel_path,
            entity_type=entity_type,
            mtime=mtime,
        )
