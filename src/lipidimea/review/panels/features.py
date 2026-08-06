"""
lipidimea.review.panels.features
================================

Top-right "DIA features in group" panel. One row per DIA precursor in
the currently selected feature group, with columns:

    [display ☑/☐]   [ID]   [data file]

The display column toggles whether that precursor's traces are shown in
the plots. Toggling is purely a viewing concern (it lives on the
Feature dataclass, not in the session deletion sets) and resets each
time a new group is loaded -- per spec.

Interactions
------------
- Click on the display cell toggles that row's display flag.
- `d` key toggles the currently selected row.
- `Delete`/`Backspace` marks the currently selected feature for deletion.

Data file names can be long; this panel enables horizontal scrolling
and lets the data file column extend off the right edge.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..models import Feature
from .base import Column, SortableTable


# ---------------------------------------------------------------------------
# Display glyphs
# ---------------------------------------------------------------------------

_GLYPH_ON = "☑"
_GLYPH_OFF = "☐"


def _display_glyph(f: Feature) -> str:
    return _GLYPH_ON if f.display else _GLYPH_OFF


# ---------------------------------------------------------------------------
# Columns
# ---------------------------------------------------------------------------

_COLUMNS: list[Column] = [
    Column(
        key="display",
        heading="display",
        width=60,
        anchor="center",
        stretch=False,
        sort_key=lambda f: not f.display,  # ☑ rows first when ascending
    ),
    Column(
        key="id",
        heading="ID",
        width=70,
        anchor="e",
        stretch=False,
        sort_key=lambda f: f.id,
    ),
    Column(
        key="data_file",
        heading="data file",
        width=400,
        anchor="w",
        stretch=False,  # don't stretch -- let it overflow into hsb
        sort_key=lambda f: f.data_file,
    ),
]


def _values(f: Feature) -> tuple[str, ...]:
    return (
        _display_glyph(f),
        str(f.id),
        f.data_file,
    )


# ---------------------------------------------------------------------------
# FeaturePanel
# ---------------------------------------------------------------------------


class FeaturePanel(SortableTable[Feature]):
    """Concrete feature panel: SortableTable specialized for Feature with
    a clickable display column and a `d`-key toggle."""

    _DELETED_TAG = "deleted"
    _DISPLAY_COL_KEY = "display"

    def __init__(self, master: tk.Widget) -> None:
        super().__init__(
            master,
            columns=_COLUMNS,
            get_id=lambda f: f.id,
            get_values=_values,
            title="DIA features in group",
            show_id_filter=True,
            horizontal_scroll=True,
            height=8,
        )

        #: Optional callback fired after a display toggle, with the
        #: feature id whose display flag just changed. The app uses
        #: this to trigger a plot redraw.
        self.on_toggle_display: "callable[[int], None] | None" = None

        self.tree.tag_configure(
            self._DELETED_TAG,
            foreground="#999999",
            background="#f4f4f4",
        )

        # Click-to-toggle on the display column.
        self.tree.bind("<Button-1>", self._on_click, add="+")
        # `d` keybind toggles the active row's display.
        self.tree.bind("d", self._on_d_key)
        self.tree.bind("D", self._on_d_key)

    # ------------------------------------------------------------------ #
    # Row rendering with deleted tag
    # ------------------------------------------------------------------ #

    def set_rows(self, items) -> None:  # type: ignore[override]
        super().set_rows(items)
        self._apply_deleted_tags()

    def update_row(self, item: Feature) -> None:  # type: ignore[override]
        super().update_row(item)
        self._apply_deleted_tag_for(item)

    def _apply_deleted_tags(self) -> None:
        for item in self._items.values():
            self._apply_deleted_tag_for(item)

    def _apply_deleted_tag_for(self, item: Feature) -> None:
        iid = str(item.id)
        if not self.tree.exists(iid):
            return
        tags = (self._DELETED_TAG,) if item.deleted else ()
        self.tree.item(iid, tags=tags)

    # ------------------------------------------------------------------ #
    # Display toggling
    # ------------------------------------------------------------------ #

    def _toggle_display(self, feature_id: int) -> None:
        feat = self._items.get(feature_id)
        if feat is None or feat.deleted:
            return
        feat.display = not feat.display
        self.update_row(feat)
        if self.on_toggle_display is not None:
            self.on_toggle_display(feature_id)

    def _on_click(self, event: tk.Event) -> str | None:
        # Only react when clicking inside an actual row in the table area.
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return None
        col_id = self.tree.identify_column(event.x)  # e.g. "#1"
        if not col_id.startswith("#"):
            return None
        try:
            col_idx = int(col_id[1:]) - 1
        except ValueError:
            return None
        if col_idx < 0 or col_idx >= len(self._columns):
            return None
        if self._columns[col_idx].key != self._DISPLAY_COL_KEY:
            return None
        iid = self.tree.identify_row(event.y)
        if not iid:
            return None
        try:
            rid = int(iid)
        except ValueError:
            return None
        self._toggle_display(rid)
        # Don't return "break" -- letting the click also drive normal
        # selection is fine and matches user expectation.
        return None

    def _on_d_key(self, _event: tk.Event) -> str:
        rid = self.selected_id
        if rid is not None:
            self._toggle_display(rid)
        return "break"
    