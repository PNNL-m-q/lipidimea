"""
lipidimea.review.panels.groups
==============================

Left-column "DIA feature groups" panel. Shows one row per FeatureGroup;
selection drives the rest of the UI (plots, feature panel, annotation
panel) via the panel's `on_select` callback.

Deleted-but-not-yet-committed groups remain visible in the table,
rendered in a muted style so the user can still see what's pending and
undo if needed.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..models import FeatureGroup
from .base import Column, SortableTable


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def _fmt_mz(v: float) -> str:
    return f"{v:.4f}"


def _fmt_rt(v: float) -> str:
    return f"{v:.2f}"


def _fmt_dt(v: float) -> str:
    return f"{v:.2f}"


def _fmt_ccs(v: float | None) -> str:
    return "" if v is None else f"{v:.2f}"


_COLUMNS: list[Column] = [
    Column(
        key="id",
        heading="ID",
        width=70,
        anchor="e",
        stretch=False,
        sort_key=lambda g: g.id,
    ),
    Column(
        key="mz",
        heading="m/z",
        width=90,
        anchor="e",
        stretch=False,
        sort_key=lambda g: g.mz,
    ),
    Column(
        key="rt",
        heading="RT",
        width=70,
        anchor="e",
        stretch=False,
        sort_key=lambda g: g.rt,
    ),
    Column(
        key="dt",
        heading="DT",
        width=70,
        anchor="e",
        stretch=False,
        sort_key=lambda g: g.dt,
    ),
    Column(
        key="ccs",
        heading="CCS",
        width=80,
        anchor="e",
        stretch=False,
        # Sort None to the end regardless of direction.
        sort_key=lambda g: (g.ccs is None, g.ccs if g.ccs is not None else 0.0),
    ),
    Column(
        key="n_ann",
        heading="# Ann.",
        width=50,
        anchor="e",
        stretch=False,
        sort_key=lambda g: g.n_annotations,
    ),
]


def _values(g: FeatureGroup) -> tuple[str, ...]:
    return (
        str(g.id),
        _fmt_mz(g.mz),
        _fmt_rt(g.rt),
        _fmt_dt(g.dt),
        _fmt_ccs(g.ccs),
        str(g.n_annotations)
    )


# ---------------------------------------------------------------------------
# GroupPanel
# ---------------------------------------------------------------------------


class GroupPanel(SortableTable[FeatureGroup]):
    """Concrete group panel: SortableTable specialized for FeatureGroup."""

    #: Tag name applied to rows representing groups marked for deletion.
    _DELETED_TAG = "deleted"

    def __init__(self, master: tk.Widget) -> None:
        super().__init__(
            master,
            columns=_COLUMNS,
            get_id=lambda g: g.id,
            get_values=_values,
            title="DIA feature groups",
            show_id_filter=True,
            horizontal_scroll=False,
            height=20,
        )
        # Configure muted style for deleted rows.
        self.tree.tag_configure(
            self._DELETED_TAG,
            foreground="#999999",
            background="#f4f4f4",
        )
        # Re-apply tags after each refresh by overriding the parent
        # rendering through update_row / set_rows hooks below.

    # ------------------------------------------------------------------ #
    # Override row insertion to apply the deleted tag where appropriate.
    # We do this by post-processing after the parent populates rows.
    # ------------------------------------------------------------------ #

    def set_rows(self, items) -> None:  # type: ignore[override]
        super().set_rows(items)
        self._apply_deleted_tags()

    def update_row(self, item: FeatureGroup) -> None:  # type: ignore[override]
        super().update_row(item)
        self._apply_deleted_tag_for(item)

    def _apply_deleted_tags(self) -> None:
        for rid, item in self._items.items():
            self._apply_deleted_tag_for(item)

    def _apply_deleted_tag_for(self, item: FeatureGroup) -> None:
        iid = str(item.id)
        if not self.tree.exists(iid):
            return
        tags = (self._DELETED_TAG,) if item.deleted else ()
        self.tree.item(iid, tags=tags)
        