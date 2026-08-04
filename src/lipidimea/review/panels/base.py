"""
lipidimea.review.panels.base
============================

Reusable table widget for the three review panels (group / feature /
lipid). Wraps a `ttk.Treeview` with:

- Column-click sorting (toggles ascending / descending; visual chevron
  in the active header).
- Optional ID filter entry above the table that jumps the selection to
  the matching row on Enter.
- Vertical scrollbar always; horizontal scrollbar optional (used by the
  feature panel for its long data-file column).
- Active/inactive visual state driven by a colored border around the
  table frame -- the app sets this when the user switches panels via
  `g`/`f`/`l` keybinds.
- Pluggable selection / delete / row-click callbacks.

Concrete panels add their own keybindings (e.g. `d` to toggle display
on the feature panel) by reaching the inner Treeview via `self.tree`.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from tkinter import ttk
from typing import Any, Generic, TypeVar


# ---------------------------------------------------------------------------
# Visual constants
# ---------------------------------------------------------------------------

_BORDER_ACTIVE = "#3b82f6"   # blue
_BORDER_INACTIVE = "#cccccc"
_BORDER_THICKNESS = 2

_SORT_ASC_GLYPH = "  ▲"
_SORT_DESC_GLYPH = "  ▼"


# ---------------------------------------------------------------------------
# Column descriptor
# ---------------------------------------------------------------------------


@dataclass
class Column:
    """Declarative column descriptor for SortableTable.

    Attributes
    ----------
    key       : stable column identifier; passed back to value getters.
    heading   : header text shown to the user.
    width     : initial column width in pixels.
    anchor    : tk anchor for cell text ("w", "center", "e").
    stretch   : whether the column grows when the panel is resized.
    sort_key  : optional callable(item) -> sortable value. If omitted,
                the cell's display value is used (which sorts strings
                lexicographically -- usually fine, but numeric columns
                should supply a sort_key returning a number).
    """

    key: str
    heading: str
    width: int = 80
    anchor: str = "w"
    stretch: bool = True
    sort_key: Callable[[Any], Any] | None = None


T = TypeVar("T")


# ---------------------------------------------------------------------------
# SortableTable
# ---------------------------------------------------------------------------


class SortableTable(ttk.Frame, Generic[T]):
    """Treeview-based table parameterized by row item type T.

    Items are arbitrary objects; the table calls `get_id` to obtain a
    stable integer id (used as the Treeview iid in string form) and
    `get_values` to obtain a tuple of display strings (one per column,
    in the order the columns were declared).

    Public surface
    --------------
    set_rows(items)            : replace all rows.
    set_active(active)         : update active-border styling and grab
                                  focus when becoming active.
    select_id(row_id)          : programmatically select a row.
    selected_id                : property -> currently selected id, or None.
    on_select / on_delete /
        on_double_click        : assignable callbacks taking row_id.
    tree                       : the inner ttk.Treeview (for subclasses
                                  that need extra bindings).
    """

    def __init__(
        self,
        master: tk.Widget,
        *,
        columns: list[Column],
        get_id: Callable[[T], int],
        get_values: Callable[[T], tuple[str, ...]],
        title: str | None = None,
        show_id_filter: bool = True,
        horizontal_scroll: bool = False,
        height: int = 12,
    ) -> None:
        super().__init__(master)

        self._columns = columns
        self._get_id = get_id
        self._get_values = get_values

        self._items: dict[int, T] = {}            # id -> item
        self._sort_col: str | None = None
        self._sort_descending: bool = False

        self.on_select: Callable[[int], None] | None = None
        self.on_delete: Callable[[int], None] | None = None
        self.on_double_click: Callable[[int], None] | None = None

        self._build(
            title=title,
            show_id_filter=show_id_filter,
            horizontal_scroll=horizontal_scroll,
            height=height,
        )

    # ------------------------------------------------------------------ #
    # Construction
    # ------------------------------------------------------------------ #

    def _build(
        self,
        *,
        title: str | None,
        show_id_filter: bool,
        horizontal_scroll: bool,
        height: int,
    ) -> None:
        # Optional title above everything else.
        if title is not None:
            ttk.Label(self, text=title, font=("", 10, "bold")).pack(
                anchor="w", padx=4, pady=(2, 0)
            )

        # Optional ID filter entry.
        if show_id_filter:
            filter_frame = ttk.Frame(self)
            filter_frame.pack(fill="x", padx=4, pady=2)
            ttk.Label(filter_frame, text="ID:").pack(side="left")
            self._filter_var = tk.StringVar()
            entry = ttk.Entry(
                filter_frame, textvariable=self._filter_var, width=10
            )
            entry.pack(side="left", padx=(4, 0))
            entry.bind("<Return>", self._on_filter_submit)
        else:
            self._filter_var = None

        # Border frame -- this is what gets recolored on active/inactive.
        # Using a plain tk.Frame so we can set highlightbackground.
        self._border = tk.Frame(
            self,
            highlightthickness=_BORDER_THICKNESS,
            highlightbackground=_BORDER_INACTIVE,
            highlightcolor=_BORDER_INACTIVE,
        )
        self._border.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        # Treeview + scrollbars inside the border.
        col_keys = [c.key for c in self._columns]
        self.tree = ttk.Treeview(
            self._border,
            columns=col_keys,
            show="headings",
            height=height,
            selectmode="browse",
        )
        for col in self._columns:
            self.tree.heading(
                col.key,
                text=col.heading,
                command=lambda k=col.key: self._on_header_click(k),
            )
            self.tree.column(
                col.key,
                width=col.width,
                anchor=col.anchor,
                stretch=col.stretch,
            )

        vsb = ttk.Scrollbar(
            self._border, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=vsb.set)
        if horizontal_scroll:
            hsb = ttk.Scrollbar(
                self._border,
                orient="horizontal",
                command=self.tree.xview,
            )
            self.tree.configure(xscrollcommand=hsb.set)
            # Grid layout when we have an hsb so it sits in the bottom corner.
            self.tree.grid(row=0, column=0, sticky="nsew")
            vsb.grid(row=0, column=1, sticky="ns")
            hsb.grid(row=1, column=0, sticky="ew")
            self._border.rowconfigure(0, weight=1)
            self._border.columnconfigure(0, weight=1)
        else:
            # Pack layout when only vertical scrollbar.
            vsb.pack(side="right", fill="y")
            self.tree.pack(side="left", fill="both", expand=True)

        # Event wiring.
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-Button-1>", self._on_tree_double_click)
        self.tree.bind("<Delete>", self._on_delete_key)
        self.tree.bind("<BackSpace>", self._on_delete_key)
        # Clicking anywhere in the table makes it the active panel; the
        # app installs a handler via FocusIn on the inner Treeview.

    # ------------------------------------------------------------------ #
    # Public API: rows
    # ------------------------------------------------------------------ #

    def set_rows(self, items: Iterable[T]) -> None:
        """Replace all rows. Preserves the current sort if any."""
        self._items = {self._get_id(it): it for it in items}
        self._refresh_rows()

    def update_row(self, item: T) -> None:
        """Update a single row in place (e.g. after toggling display)."""
        rid = self._get_id(item)
        self._items[rid] = item
        iid = str(rid)
        if self.tree.exists(iid):
            self.tree.item(iid, values=self._get_values(item))

    def remove_row(self, row_id: int) -> None:
        """Remove a row (e.g. on delete commit). No-op if not present."""
        self._items.pop(row_id, None)
        iid = str(row_id)
        if self.tree.exists(iid):
            self.tree.delete(iid)

    def get_item(self, row_id: int) -> T | None:
        return self._items.get(row_id)

    # ------------------------------------------------------------------ #
    # Public API: selection
    # ------------------------------------------------------------------ #

    @property
    def selected_id(self) -> int | None:
        sel = self.tree.selection()
        if not sel:
            return None
        try:
            return int(sel[0])
        except ValueError:
            return None

    def select_id(self, row_id: int, *, see: bool = True) -> bool:
        """Programmatically select the given row. Returns False if it
        isn't currently in the table."""
        iid = str(row_id)
        if not self.tree.exists(iid):
            return False
        self.tree.selection_set(iid)
        self.tree.focus(iid)
        if see:
            self.tree.see(iid)
        return True

    # ------------------------------------------------------------------ #
    # Public API: active state
    # ------------------------------------------------------------------ #

    def set_active(self, active: bool) -> None:
        """Toggle the active-border highlight. When becoming active,
        also grab keyboard focus so arrow keys / delete go to this
        table."""
        color = _BORDER_ACTIVE if active else _BORDER_INACTIVE
        self._border.configure(
            highlightbackground=color, highlightcolor=color
        )
        if active:
            self.tree.focus_set()
            # If nothing is selected yet, auto-select the first row so
            # arrow keys have something to start from.
            if not self.tree.selection():
                children = self.tree.get_children()
                if children:
                    self.tree.selection_set(children[0])
                    self.tree.focus(children[0])

    # ------------------------------------------------------------------ #
    # Internals: rendering & sorting
    # ------------------------------------------------------------------ #

    def _refresh_rows(self) -> None:
        """Rebuild Treeview content from `self._items`, applying current
        sort. Preserves selection by id where possible."""
        prev_sel = self.selected_id

        items = list(self._items.values())
        if self._sort_col is not None:
            col = next(
                (c for c in self._columns if c.key == self._sort_col),
                None,
            )
            if col is not None:
                if col.sort_key is not None:
                    keyfn = col.sort_key
                else:
                    col_idx = [c.key for c in self._columns].index(col.key)
                    keyfn = lambda it, i=col_idx: self._get_values(it)[i]
                items.sort(key=keyfn, reverse=self._sort_descending)

        # Clear and refill.
        self.tree.delete(*self.tree.get_children())
        for it in items:
            rid = self._get_id(it)
            self.tree.insert(
                "",
                "end",
                iid=str(rid),
                values=self._get_values(it),
            )

        # Restore selection if the row is still present.
        if prev_sel is not None and self.tree.exists(str(prev_sel)):
            self.tree.selection_set(str(prev_sel))
            self.tree.focus(str(prev_sel))

    def _on_header_click(self, col_key: str) -> None:
        # Toggle direction if same column, else default to ascending.
        if self._sort_col == col_key:
            self._sort_descending = not self._sort_descending
        else:
            self._sort_col = col_key
            self._sort_descending = False

        # Update header glyphs.
        for col in self._columns:
            text = col.heading
            if col.key == self._sort_col:
                text += (
                    _SORT_DESC_GLYPH
                    if self._sort_descending
                    else _SORT_ASC_GLYPH
                )
            self.tree.heading(col.key, text=text)

        self._refresh_rows()

    # ------------------------------------------------------------------ #
    # Internals: events
    # ------------------------------------------------------------------ #

    def _on_tree_select(self, _event: tk.Event) -> None:
        rid = self.selected_id
        if rid is not None and self.on_select is not None:
            self.on_select(rid)

    def _on_tree_double_click(self, _event: tk.Event) -> None:
        rid = self.selected_id
        if rid is not None and self.on_double_click is not None:
            self.on_double_click(rid)

    def _on_delete_key(self, _event: tk.Event) -> str:
        rid = self.selected_id
        if rid is not None and self.on_delete is not None:
            self.on_delete(rid)
        return "break"  # prevent any default Tk handling

    def _on_filter_submit(self, _event: tk.Event) -> str:
        if self._filter_var is None:
            return "break"
        text = self._filter_var.get().strip()
        if not text:
            return "break"
        try:
            target = int(text)
        except ValueError:
            return "break"
        self.select_id(target)
        self.tree.focus_set()
        return "break"
