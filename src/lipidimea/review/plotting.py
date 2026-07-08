"""
lipidimea.review.plotting
=========================

Plot drawing functions for the four panels (MS1, XIC, ATD, MS2). Each
function takes a fully populated `GroupView`, the set of feature IDs the
user has chosen to display, and an `Axes` to draw into. They clear and
redraw the axis from scratch so they can be called freely on any state
change.

These functions are pure (no Tk, no Figure-level concerns) and return
small `dataclass` records describing what was drawn -- the hover layer
uses those records to map cursor position back to data values.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field

import numpy as np
from matplotlib.axes import Axes

from .models import (
    FragmentAnnotation,
    GroupView,
    LipidAnnotation,
)


# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------

#: ppm tolerance for matching an observed MS2 peak to an annotated fragment.
FRAGMENT_MATCH_PPM: float = 20.0

#: Half-window (in DT units) around the group DT for the ATD plot.
ATD_HALF_WINDOW: float = 5.0

#: Bar width as a fraction of the MS2 x-axis span.
MS2_BAR_WIDTH_FRAC: float = 0.005

#: Style constants -- keep all in one place so they're easy to tweak.
_DIA_COLOR = "tab:blue"
_DIA_ALPHA = 0.25
_DIA_LW = 1.0
_DDA_COLOR = "#666666"
_GROUP_COLOR = "#333333"
_FRAG_DIAGNOSTIC_COLOR = "tab:red"
_FRAG_NONDIAGNOSTIC_COLOR = "tab:orange"


# ---------------------------------------------------------------------------
# Hover-support records
# ---------------------------------------------------------------------------


@dataclass
class MS1Drawn:
    """Per-feature MS1 traces drawn on an axis. Used by hover layer."""

    traces: dict[int, np.ndarray] = field(default_factory=dict)
    # feature_id -> (2, N) array (mz, intensity)


@dataclass
class MS2Drawn:
    """MS2 peak positions drawn on an axis, separated by source so the
    hover layer can label them appropriately.

    `dia_peaks[feature_id]` is a (2, N) array of (mz, intensity) for the
    DIA precursor in question (positive y).
    `dda_peaks` is a (2, N) array (mz, intensity) for the DDA mirror
    spectrum (intensities returned positive; sign is a render-time
    decision).
    """

    dia_peaks: dict[int, np.ndarray] = field(default_factory=dict)
    dda_peaks: np.ndarray | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _gaussian(x: np.ndarray, mu: float, height: float, fwhm: float) -> np.ndarray:
    """Gaussian peak parameterized by mean, height, and FWHM."""
    sigma = fwhm / (2.0 * np.sqrt(2.0 * np.log(2.0)))
    return height * np.exp(-0.5 * ((x - mu) / sigma) ** 2)


def _live_features(
    view: GroupView, displayed_ids: Iterable[int]
) -> list:
    """Return Feature objects for the given ids, filtered to non-deleted.

    Order matches the iteration order of `displayed_ids`.
    """
    out = []
    for fid in displayed_ids:
        feat = view.features.get(fid)
        if feat is not None and not feat.deleted:
            out.append(feat)
    return out


def match_fragment(
    observed_mz: float,
    annotation: LipidAnnotation,
    *,
    ppm: float = FRAGMENT_MATCH_PPM,
) -> FragmentAnnotation | None:
    """Return the closest annotated fragment within `ppm` of `observed_mz`,
    or None if no annotated fragment is in tolerance.

    Used by the MS2 hover tooltip to enrich the readout when a lipid
    annotation is the active selection.
    """
    if not annotation.fragments:
        return None
    tol = observed_mz * ppm / 1e6
    best: FragmentAnnotation | None = None
    best_diff = float("inf")
    for frag in annotation.fragments:
        diff = abs(frag.mz - observed_mz)
        if diff <= tol and diff < best_diff:
            best = frag
            best_diff = diff
    return best


# ---------------------------------------------------------------------------
# Plot functions
# ---------------------------------------------------------------------------


def plot_ms1(
    ax: Axes,
    view: GroupView,
    displayed_ids: Iterable[int],
) -> MS1Drawn:
    """Overlaid MS1 spectra for the displayed DIA precursors, with vertical
    lines at the DDA-match m/z (dotted, if any) and the group m/z (solid)."""
    ax.clear()
    drawn = MS1Drawn()

    for feat in _live_features(view, displayed_ids):
        if feat.ms1 is None or feat.ms1.shape[1] == 0:
            continue
        mz, intensity = feat.ms1
        ax.plot(
            mz, intensity,
            color=_DIA_COLOR, lw=_DIA_LW, alpha=_DIA_ALPHA,
        )
        drawn.traces[feat.id] = feat.ms1

    if view.dda is not None:
        ax.axvline(view.dda.mz, color=_DDA_COLOR, lw=1, ls=":")
    ax.axvline(view.group.mz, color=_GROUP_COLOR, lw=1)

    ax.set_xlabel("m/z")
    ax.set_ylabel("intensity")

    # scientific notation for y axis scale
    ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))

    return drawn


def plot_xic(
    ax: Axes,
    view: GroupView,
    displayed_ids: Iterable[int],
) -> None:
    """Overlaid XICs, plus a Gaussian sketch of the matched DDA peak (if
    present), plus a vertical line at the group RT."""
    ax.clear()

    for feat in _live_features(view, displayed_ids):
        if feat.xic is None or feat.xic.shape[1] == 0:
            continue
        rt, intensity = feat.xic
        ax.plot(
            rt, intensity,
            color=_DIA_COLOR, lw=_DIA_LW, alpha=_DIA_ALPHA,
        )

    dda = view.dda
    if dda is not None and dda.rt_fwhm > 0:
        dx = np.linspace(
            dda.rt - 1.5 * dda.rt_fwhm,
            dda.rt + 1.5 * dda.rt_fwhm,
            100,
        )
        dy = _gaussian(dx, dda.rt, dda.rt_pkht, dda.rt_fwhm)
        ax.plot(dx, dy, color=_DDA_COLOR, lw=1, ls=":")

    ax.axvline(view.group.rt, color=_GROUP_COLOR, lw=1)
    ax.set_xlabel("retention time")
    ax.set_ylabel("intensity")

    # scientific notation for y axis scale
    ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))


def plot_atd(
    ax: Axes,
    view: GroupView,
    displayed_ids: Iterable[int],
) -> None:
    """Overlaid ATDs with a vertical line at the group DT, x-limited to a
    window around DT."""
    ax.clear()

    for feat in _live_features(view, displayed_ids):
        if feat.atd is None or feat.atd.shape[1] == 0:
            continue
        dt, intensity = feat.atd
        ax.plot(
            dt, intensity,
            color=_DIA_COLOR, lw=_DIA_LW, alpha=_DIA_ALPHA,
        )

    ax.axvline(view.group.dt, color=_GROUP_COLOR, lw=1)
    ax.set_xlim(
        view.group.dt - ATD_HALF_WINDOW,
        view.group.dt + ATD_HALF_WINDOW,
    )
    ax.set_xlabel("drift time")
    ax.set_ylabel("intensity")

    # scientific notation for y axis scale
    ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))


def plot_ms2(
    ax: Axes,
    view: GroupView,
    displayed_ids: Iterable[int],
    *,
    active_annotation: LipidAnnotation | None = None,
) -> MS2Drawn:
    """Mirror MS2 plot: DIA precursors above the axis, DDA below.

    Deconvoluted DIA peaks are marked with a `*` glyph above the bar.
    If an active lipid annotation is supplied, its annotated fragment
    m/z values are marked with vertical guide lines (red for diagnostic,
    orange otherwise) so it's easy to see at a glance whether they line
    up with observed peaks.
    """
    ax.clear()
    drawn = MS2Drawn()
    ax.axhline(0, color="k", lw=1)

    # Determine x-axis span across all spectra so bar widths are consistent.
    all_mz: list[np.ndarray] = []
    feats = _live_features(view, displayed_ids)
    for feat in feats:
        if feat.ms2 is not None and feat.ms2.shape[1] > 0:
            all_mz.append(feat.ms2[0])
    dda = view.dda
    if dda is not None and dda.ms2.shape[1] > 0:
        all_mz.append(dda.ms2[0])

    if all_mz:
        all_concat = np.concatenate(all_mz)
        mz_span = float(all_concat.max() - all_concat.min())
    else:
        mz_span = 1.0  # fallback; nothing to draw anyway
    bar_width = MS2_BAR_WIDTH_FRAC * max(mz_span, 1.0)

    # ----- DIA precursor spectra (positive y), normalized to max=1 -----
    # Compute normalization across all displayed DIA spectra combined.
    dia_max = 0.0
    for feat in feats:
        if feat.ms2 is not None and feat.ms2.shape[1] > 0:
            dia_max = max(dia_max, float(feat.ms2[1].max()))
    dia_scale = 1.0 / dia_max if dia_max > 0 else 1.0

    for feat in feats:
        if feat.ms2 is None or feat.ms2.shape[1] == 0:
            continue
        ms2_mz, ms2_i, ms2_dc = feat.ms2
        ms2_i_norm = ms2_i * dia_scale
        ax.bar(
            ms2_mz, ms2_i_norm,
            width=bar_width,
            color=_DIA_COLOR,
            alpha=_DIA_ALPHA,
        )
        # Mark deconvoluted peaks.
        for x, y, dc in zip(ms2_mz, ms2_i_norm, ms2_dc):
            if dc > 0:
                ax.text(
                    x, y, "*",
                    ha="center", va="bottom",
                    color=_DIA_COLOR, alpha=_DIA_ALPHA,
                )
        # Record (mz, normalized intensity) for hover lookup.
        drawn.dia_peaks[feat.id] = np.vstack([ms2_mz, ms2_i_norm])

    # ----- DDA mirror spectrum (negative y), normalized to max=1 -----
    if dda is not None and dda.ms2.shape[1] > 0:
        dms2_mz, dms2_i = dda.ms2
        dda_max = float(dms2_i.max()) if dms2_i.size else 0.0
        dda_scale = 1.0 / dda_max if dda_max > 0 else 1.0
        dms2_i_norm = dms2_i * dda_scale
        ax.bar(
            dms2_mz, -dms2_i_norm,
            width=bar_width,
            color=_DDA_COLOR,
        )
        drawn.dda_peaks = np.vstack([dms2_mz, dms2_i_norm])

    # ----- Annotated-fragment guide lines (if any) -----
    if active_annotation is not None and active_annotation.fragments:
        for frag in active_annotation.fragments:
            color = (
                _FRAG_DIAGNOSTIC_COLOR
                if frag.diagnostic
                else _FRAG_NONDIAGNOSTIC_COLOR
            )
            ax.axvline(frag.mz, color=color, lw=1, ls="--", alpha=0.6)

    # Pad the y-axis a bit so the `*` markers and any future labels fit.
    ylim = ax.get_ylim()
    if ylim != (0.0, 1.0):  # i.e. something was actually drawn
        ax.set_ylim(1.1 * ylim[0], 1.1 * ylim[1])

    ax.set_xlabel("m/z")
    ax.set_ylabel("normalized intensity\n(DIA ↑ / DDA ↓)")

    return drawn


# ---------------------------------------------------------------------------
# Convenience: redraw all four panels at once
# ---------------------------------------------------------------------------


@dataclass
class AllDrawn:
    """Aggregate of records returned by the four plot calls. Held by the
    plot panel widget and consulted by the hover layer."""

    ms1: MS1Drawn
    ms2: MS2Drawn


def plot_all(
    *,
    ax_ms1: Axes,
    ax_xic: Axes,
    ax_atd: Axes,
    ax_ms2: Axes,
    view: GroupView,
    displayed_ids: Iterable[int],
    active_annotation: LipidAnnotation | None = None,
) -> AllDrawn:
    """Redraw all four panels for the given GroupView. Single entry point
    used by the plot panel widget on any state change."""
    # Materialize once so each plot fn sees the same set.
    displayed_ids = list(displayed_ids)
    ms1_drawn = plot_ms1(ax_ms1, view, displayed_ids)
    plot_xic(ax_xic, view, displayed_ids)
    plot_atd(ax_atd, view, displayed_ids)
    ms2_drawn = plot_ms2(
        ax_ms2, view, displayed_ids, active_annotation=active_annotation
    )
    return AllDrawn(ms1=ms1_drawn, ms2=ms2_drawn)
