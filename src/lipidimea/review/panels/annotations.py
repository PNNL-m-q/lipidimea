"""
lipidimea.review.panels.annotations
===================================

Bottom-right "lipid annotations" panel. One row per LipidAnnotation
attached to any DIA precursor in the currently selected feature group.

Selection in this panel has a side effect on the MS2 plot: the chosen
annotation becomes the "active annotation" used to draw fragment guide
lines and to enrich MS2 hover tooltips with fragment labels. The app
wires this via the panel's `on_select` callback.

No panel-specific keybindings beyond the base behavior (sort, ID
filter, Delete/Backspace).
"""

from __future__ import annotations

import tkinter as tk

from ..models import LipidAnnotation
from .base import Column, SortableTable


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def _fmt_ppm(v: float) -> str:
    return f"{v:.2f}"


def _fmt_pct(v: float | None) -> str:
    return "" if v is None else f"{v:.2f}"


def _fmt_str_or_blank(v: str | None) -> str:
    return "" if v is None else v


_COLUMNS: list[Column] = [
    Column(
        key="id",
        heading="ID",
        width=70,
        anchor="e",
        stretch=False,
        sort_key=lambda a: a.id,
    ),
    Column(
        key="lipid",
        heading="lipid",
        width=160,
        anchor="w",
        stretch=True,
        sort_key=lambda a: a.lipid,
    ),
    Column(
        key="adduct",
        heading="adduct",
        width=80,
        anchor="w",
        stretch=False,
        sort_key=lambda a: a.adduct,
    ),
    Column(
        key="mz_ppm_err",
        heading="m/z ppm err.",
        width=100,
        anchor="e",
        stretch=False,
        sort_key=lambda a: abs(a.mz_ppm_err),  # sort by magnitude
    ),
    Column(
        key="ccs_pct_err",
        heading="CCS %err",
        width=90,
        anchor="e",
        stretch=False,
        # None last regardless of direction; otherwise sort by magnitude.
        sort_key=lambda a: (
            a.ccs_pct_err is None,
            abs(a.ccs_pct_err) if a.ccs_pct_err is not None else 0.0,
        ),
    ),
    Column(
        key="acyl_chains",
        heading="acyl chains",
        width=120,
        anchor="w",
        stretch=False,
        sort_key=lambda a: a.acyl_chains or "",
    ),
]


def _values(a: LipidAnnotation) -> tuple[str, ...]:
    return (
        str(a.id),
        a.lipid,
        a.adduct,
        _fmt_ppm(a.mz_ppm_err),
        _fmt_pct(a.ccs_pct_err),
        _fmt_str_or_blank(a.acyl_chains),
    )


# ---------------------------------------------------------------------------
# AnnotationPanel
# ---------------------------------------------------------------------------


class AnnotationPanel(SortableTable[LipidAnnotation]):
    """Concrete lipid-annotation panel."""

    _DELETED_TAG = "deleted"

    def __init__(self, master: tk.Widget) -> None:
        super().__init__(
            master,
            columns=_COLUMNS,
            get_id=lambda a: a.id,
            get_values=_values,
            title="lipid annotations",
            show_id_filter=True,
            horizontal_scroll=False,
            height=8,
        )
        self.tree.tag_configure(
            self._DELETED_TAG,
            foreground="#999999",
            background="#f4f4f4",
        )

    # ------------------------------------------------------------------ #
    # Row rendering with deleted tag
    # ------------------------------------------------------------------ #

    def set_rows(self, items) -> None:  # type: ignore[override]
        super().set_rows(items)
        self._apply_deleted_tags()

    def update_row(self, item: LipidAnnotation) -> None:  # type: ignore[override]
        super().update_row(item)
        self._apply_deleted_tag_for(item)

    def _apply_deleted_tags(self) -> None:
        for item in self._items.values():
            self._apply_deleted_tag_for(item)

    def _apply_deleted_tag_for(self, item: LipidAnnotation) -> None:
        iid = str(item.id)
        if not self.tree.exists(iid):
            return
        tags = (self._DELETED_TAG,) if item.deleted else ()
        self.tree.item(iid, tags=tags)

    # ------------------------------------------------------------------ #
    # Selection -> active annotation
    # ------------------------------------------------------------------ #

    @property
    def selected_annotation(self) -> LipidAnnotation | None:
        """Convenience for callers that want the dataclass, not just an
        id. Returns None if nothing selected, the selected row was just
        removed, or the selected annotation is pending deletion (the
        last case is debatable; we exclude deleted here so the MS2 plot
        doesn't decorate based on a row the user has marked for
        removal)."""
        rid = self.selected_id
        if rid is None:
            return None
        item = self._items.get(rid)
        if item is None or item.deleted:
            return None
        return item
