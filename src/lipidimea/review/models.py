"""
lipidimea.review.models
=======================

Dataclasses representing the units of information shown in each of the three
review panels (group / feature / lipid), plus supporting types for the
matched DDA precursor and the fully-populated view of a single feature group.

These types are pure data containers with no DB or UI knowledge.
"""


from dataclasses import dataclass, field

import numpy as np


# ---------------------------------------------------------------------------
# Row-level types (one per row in their respective panel)
# ---------------------------------------------------------------------------


@dataclass
class FeatureGroup:
    """One row in the 'DIA feature groups' panel.

    Loaded eagerly for all groups at startup; cheap.
    `deleted` is the in-memory soft-delete flag — actual DB deletion only
    happens on save.
    """

    id: int
    mz: float
    rt: float
    dt: float
    ccs: float | None
    deleted: bool = False


@dataclass
class Feature:
    """One row in the 'DIA features in group' panel (i.e. one DIA precursor).

    Blob arrays are populated when the parent GroupView is built and remain
    attached for the lifetime of that GroupView.

    Array shapes:
        ms1, xic, atd : (2, N)   rows = (x-axis, intensity)
        ms2           : (3, N)   rows = (m/z, intensity, deconvoluted-flag)
    """

    id: int
    group_id: int
    data_file: str
    display: bool = True
    deleted: bool = False

    ms1: np.ndarray | None = None
    xic: np.ndarray | None = None
    atd: np.ndarray | None = None
    ms2: np.ndarray | None = None


@dataclass
class FragmentAnnotation:
    """One annotated fragment for a lipid annotation.

    `mz` is the *theoretical* fragment m/z from the annotation source;
    matching to observed MS2 peaks is done with a ppm tolerance defined
    in `lipidimea.review.plotting`.
    """

    mz: float
    label: str
    diagnostic: bool  # diagnostic for the lipid class?


@dataclass
class LipidAnnotation:
    """One row in the 'lipid annotations' panel."""

    id: int
    feature_id: int  # which DIA precursor this annotation is attached to
    lipid: str
    adduct: str
    mz_ppm_err: float
    ccs_pct_err: float | None
    acyl_chains: str | None
    # populated by a future query; left empty for v1
    fragments: list[FragmentAnnotation] = field(default_factory=list)
    deleted: bool = False


@dataclass
class DDAMatch:
    """The closest matching DDA precursor for a feature group, if any."""

    dda_pre_id: int
    mz: float
    rt: float
    rt_fwhm: float
    rt_pkht: float
    ms2: np.ndarray  # shape (2, N): m/z, intensity


# ---------------------------------------------------------------------------
# Aggregate type: everything needed to render one feature group
# ---------------------------------------------------------------------------


@dataclass
class GroupView:
    """Fully populated view of a single feature group.

    Built on demand by the session layer when a group is selected, and cached
    in an LRU so back/forth navigation is instant.
    """

    group: FeatureGroup
    features: dict[int, Feature]              # feature_id -> Feature
    annotations: dict[int, LipidAnnotation]   # annotation_id -> LipidAnnotation
    dda: DDAMatch | None