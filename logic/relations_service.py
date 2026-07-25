"""
AEGIS_RELATIONS_SERVICE: keeps one live RelationIndex per active archive root.

Deliberately not a global singleton: the active root is per-request
(`PathSanitizer`, bound per-user in `main.py`'s `auth_middleware`), so a
single shared index would mix one user's entities/relations into another's
session — the same class of shortcut `StorageCache` takes for storage stats
(low-stakes there: a stale byte count; unacceptable here, a real data leak).
Keyed instead by the resolved root Path, one RelationIndex per root, built
lazily on first access.
"""
import asyncio
from collections import defaultdict
from pathlib import Path

from logic.files import PathSanitizer
from logic.relations_index import RelationIndex, RelationIndexBuilder

_indexes: dict[Path, RelationIndex] = {}
_locks: dict[Path, asyncio.Lock] = defaultdict(asyncio.Lock)


class RelationGraphService:
    """Lazily builds and caches a RelationIndex per active archive root."""

    @staticmethod
    async def get_index() -> RelationIndex:
        root = PathSanitizer.get_root().resolve()
        if root in _indexes:
            return _indexes[root]
        async with _locks[root]:
            if root not in _indexes:  # re-check: another request may have built it while we waited
                _indexes[root] = await RelationIndexBuilder().build()
        return _indexes[root]

    @staticmethod
    async def reindex_file(path: str, content: str | None = None) -> None:
        """Incrementally updates the current root's index for a single file
        (RF-6), if that root's index has already been built. A no-op
        otherwise — the next get_index() call performs a full build anyway,
        which would already reflect this file's current state.

        content: pass the caller's already-in-memory new text (e.g. right
        after a save) to skip a redundant re-read of the file just written."""
        root = PathSanitizer.get_root().resolve()
        index = _indexes.get(root)
        if index is None:
            return
        await RelationIndexBuilder().reindex_file(index, Path(path), content)

    @staticmethod
    async def reindex_all() -> RelationIndex:
        """Forces a full rebuild for the current root (POST /api/index/reindex)."""
        root = PathSanitizer.get_root().resolve()
        async with _locks[root]:
            _indexes[root] = await RelationIndexBuilder().build()
        return _indexes[root]

    @staticmethod
    def invalidate_all() -> None:
        """Drops every cached index — for tests, and for a root switch (the
        active root changing invalidates nothing by itself since indexes are
        keyed by root, but a deleted/renamed root's cache would otherwise
        linger unused forever)."""
        _indexes.clear()
        _locks.clear()
