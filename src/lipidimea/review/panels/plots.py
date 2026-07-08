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
from matplotlib import rcParams

from .. import plotting
from ..hover import HoverTooltip, make_ms1_locator, make_ms2_locator
from ..models import GroupView, LipidAnnotation


# ---------------------------------------------------------------------------
# constants
# --------------------------------------------------------------------------- 

#: Matplotlib's baseline DPI. All our font/line sizes were tuned at this
#: value.
_BASE_DPI: int = 100

#: Render DPI for on-screen figures. Higher = crisper on HiDPI displays.
#: Font and line sizes are automatically rescaled to preserve visual
#: layout (see _apply_hidpi_scaling).
PLOT_DPI: int = 100

rcParams["font.size"] = 7


# ---------------------------------------------------------------------------
# Helper: a mini toolbar, the default matplotlib one is not so pleasing
# --------------------------------------------------------------------------- 

class _MiniToolbar(ttk.Frame):
    """Compact replacement for NavigationToolbar2Tk with just the
    essential actions."""

    def __init__(self, master: tk.Widget, canvas: FigureCanvasTkAgg) -> None:
        super().__init__(master)
        # Build a hidden real toolbar to delegate to.
        self._real = NavigationToolbar2Tk(canvas, master, pack_toolbar=False)
        self._real.pack_forget()

        style = {"width": 3, "padding": 0}
        ttk.Button(self, text="⌂", command=self._real.home, **style).pack(side="left")
        ttk.Button(self, text="←", command=self._real.back, **style).pack(side="left")
        ttk.Button(self, text="→", command=self._real.forward, **style).pack(side="left")
        ttk.Button(self, text="✥", command=self._real.pan, **style).pack(side="left")
        ttk.Button(self, text="⊕", command=self._real.zoom, **style).pack(side="left")
        ttk.Button(self, text="💾", command=self._real.save_figure, **style).pack(side="left")


# ---------------------------------------------------------------------------
# Helper: one (canvas + toolbar) cell stacked vertically.
# ---------------------------------------------------------------------------


class _PlotCell(ttk.Frame):
    """A single plot panel: matplotlib canvas above, nav toolbar below.

    The toolbar's parent must be a Tk widget (NavigationToolbar2Tk
    requires `pack`-style placement on its own frame), so we give it a
    dedicated sub-frame.
    """

    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master)

        self.figure = Figure(figsize=(4, 2), dpi=PLOT_DPI, layout="constrained")
        self.ax = self.figure.add_subplot(111)

        toolbar_frame = ttk.Frame(self)
        toolbar_frame.pack(side="bottom", fill="x")

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

        self.toolbar = _MiniToolbar(toolbar_frame, self.canvas)
        self.toolbar.pack(side="left")

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
        self._ms1 = _PlotCell(self)
        self._xic = _PlotCell(self)
        self._atd = _PlotCell(self)
        self._ms2 = _PlotCell(self)

        # Grid layout with uniform row weights: all four plots always
        # get equal vertical share, even when the window is too short
        # to satisfy their natural size requests. (pack + expand=True
        # respects natural size first and starves the last widget.)
        cells = (self._ms1, self._xic, self._atd, self._ms2)
        for row, cell in enumerate(cells):
            cell.grid(
                row=row, column=0, sticky="nsew", padx=2, pady=2
            )
            self.rowconfigure(row, weight=1, uniform="plots")
        self.columnconfigure(0, weight=1)

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

        # Redraw wiped the axes; put the hover annotations back.
        self._hover_ms1.reattach()
        self._hover_ms2.reattach()

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
        self._hover_ms1.reattach()
        self._hover_ms2.reattach()
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
        self._ms1.ax.set_title("MS1", loc="right")
        self._xic.ax.set_title("XIC", loc="right")
        self._atd.ax.set_title("ATD", loc="right")
        self._ms2.ax.set_title("MS2", loc="right")
        