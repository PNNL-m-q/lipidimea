"""
lipidimea.review.app
====================

Main Tk application window. Owns one Session, the four panel widgets,
and the wiring between them.

Layout
------
    +--------------------------------------------------------------+
    | [load] [save] [export]                                       |
    +--------+-------------------------+---------------------------+
    |        |                         |    feature panel          |
    | group  |     plot stack          +---------------------------+
    | panel  |     (MS1/XIC/ATD/MS2)   |    annotation panel       |
    |        |                         |                           |
    +--------+-------------------------+---------------------------+
    | status: <db path> | dirty: 0g/0f/0a | active: group          |
    +--------------------------------------------------------------+

Layout uses ttk.PanedWindow so users can drag the column / row
dividers.

Active-panel concept
--------------------
At any time exactly one of the three table panels is "active" -- it
has keyboard focus and its border is highlighted. The active panel is
the target of `Delete`/`Backspace` (and `d` for the feature panel),
and the `g`/`f`/`l` keybinds switch which panel is active.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import export
from .session import Session
from .panels.annotations import AnnotationPanel
from .panels.features import FeaturePanel
from .panels.groups import GroupPanel
from .panels.plots import PlotStackPanel


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_APP_TITLE = "lipidimea-review"

_PANEL_NAMES = ("group", "feature", "lipid")


# ---------------------------------------------------------------------------
# ReviewApp
# ---------------------------------------------------------------------------


class ReviewApp(tk.Tk):
    """Top-level application window."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        super().__init__()
        self.title(_APP_TITLE)
        self.geometry("1600x1000")
        self.minsize(1600, 1000)

        # -- state ------------------------------------------------------
        self.session: Session | None = None
        self._active_panel: str = "group"
        self._active_annotation_id: int | None = None

        # -- build ------------------------------------------------------
        self._build_toolbar()
        self._build_statusbar()
        self._build_main()

        # -- wire -------------------------------------------------------
        self._wire_panel_callbacks()
        self._wire_global_bindings()

        # -- close handling --------------------------------------------
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # -- initial state ---------------------------------------------
        self._update_button_state()
        self._refresh_status()
        self._set_active_panel("group", grab_focus=False)

        if db_path is not None:
            self._load_db(Path(db_path))

    # ================================================================== #
    # Construction
    # ================================================================== #

    def _build_toolbar(self) -> None:
        bar = ttk.Frame(self, padding=(4, 4))
        bar.pack(side="top", fill="x")

        self._btn_load = ttk.Button(
            bar, text="load results", command=self._on_load_results
        )
        self._btn_save = ttk.Button(
            bar, text="save results", command=self._on_save_results
        )
        self._btn_export = ttk.Button(
            bar, text="export results", command=self._on_export_results
        )
        self._btn_load.pack(side="left", padx=2)
        self._btn_save.pack(side="left", padx=2)
        self._btn_export.pack(side="left", padx=2)

    def _build_main(self) -> None:
        outer = ttk.PanedWindow(self, orient="horizontal")
        outer.pack(side="top", fill="both", expand=True, padx=4, pady=4)

        self.group_panel = GroupPanel(outer)
        outer.add(self.group_panel, weight=2)

        self.plot_panel = PlotStackPanel(outer)
        outer.add(self.plot_panel, weight=3)

        right = ttk.PanedWindow(outer, orient="vertical")
        outer.add(right, weight=3)

        self.feature_panel = FeaturePanel(right)
        right.add(self.feature_panel, weight=1)

        self.annotation_panel = AnnotationPanel(right)
        right.add(self.annotation_panel, weight=1)

        # Set initial sash positions once widgets are realized.
        self._outer_paned = outer
        self._right_paned = right
        self.after(0, self._apply_initial_sash_positions)

    def _apply_initial_sash_positions(self) -> None:
        # Horizontal: group | plots | right-stack
        # Fractions of total width.
        w = self._outer_paned.winfo_width()
        self._outer_paned.sashpos(0, int(w * 0.20))   # end of group panel
        self._outer_paned.sashpos(1, int(w * 0.70))   # end of plot panel

        # Vertical: features | annotations
        h = self._right_paned.winfo_height()
        self._right_paned.sashpos(0, int(h * 0.50))   # split between them

    def _build_statusbar(self) -> None:
        self._status_var = tk.StringVar(value="no database loaded")
        bar = ttk.Frame(self, padding=(4, 2))
        bar.pack(side="bottom", fill="x")
        ttk.Label(bar, textvariable=self._status_var, anchor="w").pack(
            side="left", fill="x", expand=True
        )

    # ================================================================== #
    # Wiring
    # ================================================================== #

    def _wire_panel_callbacks(self) -> None:
        # Selection
        self.group_panel.on_select = self._on_group_selected
        self.feature_panel.on_select = self._on_feature_selected
        self.annotation_panel.on_select = self._on_annotation_selected

        # Deletion (Delete/Backspace inside each panel)
        self.group_panel.on_delete = self._on_group_delete
        self.feature_panel.on_delete = self._on_feature_delete
        self.annotation_panel.on_delete = self._on_annotation_delete

        # Feature display toggle
        self.feature_panel.on_toggle_display = self._on_feature_display_toggled

        # Active-panel tracking via FocusIn on each Treeview.
        self.group_panel.tree.bind(
            "<FocusIn>",
            lambda _e: self._set_active_panel("group", grab_focus=False),
            add="+",
        )
        self.feature_panel.tree.bind(
            "<FocusIn>",
            lambda _e: self._set_active_panel("feature", grab_focus=False),
            add="+",
        )
        self.annotation_panel.tree.bind(
            "<FocusIn>",
            lambda _e: self._set_active_panel("lipid", grab_focus=False),
            add="+",
        )

    def _wire_global_bindings(self) -> None:
        # Panel-switch keybinds. Bound on the toplevel so they fire from
        # anywhere -- including when focus is on a Treeview that would
        # otherwise consume the keystroke as a search.
        # We use bind_all but guard against firing when a text-entry
        # widget is focused (e.g. the ID filter Entry).
        self.bind_all("g", self._kb_panel_switch("group"))
        self.bind_all("f", self._kb_panel_switch("feature"))
        self.bind_all("l", self._kb_panel_switch("lipid"))
        self.bind_all("G", self._kb_panel_switch("group"))
        self.bind_all("F", self._kb_panel_switch("feature"))
        self.bind_all("L", self._kb_panel_switch("lipid"))

        # Save / export / undo shortcuts.
        self.bind_all("<Control-s>", lambda _e: self._on_save_results())
        self.bind_all("<Control-S>", lambda _e: self._on_save_results())
        self.bind_all("<Control-e>", lambda _e: self._on_export_results())
        self.bind_all("<Control-E>", lambda _e: self._on_export_results())
        self.bind_all("<Control-z>", lambda _e: self._on_undo())
        self.bind_all("<Control-Z>", lambda _e: self._on_undo())

    def _kb_panel_switch(self, name: str):
        """Build a keybind handler that switches active panel, but only
        when focus isn't on a text-entry widget (Entry / Spinbox)."""
        def handler(event: tk.Event) -> str | None:
            w = event.widget
            try:
                cls = w.winfo_class()
            except Exception:
                cls = ""
            if cls in ("TEntry", "Entry", "TSpinbox", "Spinbox", "Text"):
                return None  # let the keystroke through to the entry
            self._set_active_panel(name, grab_focus=True)
            return "break"
        return handler

    # ================================================================== #
    # Active-panel state
    # ================================================================== #

    def _set_active_panel(self, name: str, *, grab_focus: bool) -> None:
        if name not in _PANEL_NAMES:
            return
        self._active_panel = name
        self.group_panel.set_active(name == "group")
        self.feature_panel.set_active(name == "feature")
        self.annotation_panel.set_active(name == "lipid")
        if grab_focus:
            target = {
                "group": self.group_panel,
                "feature": self.feature_panel,
                "lipid": self.annotation_panel,
            }[name]
            target.tree.focus_set()
        self._refresh_status()

    # ================================================================== #
    # Group selection -> populate everything else
    # ================================================================== #

    def _on_group_selected(self, group_id: int) -> None:
        if self.session is None:
            return
        try:
            view = self.session.get_group_view(group_id)
        except Exception as e:
            messagebox.showerror(
                "Load error",
                f"failed to load group {group_id}:\n{e}",
                parent=self,
            )
            self.plot_panel.clear()
            self.feature_panel.set_rows([])
            self.annotation_panel.set_rows([])
            return

        # Refresh dependent panels.
        self.feature_panel.set_rows(view.features.values())
        self.annotation_panel.set_rows(view.annotations.values())

        # Active-annotation reset on each group change.
        self._active_annotation_id = None

        self._redraw_plots()
        self._refresh_status()

    def _on_feature_selected(self, _feature_id: int) -> None:
        # Selection in the feature panel doesn't change what's plotted
        # (display checkbox does that); nothing to do.
        pass

    def _on_annotation_selected(self, annotation_id: int) -> None:
        ann = self.annotation_panel.get_item(annotation_id)
        if ann is None or ann.deleted:
            self._active_annotation_id = None
        else:
            self._active_annotation_id = annotation_id
        self._redraw_plots()

    def _on_feature_display_toggled(self, _feature_id: int) -> None:
        self._redraw_plots()

    # ================================================================== #
    # Deletion handlers
    # ================================================================== #

    def _on_group_delete(self, group_id: int) -> None:
        if self.session is None:
            return
        self.session.delete_group(group_id)
        # Repaint the row with deleted styling, leave it visible.
        item = self.group_panel.get_item(group_id)
        if item is not None:
            self.group_panel.update_row(item)
        self._update_button_state()
        self._refresh_status()

    def _on_feature_delete(self, feature_id: int) -> None:
        if self.session is None:
            return
        self.session.delete_feature(feature_id)
        item = self.feature_panel.get_item(feature_id)
        if item is not None:
            self.feature_panel.update_row(item)
        # Deleted feature drops out of the displayed traces.
        self._redraw_plots()
        self._update_button_state()
        self._refresh_status()

    def _on_annotation_delete(self, annotation_id: int) -> None:
        if self.session is None:
            return
        self.session.delete_annotation(annotation_id)
        item = self.annotation_panel.get_item(annotation_id)
        if item is not None:
            self.annotation_panel.update_row(item)
        # If it was the active annotation, clear it and redraw MS2.
        if self._active_annotation_id == annotation_id:
            self._active_annotation_id = None
            self._redraw_plots()
        self._update_button_state()
        self._refresh_status()

    # ================================================================== #
    # Undo
    # ================================================================== #

    def _on_undo(self) -> None:
        if self.session is None:
            return
        op = self.session.undo_last_deletion()
        if op is None:
            return
        # Repaint affected row(s); for groups & annotations the row may
        # not be in the currently-displayed group, in which case the
        # update_row call is a no-op.
        match op.kind:
            case "group":
                item = self.group_panel.get_item(op.id)
                if item is not None:
                    self.group_panel.update_row(item)
            case "feature":
                item = self.feature_panel.get_item(op.id)
                if item is not None:
                    self.feature_panel.update_row(item)
                self._redraw_plots()
            case "annotation":
                item = self.annotation_panel.get_item(op.id)
                if item is not None:
                    self.annotation_panel.update_row(item)
        self._update_button_state()
        self._refresh_status()

    # ================================================================== #
    # Plot redraw helper
    # ================================================================== #

    def _redraw_plots(self) -> None:
        if self.session is None:
            self.plot_panel.clear()
            return
        gid = self.group_panel.selected_id
        if gid is None:
            self.plot_panel.clear()
            return
        try:
            view = self.session.get_group_view(gid)
        except Exception:
            self.plot_panel.clear()
            return

        displayed_ids = [
            f.id
            for f in view.features.values()
            if f.display and not f.deleted
        ]
        active = None
        if self._active_annotation_id is not None:
            ann = view.annotations.get(self._active_annotation_id)
            if ann is not None and not ann.deleted:
                active = ann

        self.plot_panel.redraw(
            view, displayed_ids, active_annotation=active
        )

    # ================================================================== #
    # Toolbar actions
    # ================================================================== #

    def _on_load_results(self) -> None:
        if not self._confirm_discard_if_dirty():
            return
        path = filedialog.askopenfilename(
            parent=self,
            title="Open results database",
            filetypes=[("SQLite database", "*.db *.sqlite *.sqlite3"),
                       ("All files", "*.*")],
        )
        if not path:
            return
        self._load_db(Path(path))

    def _on_save_results(self) -> None:
        if self.session is None or not self.session.dirty:
            return
        ng, nf, na = self.session.n_pending_deletions
        if not messagebox.askyesno(
            "Commit deletions",
            f"Permanently delete:\n"
            f"  {ng} feature group(s)\n"
            f"  {nf} feature(s)\n"
            f"  {na} annotation(s)\n\n"
            f"This cannot be undone.",
            parent=self,
        ):
            return
        try:
            self.session.commit()
        except Exception as e:
            messagebox.showerror(
                "Commit error", f"failed to commit deletions:\n{e}",
                parent=self,
            )
            return
        # Rebuild group panel from the now-pruned in-memory dict.
        self.group_panel.set_rows(self.session.iter_live_groups())
        # The previously selected group may have been deleted; if not,
        # its dependent panels are now stale (its cached view was
        # cleared). Easiest: clear right side and plots.
        self.feature_panel.set_rows([])
        self.annotation_panel.set_rows([])
        self.plot_panel.clear()
        self._active_annotation_id = None
        self._update_button_state()
        self._refresh_status()

    def _on_export_results(self) -> None:
        if self.session is None:
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Export retained results to CSV",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            n = export.export_csv(self.session, Path(path))
        except Exception as e:
            messagebox.showerror(
                "Export error", f"failed to export:\n{e}", parent=self,
            )
            return
        messagebox.showinfo(
            "Export complete",
            f"Wrote {n} rows to:\n{path}",
            parent=self,
        )

    # ================================================================== #
    # DB load / close
    # ================================================================== #

    def _load_db(self, path: Path) -> None:
        # Close prior session if any.
        if self.session is not None:
            self.session.close()
            self.session = None

        try:
            self.session = Session(path)
        except Exception as e:
            messagebox.showerror(
                "Load error", f"failed to open {path}:\n{e}", parent=self,
            )
            self.session = None
            self._update_button_state()
            self._refresh_status()
            return

        # Repopulate everything.
        self.group_panel.set_rows(self.session.iter_live_groups())
        self.feature_panel.set_rows([])
        self.annotation_panel.set_rows([])
        self.plot_panel.clear()
        self._active_annotation_id = None
        self.title(f"{_APP_TITLE} — {path.name}")
        self._update_button_state()
        self._refresh_status()
        self._set_active_panel("group", grab_focus=True)

    def _confirm_discard_if_dirty(self) -> bool:
        """Return True if it's OK to proceed with an action that would
        discard pending deletions (Load, app close)."""
        if self.session is None or not self.session.dirty:
            return True
        ng, nf, na = self.session.n_pending_deletions
        return messagebox.askyesno(
            "Discard pending deletions?",
            f"You have unsaved deletions:\n"
            f"  {ng} feature group(s)\n"
            f"  {nf} feature(s)\n"
            f"  {na} annotation(s)\n\n"
            f"Discard them and continue?",
            parent=self,
        )

    # ================================================================== #
    # Status bar / button state
    # ================================================================== #

    def _refresh_status(self) -> None:
        parts: list[str] = []
        if self.session is None:
            parts.append("no database loaded")
        else:
            parts.append(str(self.session.db_path))
            ng, nf, na = self.session.n_pending_deletions
            parts.append(f"pending: {ng}g / {nf}f / {na}a")
        parts.append(f"active: {self._active_panel}")
        self._status_var.set("   |   ".join(parts))

    def _update_button_state(self) -> None:
        loaded = self.session is not None
        dirty = loaded and self.session.dirty
        self._btn_save.configure(state=("normal" if dirty else "disabled"))
        self._btn_export.configure(state=("normal" if loaded else "disabled"))

    # ================================================================== #
    # Close
    # ================================================================== #

    def _on_close(self) -> None:
        if not self._confirm_discard_if_dirty():
            return
        try:
            self.plot_panel.shutdown()
        except Exception:
            pass
        if self.session is not None:
            self.session.close()
            self.session = None
        self.destroy()