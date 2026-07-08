"""
lipidimea.review.db
===================

Database access layer. Pure functions over a sqlite3 connection; no UI,
no in-memory state. Returns dataclasses defined in `lipidimea.review.models`.

Conventions
-----------
- All loader functions take a `sqlite3.Connection` (not a Cursor) and create
  their own cursors as needed.
- Loaders raise `DBLoadError` on missing/inconsistent rows that should never
  occur in a well-formed results database; callers may catch and report.
- `commit_deletions` issues `DELETE` statements in a single transaction.

NOTE on cascading deletes
-------------------------
The current schema does not declare foreign-key constraints, so deleting a
feature group / feature / annotation here will leave orphan rows in
dependent tables (`DIAPrecursorToGroup`, `Raw`, `DIAFragments`, `Lipids`).
Those orphans are effectively invisible to the review UI because all of its
queries start from `DIAFeatureGroups`. If the schema is updated in the
future to declare FK relationships with `ON DELETE CASCADE`, the manual
multi-table cleanup can be replaced with a single delete on the parent
table.
"""

import sqlite3
from collections.abc import Iterable

import numpy as np

from .models import (
    DDAMatch,
    Feature,
    FeatureGroup,
    GroupView,
    LipidAnnotation,
)


# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------

#: ppm tolerance used when looking up the closest matching DDA precursor
DDA_MATCH_PPM: float = 20.0

#: RT tolerance (minutes) used when looking up the closest matching DDA precursor
DDA_MATCH_RT_TOL: float = 0.3


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class DBLoadError(RuntimeError):
    """Raised when a query returns an unexpected/invalid number of rows."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ppm_tol(mz: float, ppm: float) -> float:
    """Absolute m/z tolerance corresponding to a ppm window."""
    return mz * ppm / 1e6


def _blob_to_2xN(blob: bytes, n: int) -> np.ndarray:
    """Decode a raw float64 blob of length 2*n into a (2, n) array."""
    return np.frombuffer(blob, dtype=np.float64).reshape((2, n))


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

_QUERIES: dict[str, str] = {
    # All feature groups, for the group panel.
    "all_feature_groups": """
        SELECT
            g.dia_fgroup_id, g.mz, g.rt, g.dt, g.ccs,
            COUNT(DISTINCT L.lipid_id) AS n_ann
        FROM DIAFeatureGroups AS g
        LEFT JOIN DIAPrecursorToGroup AS g2p
            ON g2p.dia_fgroup_id = g.dia_fgroup_id
        LEFT JOIN Lipids AS L
            ON L.dia_fgroup_id = g.dia_fgroup_id
        GROUP BY g.dia_fgroup_id
        ORDER BY g.dia_fgroup_id
    """,
    # One feature group's scalar info.
    "feature_group_info": """
        SELECT dia_fgroup_id, mz, rt, dt, ccs
        FROM DIAFeatureGroups
        WHERE dia_fgroup_id=?
    """,
    # Closest DDA match by m/z within m/z and RT tolerances. Returns at most
    # one row, the one with the smallest |Δm/z| (ties broken by |Δrt|).
    "closest_dda_feat": """
        SELECT dda_pre_id, mz, rt, rt_fwhm, rt_pkht
        FROM DDAPrecursors
        WHERE ABS(mz - ?) <= ?
          AND ABS(rt - ?) <= ?
        ORDER BY ABS(mz - ?), ABS(rt - ?)
        LIMIT 1
    """,
    # All DIA precursors in a group, with their data file label.
    # NOTE: assumes DIAPrecursors has a `data_file` column. If your schema
    # stores this elsewhere (e.g. via a join through a samples table),
    # adjust this query and the unpacking in `_load_features_for_group`.
    "precursors_in_group": """
        SELECT p.dia_pre_id, df.dfile_name
        FROM DIAPrecursorToGroup AS g2p
        JOIN DIAPrecursors AS p ON p.dia_pre_id = g2p.dia_pre_id
        JOIN DataFiles AS df ON p.dfile_id = df.dfile_id
        WHERE g2p.dia_fgroup_id=?
        ORDER BY p.dia_pre_id
    """,
    # Raw blobs (one row each) for a given DIA precursor.
    "dia_ms1_blob": """
        SELECT raw_n, raw_data FROM Raw
        WHERE raw_type='DIA_PRE_MS1' AND feat_id=?
    """,
    "dia_xic_blob": """
        SELECT raw_n, raw_data FROM Raw
        WHERE raw_type='DIA_PRE_XIC' AND feat_id=?
    """,
    "dia_atd_blob": """
        SELECT raw_n, raw_data FROM Raw
        WHERE raw_type='DIA_PRE_ATD' AND feat_id=?
    """,
    # Fragment spectra.
    "dda_ms2_spec": """
        SELECT fmz, fint FROM DDAFragments
        WHERE dda_pre_id=?
        ORDER BY fmz
    """,
    "dia_ms2_spec": """
        SELECT fmz, fint, deconvoluted FROM DIAFragments
        WHERE dia_pre_id=?
        ORDER BY fmz
    """,
    # Lipid annotations attached to any of a list of DIA feature groups. The
    # `IN (...)` placeholder is filled in dynamically in the loader since
    # sqlite3 doesn't bind list parameters.
    "lipids_for_fgroups_TEMPLATE": """
        SELECT lipid_id, dia_fgroup_id, lipid, adduct, mz_ppm_err,
               ccs_rel_err, chains
        FROM Lipids
        WHERE dia_fgroup_id IN ({placeholders})
        ORDER BY lipid_id
    """,
    # Annotated fragments for a set of lipid annotations. Uses the same
    # dynamic-IN-clause trick as the annotations query.
    "fragments_for_lipids_TEMPLATE": """
        SELECT
            lipid_id,
            frag_rule,
            rule_mz,
            diagnostic
        FROM LipidFragments
        WHERE lipid_id IN ({placeholders})
        ORDER BY lipid_id, rule_mz
    """,
}


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def load_all_feature_groups(conn: sqlite3.Connection) -> dict[int, FeatureGroup]:
    """Load every feature group in the DB as shallow rows, including a
    count of attached lipid annotations. Cheap; called once at app
    startup (and after committing deletions)."""
    cur = conn.cursor()
    out: dict[int, FeatureGroup] = {}
    for gid, mz, rt, dt, ccs, n_ann in cur.execute(
        _QUERIES["all_feature_groups"]
    ):
        out[gid] = FeatureGroup(
            id=gid, mz=mz, rt=rt, dt=dt, ccs=ccs, n_annotations=n_ann
        )
    return out


def load_dda_match(
    conn: sqlite3.Connection, mz: float, rt: float
) -> DDAMatch | None:
    """Find the closest DDA precursor within tolerance and load its MS2.

    Returns None if no DDA precursor is within (DDA_MATCH_PPM, DDA_MATCH_RT_TOL).
    """
    cur = conn.cursor()
    mz_tol = _ppm_tol(mz, DDA_MATCH_PPM)
    row = cur.execute(
        _QUERIES["closest_dda_feat"],
        (mz, mz_tol, rt, DDA_MATCH_RT_TOL, mz, rt),
    ).fetchone()
    if row is None:
        return None
    dda_pre_id, dmz, drt, drt_fwhm, drt_pkht = row

    spec_rows = cur.execute(_QUERIES["dda_ms2_spec"], (dda_pre_id,)).fetchall()
    if spec_rows:
        ms2 = np.asarray(spec_rows, dtype=np.float64).T  # shape (2, N)
    else:
        ms2 = np.empty((2, 0), dtype=np.float64)

    return DDAMatch(
        dda_pre_id=dda_pre_id,
        mz=dmz,
        rt=drt,
        rt_fwhm=drt_fwhm,
        rt_pkht=drt_pkht,
        ms2=ms2,
    )


def _load_blob_2xN(
    cur: sqlite3.Cursor, query: str, feat_id: int, *, label: str
) -> np.ndarray:
    """Fetch a single (raw_n, raw_data) row and decode it to a (2, N) array."""
    rows = cur.execute(query, (feat_id,)).fetchall()
    if len(rows) != 1:
        raise DBLoadError(
            f"expected exactly 1 {label} blob for feat_id={feat_id}, got {len(rows)}"
        )
    n, blob = rows[0]
    return _blob_to_2xN(blob, n)


def _load_features_for_group(
    conn: sqlite3.Connection, group_id: int
) -> dict[int, Feature]:
    """Load all DIA precursors in a group, including all their blob arrays
    and MS2 spectra. Returns dict keyed by feature (precursor) id."""
    cur = conn.cursor()
    rows = cur.execute(_QUERIES["precursors_in_group"], (group_id,)).fetchall()
    if not rows:
        raise DBLoadError(f"no DIA precursors assigned to group {group_id}")

    features: dict[int, Feature] = {}
    for pre_id, data_file in rows:
        ms1 = _load_blob_2xN(cur, _QUERIES["dia_ms1_blob"], pre_id, label="MS1")
        xic = _load_blob_2xN(cur, _QUERIES["dia_xic_blob"], pre_id, label="XIC")
        atd = _load_blob_2xN(cur, _QUERIES["dia_atd_blob"], pre_id, label="ATD")

        ms2_rows = cur.execute(_QUERIES["dia_ms2_spec"], (pre_id,)).fetchall()
        if ms2_rows:
            ms2 = np.asarray(ms2_rows, dtype=np.float64).T  # shape (3, N)
        else:
            ms2 = np.empty((3, 0), dtype=np.float64)

        features[pre_id] = Feature(
            id=pre_id,
            group_id=group_id,
            data_file=data_file,
            ms1=ms1,
            xic=xic,
            atd=atd,
            ms2=ms2,
        )
    return features


def _load_fragments_for_annotations(
    conn: sqlite3.Connection, lipid_ids: Iterable[int]
) -> dict[int, list["FragmentAnnotation"]]:
    """Load annotated fragments for the given lipid annotation ids,
    returning a dict keyed by lipid_id.

    Label is composed as `frag_rule` with `supports_fa` appended in
    parentheses when non-null.
    """
    from .models import FragmentAnnotation  # local import: avoid cycles

    lipid_ids = list(lipid_ids)
    if not lipid_ids:
        return {}

    cur = conn.cursor()
    placeholders = ",".join("?" * len(lipid_ids))
    query = _QUERIES["fragments_for_lipids_TEMPLATE"].format(
        placeholders=placeholders
    )

    out: dict[int, list[FragmentAnnotation]] = {}
    for lipid_id, frag_rule, rule_mz, diagnostic in cur.execute(
        query, lipid_ids
    ):
        out.setdefault(lipid_id, []).append(
            FragmentAnnotation(
                mz=rule_mz,
                label=frag_rule,
                diagnostic=bool(diagnostic),
            )
        )

    return out


def _load_annotations_for_features(
    conn: sqlite3.Connection, feature_ids: Iterable[int]
) -> dict[int, LipidAnnotation]:
    feature_ids = list(feature_ids)
    if not feature_ids:
        return {}

    cur = conn.cursor()
    placeholders = ",".join("?" * len(feature_ids))
    query = _QUERIES["lipids_for_fgroups_TEMPLATE"].format(
        placeholders=placeholders
    )

    out: dict[int, LipidAnnotation] = {}
    for row in cur.execute(query, feature_ids):
        (
            lipid_id, dia_fgroup_id, lipid, adduct,
            mz_ppm_err, ccs_pct_err, acyl_chains,
        ) = row
        out[lipid_id] = LipidAnnotation(
            id=lipid_id,
            feature_id=dia_fgroup_id,
            lipid=lipid,
            adduct=adduct,
            mz_ppm_err=mz_ppm_err,
            ccs_pct_err=ccs_pct_err,
            acyl_chains=acyl_chains,
            fragments=[],  # filled in below
        )

    # Second pass: populate fragments.
    frags_by_lipid = _load_fragments_for_annotations(conn, out.keys())
    for lipid_id, frags in frags_by_lipid.items():
        out[lipid_id].fragments = frags

    return out


def load_group_view(
    conn: sqlite3.Connection,
    group_id: int,
    *,
    groups_cache: dict[int, FeatureGroup] | None = None,
) -> GroupView:
    """Build a fully populated GroupView for a single feature group.

    If `groups_cache` is provided, the FeatureGroup is taken from it (avoiding
    a redundant query); otherwise it is re-fetched from the DB.
    """
    cur = conn.cursor()

    if groups_cache is not None and group_id in groups_cache:
        group = groups_cache[group_id]
    else:
        row = cur.execute(
            _QUERIES["feature_group_info"], (group_id,)
        ).fetchone()
        if row is None:
            raise DBLoadError(f"no feature group with id={group_id}")
        gid, mz, rt, dt, ccs = row
        group = FeatureGroup(id=gid, mz=mz, rt=rt, dt=dt, ccs=ccs)

    features = _load_features_for_group(conn, group_id)
    annotations = _load_annotations_for_features(conn, [group.id])
    dda = load_dda_match(conn, group.mz, group.rt)

    return GroupView(
        group=group,
        features=features,
        annotations=annotations,
        dda=dda,
    )


# ---------------------------------------------------------------------------
# Deletion
# ---------------------------------------------------------------------------

# TODO (schema): if FK constraints with ON DELETE CASCADE are added to the
# schema (DIAPrecursorToGroup.dia_fgroup_id -> DIAFeatureGroups.dia_fgroup_id,
# Raw.feat_id -> DIAPrecursors.dia_pre_id, DIAFragments.dia_pre_id ->
# DIAPrecursors.dia_pre_id, Lipids.dia_pre_id -> DIAPrecursors.dia_pre_id),
# the manual cleanup below can be replaced with a single DELETE on each
# parent table. For now, we delete only the parent rows and accept orphans
# in dependent tables -- they are invisible to the review UI because all
# its queries start from DIAFeatureGroups.

_DELETE_GROUP = "DELETE FROM DIAFeatureGroups WHERE dia_fgroup_id=?"
_DELETE_FEATURE = "DELETE FROM DIAPrecursors WHERE dia_pre_id=?"
_DELETE_ANNOTATION = "DELETE FROM Lipids WHERE lipid_id=?"


def commit_deletions(
    conn: sqlite3.Connection,
    *,
    deleted_groups: Iterable[int] = (),
    deleted_features: Iterable[int] = (),
    deleted_annotations: Iterable[int] = (),
) -> None:
    """Apply pending deletions in a single transaction.

    Order: annotations -> features -> groups. The order is not strictly
    necessary while there are no FK constraints, but it matches the
    dependency order that *will* be required once the schema is tightened.
    """
    deleted_annotations = list(deleted_annotations)
    deleted_features = list(deleted_features)
    deleted_groups = list(deleted_groups)

    if not (deleted_annotations or deleted_features or deleted_groups):
        return

    try:
        with conn:  # transaction; rolls back on exception
            cur = conn.cursor()
            if deleted_annotations:
                cur.executemany(
                    _DELETE_ANNOTATION, [(i,) for i in deleted_annotations]
                )
            if deleted_features:
                cur.executemany(
                    _DELETE_FEATURE, [(i,) for i in deleted_features]
                )
            if deleted_groups:
                cur.executemany(
                    _DELETE_GROUP, [(i,) for i in deleted_groups]
                )
    except sqlite3.Error as e:
        raise DBLoadError(f"failed to commit deletions: {e}") from e


# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------


def open_connection(db_path: str) -> sqlite3.Connection:
    """Open a sqlite3 connection suitable for the review app.

    No special pragmas yet; centralized so we have one place to add things
    like `PRAGMA foreign_keys=ON` once the schema supports it.
    """
    conn = sqlite3.connect(db_path)
    # TODO(schema): once FKs are declared, enable enforcement:
    # conn.execute("PRAGMA foreign_keys=ON")
    return conn