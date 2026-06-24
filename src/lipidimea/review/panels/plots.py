"""
lipidimea.review.panels.plots
=============================

Middle-column plot stack: four stacked matplotlib figures (MS1, XIC,
ATD, MS2), each with its own navigation toolbar (zoom / pan / home /
save) and -- on MS1 and MS2 -- a hover tooltip.

The widget exposes a single `redraw` method that takes the current
state and updates all four plots plus rebuilds the hover locators so
they close over the freshest data.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Iterable
from tkinter import ttk

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk,
)
from matplotlib.figure import Figure

from .. import plotting
from ..hover import HoverTooltip, make_ms1_locator, make_ms2_locator
from ..models import GroupView, LipidAnnotation


# ---------------------------------------------------------------------------
# Helper: one (canvas + toolbar) cell stacked vertically.
# ---------------------------------------------------------------------------


class _PlotCell(ttk.Frame):
    """A single plot panel: matplotlib canvas above, nav toolbar below.

    The toolbar's parent must be a Tk widget (NavigationToolbar2Tk
    requires `pack`-style placement on its own frame), so we give it a
    dedicated sub-frame.
    """

    def __init__(self, master: tk.Widget, *, figsize: tuple[float, float]) -> None:
        super().__init__(master)

        self.figure = Figure(figsize=figsize, dpi=100, layout="constrained")
        self.ax = self.figure.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.pack(side="top", fill="both", expand=True)

        toolbar_frame = ttk.Frame(self)
        toolbar_frame.pack(side="bottom", fill="x")
        self.toolbar = NavigationToolbar2Tk(
            self.canvas, toolbar_frame, pack_toolbar=False
        )
        self.toolbar.update()
        self.toolbar.pack(side="left", fill="x")

    def draw(self) -> None:
        self.canvas.draw_idle()


# ---------------------------------------------------------------------------
# PlotStackPanel
# ---------------------------------------------------------------------------


class PlotStackPanel(ttk.Frame):
    """Four-plot stack with hover tooltips on MS1 and MS2.

    Public API
    ----------
    redraw(view, displayed_ids, active_annotation) : update all four
        plots and rebuild hover locators.
    clear() : blank all plots (used when no group is selected).
    """

    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master)

        # Each plot gets a roughly equal vertical share.
        self._ms1 = _PlotCell(self, figsize=(4.0, 2.0))
        self._xic = _PlotCell(self, figsize=(4.0, 2.0))
        self._atd = _PlotCell(self, figsize=(4.0, 2.0))
        self._ms2 = _PlotCell(self, figsize=(4.0, 2.0))

        for cell in (self._ms1, self._xic, self._atd, self._ms2):
            cell.pack(side="top", fill="both", expand=True, padx=2, pady=2)

        # Hover tooltips on MS1 and MS2 only.
        self._hover_ms1 = HoverTooltip(self._ms1.ax)
        self._hover_ms2 = HoverTooltip(self._ms2.ax)

        # Static labels so empty plots aren't unlabeled.
        self._apply_static_titles()

    # ------------------------------------------------------------------ #
    # Drawing
    # ------------------------------------------------------------------ #

    def redraw(
        self,
        view: GroupView | None,
        displayed_ids: Iterable[int] = (),
        *,
        active_annotation: LipidAnnotation | None = None,
    ) -> None:
        """Update all four plots and rebuild hover locators.

        Pass `view=None` to blank everything (equivalent to `clear()`).
        """
        if view is None:
            self.clear()
            return

        drawn = plotting.plot_all(
            ax_ms1=self._ms1.ax,
            ax_xic=self._xic.ax,
            ax_atd=self._atd.ax,
            ax_ms2=self._ms2.ax,
            view=view,
            displayed_ids=displayed_ids,
            active_annotation=active_annotation,
        )

        # Rebuild hover locators against the freshly drawn data.
        self._hover_ms1.set_locator(
            make_ms1_locator(drawn.ms1, self._ms1.ax)
        )
        self._hover_ms2.set_locator(
            make_ms2_locator(
                drawn.ms2,
                self._ms2.ax,
                active_annotation=active_annotation,
            )
        )

        self._apply_static_titles()
        self._draw_all()

    def clear(self) -> None:
        """Blank all four plots and disable hover."""
        for cell in (self._ms1, self._xic, self._atd, self._ms2):
            cell.ax.clear()
        self._hover_ms1.set_locator(None)
        self._hover_ms2.set_locator(None)
        self._apply_static_titles()
        self._draw_all()

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def shutdown(self) -> None:
        """Disconnect hover handlers. Called on app teardown to avoid
        callbacks firing into a half-destroyed widget tree."""
        self._hover_ms1.disconnect()
        self._hover_ms2.disconnect()

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _draw_all(self) -> None:
        for cell in (self._ms1, self._xic, self._atd, self._ms2):
            cell.draw()

    def _apply_static_titles(self) -> None:
        """Add a small title to each axis so empty plots are still
        identifiable. Titles are cheap and survive `ax.clear()` only if
        re-applied, so we call this after every clear/redraw."""
        self._ms1.ax.set_title("MS1", fontsize=9, loc="left")
        self._xic.ax.set_title("XIC", fontsize=9, loc="left")
        self._atd.ax.set_title("ATD", fontsize=9, loc="left")
        self._ms2.ax.set_title("MS2", fontsize=9, loc="left")
        