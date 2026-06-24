"""
lipidimea.review.export
=======================

CSV export of the current session state.

Output is one row per (feature group, lipid annotation) pair, plus one
row for each retained feature group that has no annotations. "Retained"
respects in-memory deletions but does not require them to be committed
to the database first -- per spec, export is a snapshot of the current
review view.

A row is emitted unless any of:
- its feature group is marked deleted in the session, or
- its lipid annotation is marked deleted in the session, or
- the DIA precursor the annotation is attached to is marked deleted.
"""

from __future__ import annotations

import csv
from pathlib import Path

from .session import Session


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------

CSV_COLUMNS: tuple[str, ...] = (
    "group_id",
    "group_mz",
    "group_rt",
    "group_dt",
    "group_ccs",
    "annotation_id",
    "lipid",
    "adduct",
    "mz_ppm_err",
    "ccs_pct_err",
    "acyl_chains",
)


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------

# Joins groups -> precursors -> lipids. INNER JOIN on Lipids so groups
# without annotations are not produced here; those are emitted separately
# by iterating live groups and noting which ids didn't appear in the
# join result.
_ANN_QUERY = """
    SELECT
        g.dia_fgroup_id,
        L.lipid_id,
        L.dia_pre_id,
        L.lipid,
        L.adduct,
        L.mz_ppm_err,
        L.ccs_pct_err,
        L.acyl_chains
    FROM DIAFeatureGroups AS g
    JOIN DIAPrecursorToGroup AS g2p
        ON g2p.dia_fgroup_id = g.dia_fgroup_id
    JOIN Lipids AS L
        ON L.dia_pre_id = g2p.dia_pre_id
    ORDER BY g.dia_fgroup_id, L.lipid_id
"""


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _fmt_float(v: float | None, *, places: int) -> str:
    return "" if v is None else f"{v:.{places}f}"


def _fmt_str(v: str | None) -> str:
    return "" if v is None else v


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


def export_csv(session: Session, path: Path) -> int:
    """Write a CSV of the current session state. Returns the number of
    data rows written (excludes the header)."""

    # Live group ids (per the in-memory deletion sets), and a quick
    # lookup for the group dataclass so we can pull mz/rt/dt/ccs.
    live_groups = list(session.iter_live_groups())
    live_group_ids: set[int] = {g.id for g in live_groups}
    groups_by_id = {g.id: g for g in live_groups}

    # Pull the deletion sets directly. These are part of session.py's
    # in-package surface; we read them rather than reconstructing the
    # filter from get_group_view, since this is far cheaper for export.
    deleted_features = session._deleted_features
    deleted_annotations = session._deleted_annotations

    # Run the join and bucket annotations by group, filtering out any
    # rows whose group / feature / annotation is pending deletion.
    cur = session.conn.cursor()
    annotations_by_group: dict[int, list[tuple]] = {}
    seen_groups_with_anns: set[int] = set()

    for row in cur.execute(_ANN_QUERY):
        (
            gid,
            lid,
            fid,
            lipid,
            adduct,
            ppm,
            pct,
            acyl,
        ) = row
        if gid not in live_group_ids:
            continue
        if fid in deleted_features:
            continue
        if lid in deleted_annotations:
            continue
        annotations_by_group.setdefault(gid, []).append(
            (lid, lipid, adduct, ppm, pct, acyl)
        )
        seen_groups_with_anns.add(gid)

    # Write rows: ordered by group id (matches session.iter_live_groups
    # which is dict insertion order, which is ascending id from the
    # loader's ORDER BY).
    n_rows = 0
    path = Path(path)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(CSV_COLUMNS)

        for g in live_groups:
            group_cells = (
                str(g.id),
                _fmt_float(g.mz, places=4),
                _fmt_float(g.rt, places=2),
                _fmt_float(g.dt, places=2),
                _fmt_float(g.ccs, places=2),
            )
            anns = annotations_by_group.get(g.id, [])
            if not anns:
                # Group with no annotations: still emit a row so the
                # group itself appears in the output.
                writer.writerow(
                    group_cells + ("", "", "", "", "", "")
                )
                n_rows += 1
                continue
            for lid, lipid, adduct, ppm, pct, acyl in anns:
                writer.writerow(
                    group_cells
                    + (
                        str(lid),
                        _fmt_str(lipid),
                        _fmt_str(adduct),
                        _fmt_float(ppm, places=2),
                        _fmt_float(pct, places=2),
                        _fmt_str(acyl),
                    )
                )
                n_rows += 1

    return n_rows
