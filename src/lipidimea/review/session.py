"""
lipidimea.review.session
========================

In-memory session state for the review app. Wraps a single open results
database, the dictionary of all feature groups, an LRU cache of populated
GroupViews, and the three deletion sets that drive the dirty flag.

The session is the single source of truth for "what has been deleted in
this session"; the `.deleted` flags on dataclass instances are kept in
sync with the deletion sets so UI code can read the flag directly off
any row it has a handle to.

No Tk imports here -- this module is fully testable in isolation.
"""

from collections import OrderedDict
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from . import db
from .models import FeatureGroup, GroupView


#: How many populated GroupViews to keep in memory at once. Each view
#: includes all blob arrays for every precursor in its group, so this is
#: the main memory knob. 8 covers typical back-and-forth navigation.
LRU_SIZE: int = 8


# ---------------------------------------------------------------------------
# Undo log
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _DeleteOp:
    """A single deletion, recorded so it can be undone."""

    kind: str  # "group" | "feature" | "annotation"
    id: int


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------


class Session:
    """Owns the DB connection, the in-memory dataclass dicts, and the
    deletion bookkeeping for one results database.

    Construction loads all FeatureGroup rows eagerly (cheap, one query).
    Populated GroupViews are loaded on demand via `get_group_view` and
    cached LRU-style.
    """

    def __init__(self, db_path: str | Path) -> None:
        self.db_path: Path = Path(db_path)
        self.conn = db.open_connection(str(self.db_path))

        # All shallow groups, keyed by id. Loaded once at startup; deleted
        # entries are removed from this dict on commit.
        self.groups: dict[int, FeatureGroup] = db.load_all_feature_groups(
            self.conn
        )

        # LRU of populated views. OrderedDict: most-recently-used at the end.
        self._view_cache: OrderedDict[int, GroupView] = OrderedDict()

        # Pending deletions (in-memory only until commit()).
        self._deleted_groups: set[int] = set()
        self._deleted_features: set[int] = set()
        self._deleted_annotations: set[int] = set()

        # Undo log of deletion ops, most recent at the end.
        self._undo: list[_DeleteOp] = []

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def close(self) -> None:
        """Close the underlying DB connection. Idempotent."""
        try:
            self.conn.close()
        except Exception:
            pass

    def __enter__(self) -> "Session":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # ------------------------------------------------------------------ #
    # State queries
    # ------------------------------------------------------------------ #

    @property
    def dirty(self) -> bool:
        """True if any deletions are pending commit."""
        return bool(
            self._deleted_groups
            or self._deleted_features
            or self._deleted_annotations
        )

    @property
    def n_pending_deletions(self) -> tuple[int, int, int]:
        """(groups, features, annotations) counts of pending deletions."""
        return (
            len(self._deleted_groups),
            len(self._deleted_features),
            len(self._deleted_annotations),
        )

    def iter_live_groups(self) -> Iterator[FeatureGroup]:
        """Yield groups that are not pending deletion. Order matches the
        underlying dict insertion order (which is ascending id from the
        loader's ORDER BY)."""
        for g in self.groups.values():
            if not g.deleted:
                yield g

    # ------------------------------------------------------------------ #
    # GroupView loading + caching
    # ------------------------------------------------------------------ #

    def get_group_view(self, group_id: int) -> GroupView:
        """Return the populated view for `group_id`, building it from the
        DB on cache miss. Always returns a view with `.deleted` flags
        synced to the current deletion sets."""
        view = self._view_cache.get(group_id)
        if view is None:
            view = db.load_group_view(
                self.conn, group_id, groups_cache=self.groups
            )
            self._view_cache[group_id] = view
            while len(self._view_cache) > LRU_SIZE:
                self._view_cache.popitem(last=False)  # evict oldest
        else:
            self._view_cache.move_to_end(group_id)  # mark MRU

        self._sync_deleted_flags(view)
        return view

    def invalidate_view_cache(self, group_id: int | None = None) -> None:
        """Drop one cached view (or all of them). Called after operations
        that might invalidate cached blob arrays."""
        if group_id is None:
            self._view_cache.clear()
        else:
            self._view_cache.pop(group_id, None)

    def _sync_deleted_flags(self, view: GroupView) -> None:
        """Make `.deleted` on every dataclass in the view reflect the
        current deletion sets. Cheap; called on every view retrieval."""
        view.group.deleted = view.group.id in self._deleted_groups
        for fid, feat in view.features.items():
            feat.deleted = fid in self._deleted_features
        for aid, ann in view.annotations.items():
            ann.deleted = aid in self._deleted_annotations

    # ------------------------------------------------------------------ #
    # Deletion API
    # ------------------------------------------------------------------ #

    def delete_group(self, group_id: int) -> None:
        if group_id in self._deleted_groups:
            return
        self._deleted_groups.add(group_id)
        if group_id in self.groups:
            self.groups[group_id].deleted = True
        view = self._view_cache.get(group_id)
        if view is not None:
            view.group.deleted = True
        self._undo.append(_DeleteOp("group", group_id))

    def delete_feature(self, feature_id: int) -> None:
        if feature_id in self._deleted_features:
            return
        self._deleted_features.add(feature_id)
        for view in self._view_cache.values():
            feat = view.features.get(feature_id)
            if feat is not None:
                feat.deleted = True
        self._undo.append(_DeleteOp("feature", feature_id))

    def delete_annotation(self, annotation_id: int) -> None:
        if annotation_id in self._deleted_annotations:
            return
        self._deleted_annotations.add(annotation_id)
        for view in self._view_cache.values():
            ann = view.annotations.get(annotation_id)
            if ann is not None:
                ann.deleted = True
        self._undo.append(_DeleteOp("annotation", annotation_id))

    def undelete_group(self, group_id: int) -> None:
        self._deleted_groups.discard(group_id)
        if group_id in self.groups:
            self.groups[group_id].deleted = False
        view = self._view_cache.get(group_id)
        if view is not None:
            view.group.deleted = False

    def undelete_feature(self, feature_id: int) -> None:
        self._deleted_features.discard(feature_id)
        for view in self._view_cache.values():
            feat = view.features.get(feature_id)
            if feat is not None:
                feat.deleted = False

    def undelete_annotation(self, annotation_id: int) -> None:
        self._deleted_annotations.discard(annotation_id)
        for view in self._view_cache.values():
            ann = view.annotations.get(annotation_id)
            if ann is not None:
                ann.deleted = False

    # ------------------------------------------------------------------ #
    # Undo / discard
    # ------------------------------------------------------------------ #

    def undo_last_deletion(self) -> _DeleteOp | None:
        """Reverse the most recent deletion. Returns the op that was
        undone, or None if the undo stack was empty."""
        if not self._undo:
            return None
        op = self._undo.pop()
        match op.kind:
            case "group":
                self.undelete_group(op.id)
            case "feature":
                self.undelete_feature(op.id)
            case "annotation":
                self.undelete_annotation(op.id)
        return op

    def discard_pending_deletions(self) -> None:
        """Drop all pending deletions without touching the DB. Used when
        loading a new database (per spec: discard unsaved changes)."""
        self._deleted_groups.clear()
        self._deleted_features.clear()
        self._deleted_annotations.clear()
        self._undo.clear()
        # Reset all in-memory flags.
        for g in self.groups.values():
            g.deleted = False
        for view in self._view_cache.values():
            for f in view.features.values():
                f.deleted = False
            for a in view.annotations.values():
                a.deleted = False

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #

    def commit(self) -> tuple[int, int, int]:
        """Apply pending deletions to the database in a single transaction.

        Returns the (groups, features, annotations) counts that were
        deleted, for status-bar reporting.

        Post-commit the in-memory state is reconciled: deleted groups are
        removed from `self.groups`, deletion sets and undo log are cleared,
        and the view cache is dropped (simpler than splicing out deleted
        sub-rows from cached views).
        """
        counts = self.n_pending_deletions
        if not self.dirty:
            return counts

        db.commit_deletions(
            self.conn,
            deleted_groups=self._deleted_groups,
            deleted_features=self._deleted_features,
            deleted_annotations=self._deleted_annotations,
        )

        # Reconcile in-memory state with the now-modified DB.
        for gid in self._deleted_groups:
            self.groups.pop(gid, None)
        self._view_cache.clear()
        self._deleted_groups.clear()
        self._deleted_features.clear()
        self._deleted_annotations.clear()
        self._undo.clear()

        return counts
