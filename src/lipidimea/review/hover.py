"""
lipidimea.review.hover
======================

Generic Matplotlib hover-tooltip helper plus locator factories for the
MS1 and MS2 panels.

Design
------
A `HoverTooltip` listens to `motion_notify_event` on a given Axes and
delegates "what's near the cursor?" to a `Locator` callable supplied by
the panel widget. The locator returns an `(x, y, text)` tuple in data
coords, or None to hide the tooltip. This separation keeps the tooltip
class agnostic about what's being hovered over -- the MS2 locator can
do annotation-aware fragment matching, the MS1 locator just snaps to
the nearest peak, and so on.

Locators are stateless w.r.t. the Axes view: they should be rebuilt by
the panel widget whenever the underlying data changes (new GroupView
loaded, display checkboxes toggled, active annotation changes).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

import numpy as np
from matplotlib.axes import Axes
from matplotlib.backend_bases import MouseEvent

from .models import LipidAnnotation
from .plotting import MS1Drawn, MS2Drawn, match_fragment


#: Default cursor capture radius in display pixels.
DEFAULT_PIXEL_RADIUS: int = 20


# ---------------------------------------------------------------------------
# Locator protocol
# ---------------------------------------------------------------------------


class Locator(Protocol):
    """Callable that maps a mouse event to a tooltip placement, or None.

    Returns (data_x, data_y, text) -- the tooltip is anchored at
    (data_x, data_y) in the axis's data coords and shows `text`.
    """

    def __call__(
        self, event: MouseEvent
    ) -> tuple[float, float, str] | None: ...


# ---------------------------------------------------------------------------
# HoverTooltip
# ---------------------------------------------------------------------------


class HoverTooltip:
    """Single-axis hover annotation managed by a locator callback.

    Lifetime: created once per Axes by the panel widget. The locator can
    be swapped at any time via `set_locator` (e.g. when the active lipid
    annotation changes, the panel installs a fresh MS2 locator that
    closes over the new annotation).
    """

    def __init__(
        self,
        ax: Axes,
        locator: Locator | None = None,
    ) -> None:
        self.ax = ax
        self.canvas = ax.figure.canvas
        self._locator: Locator | None = locator

        self._annot = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(10, 10),
            textcoords="offset points",
            bbox={
                "boxstyle": "round,pad=0.3",
                "fc": "#ffffe0",
                "ec": "#888888",
                "lw": 0.5,
                "alpha": 0.9,
            },
            fontsize=8,
            zorder=10,
        )
        self._annot.set_visible(False)

        self._cid_motion = self.canvas.mpl_connect(
            "motion_notify_event", self._on_move
        )
        self._cid_leave = self.canvas.mpl_connect(
            "axes_leave_event", self._on_leave
        )

    # ------------------------------------------------------------------ #

    def set_locator(self, locator: Locator | None) -> None:
        """Replace the locator. Pass None to disable hover (tooltip hides)."""
        self._locator = locator
        if locator is None and self._annot.get_visible():
            self._annot.set_visible(False)
            self.canvas.draw_idle()

    def disconnect(self) -> None:
        """Unhook from canvas events. Called on app teardown."""
        self.canvas.mpl_disconnect(self._cid_motion)
        self.canvas.mpl_disconnect(self._cid_leave)

    # ------------------------------------------------------------------ #

    def _on_move(self, event: MouseEvent) -> None:
        if self._locator is None or event.inaxes is not self.ax:
            if self._annot.get_visible():
                self._annot.set_visible(False)
                self.canvas.draw_idle()
            return

        result = self._locator(event)
        if result is None:
            if self._annot.get_visible():
                self._annot.set_visible(False)
                self.canvas.draw_idle()
            return

        x, y, text = result
        self._annot.xy = (x, y)
        self._annot.set_text(text)
        self._annot.set_visible(True)
        self.canvas.draw_idle()

    def _on_leave(self, event: MouseEvent) -> None:
        if self._annot.get_visible():
            self._annot.set_visible(False)
            self.canvas.draw_idle()


# ---------------------------------------------------------------------------
# Coord helpers
# ---------------------------------------------------------------------------


def _pixel_x_radius_in_data(ax: Axes, pixel_radius: float) -> float:
    """Return how many data-x units correspond to `pixel_radius` display
    pixels at the current axis view."""
    inv = ax.transData.inverted()
    (x0, _), (x1, _) = inv.transform([(0, 0), (pixel_radius, 0)])
    return abs(x1 - x0)


# ---------------------------------------------------------------------------
# Locator factories
# ---------------------------------------------------------------------------


def make_ms1_locator(
    drawn: MS1Drawn,
    ax: Axes,
    *,
    pixel_radius: int = DEFAULT_PIXEL_RADIUS,
) -> Locator:
    """Build an MS1 locator that snaps to the highest-intensity peak
    within `pixel_radius` of the cursor x-position.

    If no points are drawn, returns a no-op locator.
    """

    if not drawn.traces:
        return lambda event: None

    mzs = np.concatenate([arr[0] for arr in drawn.traces.values()])
    ints = np.concatenate([arr[1] for arr in drawn.traces.values()])
    order = np.argsort(mzs)
    mzs = mzs[order]
    ints = ints[order]

    def locate(event: MouseEvent) -> tuple[float, float, str] | None:
        if event.xdata is None:
            return None
        radius = _pixel_x_radius_in_data(ax, pixel_radius)
        # Window of points within radius of the cursor x.
        lo = np.searchsorted(mzs, event.xdata - radius, side="left")
        hi = np.searchsorted(mzs, event.xdata + radius, side="right")
        if lo == hi:
            return None
        # Snap to the highest-intensity peak in the window.
        local_ints = ints[lo:hi]
        idx = lo + int(np.argmax(local_ints))
        x, y = float(mzs[idx]), float(ints[idx])
        return x, y, f"m/z {x:.4f}"

    return locate


def make_ms2_locator(
    drawn: MS2Drawn,
    ax: Axes,
    *,
    active_annotation: LipidAnnotation | None = None,
    pixel_radius: int = DEFAULT_PIXEL_RADIUS,
) -> Locator:
    """Build an MS2 locator that snaps to the nearest bar within
    `pixel_radius` of the cursor x-position.

    Bars above the axis (DIA) and below (DDA mirror) are searched
    separately based on cursor y-sign so the tooltip reflects what the
    user is actually pointing at. When an active lipid annotation is
    supplied, the tooltip text includes the matching annotated fragment
    label (and a "[diagnostic]" tag if applicable).
    """
    # Pre-build sorted (mz, intensity) arrays for each side.
    def _prep(arr: np.ndarray | None) -> tuple[np.ndarray, np.ndarray] | None:
        if arr is None or arr.shape[1] == 0:
            return None
        mz = arr[0]
        intensity = arr[1]
        order = np.argsort(mz)
        return mz[order], intensity[order]

    dia_combined: tuple[np.ndarray, np.ndarray] | None
    if drawn.dia_peaks:
        dia_mz = np.concatenate([a[0] for a in drawn.dia_peaks.values()])
        dia_int = np.concatenate([a[1] for a in drawn.dia_peaks.values()])
        order = np.argsort(dia_mz)
        dia_combined = (dia_mz[order], dia_int[order])
    else:
        dia_combined = None

    dda_combined = _prep(drawn.dda_peaks)

    if dia_combined is None and dda_combined is None:
        return lambda event: None

    def _nearest(
        mzs: np.ndarray, ints: np.ndarray, x: float, radius: float
    ) -> tuple[float, float] | None:
        lo = np.searchsorted(mzs, x - radius, side="left")
        hi = np.searchsorted(mzs, x + radius, side="right")
        if lo == hi:
            return None
        local_mz = mzs[lo:hi]
        idx = lo + int(np.argmin(np.abs(local_mz - x)))
        return float(mzs[idx]), float(ints[idx])

    def _format(mz: float, *, mirrored: bool) -> str:
        text = f"m/z {mz:.4f}"
        if active_annotation is not None and not mirrored:
            # Fragment annotations apply only to DIA peaks.
            frag = match_fragment(mz, active_annotation)
            if frag is not None:
                tag = " [diagnostic]" if frag.diagnostic else ""
                text += f"\n{frag.label}{tag}"
        return text

    def locate(event: MouseEvent) -> tuple[float, float, str] | None:
        if event.xdata is None or event.ydata is None:
            return None
        radius = _pixel_x_radius_in_data(ax, pixel_radius)

        # Choose side based on cursor y-sign: above 0 -> DIA, below -> DDA.
        if event.ydata >= 0 and dia_combined is not None:
            hit = _nearest(*dia_combined, event.xdata, radius)
            if hit is None:
                return None
            mz, intensity = hit
            return mz, intensity, _format(mz, mirrored=False)

        if event.ydata < 0 and dda_combined is not None:
            hit = _nearest(*dda_combined, event.xdata, radius)
            if hit is None:
                return None
            mz, intensity = hit
            # DDA bars are drawn at -intensity; anchor tooltip there.
            return mz, -intensity, _format(mz, mirrored=True)

        return None

    return locate


# ---------------------------------------------------------------------------
# Convenience wiring
# ---------------------------------------------------------------------------


def install_default_hovers(
    *,
    ax_ms1: Axes,
    ax_ms2: Axes,
) -> tuple[HoverTooltip, HoverTooltip]:
    """Create HoverTooltip instances on the MS1 and MS2 axes with no
    locators yet attached. The plot panel widget is responsible for
    calling `set_locator` after each redraw with locators built from the
    fresh `MS1Drawn` / `MS2Drawn` records.
    """
    return HoverTooltip(ax_ms1), HoverTooltip(ax_ms2)