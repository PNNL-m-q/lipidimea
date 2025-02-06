"""
lipidimea/params.py
Dylan Ross (dylan.ross@pnnl.gov)

    module for organizing/handling parameters 
"""


from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
import os
import enum

import yaml

from lipidimea.util import INCLUDE_DIR
from lipidimea.typing import YamlFilePath


# define paths to default config files
_DEFAULT_DDA_CONFIG = os.path.join(INCLUDE_DIR, "")
_DEFAULT_DIA_CONFIG = os.path.join(INCLUDE_DIR, "")
_DEFAULT_ANN_CONFIG = os.path.join(INCLUDE_DIR, "")


# -----------------------------------------------------------------------------
# Component dataclasses that are nested under the DdaParams, DiaParams
# and AnnotationParams dataclasses. 


@dataclass
class _Range:
    min: float
    max: float


@dataclass
class _IntRange:
    min: int
    max: int


@dataclass
class _ExtractAndFitChroms:
    min_rel_height: float
    min_abs_height: float
    fwhm: _Range
    max_peaks: int
    min_psnr: Optional[float] = None
    mz_ppm: Optional[float] = None
    rt_tol: Optional[float] = None

    def __post_init__(self):
        if type(self.fwhm) is dict:
            self.fwhm = _Range(**self.fwhm)


@dataclass
class _ConsolidateChromFeats:
    mz_ppm: float
    rt_tol: float


@dataclass
class _ExtractAndFitMs2Spectra:
    min_rel_height: float
    min_abs_height: float
    fwhm: _Range
    peak_min_dist: float
    pre_mz_ppm: Optional[float] = None
    mz_bin_min: Optional[float] = None
    mz_bin_size: Optional[float] = None

    def __post_init__(self):
        if type(self.fwhm) is dict:
            self.fwhm = _Range(**self.fwhm)


@dataclass
class _ConsolidateDdaFeats:
    mz_ppm: float
    rt_tol: float
    drop_if_no_ms2: bool


@dataclass
class _DiaChromPeakSelect:
    target_rt_shift: float
    target_rt_tol: float


@dataclass
class _DeconvoluteMs2Peaks:
    mz_ppm: float
    xic_dist_threshold: float
    atd_dist_threshold: float 
    xic_dist_metric: str
    atd_dist_metric: str


@dataclass
class _AnnotationComponent:
    fa_c: _IntRange
    fa_odd_c: bool
    mz_ppm: float
    config: Optional[YamlFilePath] = None

    def __post_init__(self):
        if type(self.fa_c) is dict:
            self.fa_c = _IntRange(**self.fa_c)


@dataclass
class _CcsTrends:
    percent: float 
    config: Optional[YamlFilePath] = None


# -----------------------------------------------------------------------------
# Main parameter dataclasses


@dataclass
class DdaParams:
    """ class for organizing DDA data processing parameters """
    precursor_mz: _Range
    extract_and_fit_chroms: _ExtractAndFitChroms
    consolidate_chrom_feats: _ConsolidateChromFeats
    extract_and_fit_ms2_spectra: _ExtractAndFitMs2Spectra
    consolidate_dda_feats: _ConsolidateDdaFeats

    def __post_init__(self):
        if type(self.precursor_mz) is dict:
            self.precursor_mz = _Range(**self.precursor_mz)
        if type(self.extract_and_fit_chroms) is dict:
            self.extract_and_fit_chroms = _ExtractAndFitChroms(**self.extract_and_fit_chroms)
        if type(self.consolidate_chrom_feats) is dict:
            self.consolidate_chrom_feats = _ConsolidateChromFeats(**self.consolidate_chrom_feats) 
        if type(self.extract_and_fit_ms2_spectra) is dict:
            self.extract_and_fit_ms2_spectra = _ExtractAndFitMs2Spectra(**self.extract_and_fit_ms2_spectra)
        if type(self.consolidate_dda_feats) is dict:
            self.consolidate_dda_feats = _ConsolidateDdaFeats(**self.consolidate_dda_feats)


@dataclass
class DiaParams:
    """ class for organizing DIA data processing parameters """
    extract_and_fit_chroms: _ExtractAndFitChroms
    select_chrom_peaks: _DiaChromPeakSelect
    extract_and_fit_atds: _ExtractAndFitChroms
    extract_and_fit_ms2_spectra: _ExtractAndFitMs2Spectra
    ms2_peak_matching_ppm: float
    deconvolute_ms2_peaks: _DeconvoluteMs2Peaks
    store_blobs: bool

    def __post_init__(self):
        if type(self.extract_and_fit_chroms) is dict:
            self.extract_and_fit_chroms = _ExtractAndFitChroms(**self.extract_and_fit_chroms)
        if type(self.select_chrom_peaks) is dict:
            self.select_chrom_peaks = _DiaChromPeakSelect(**self.select_chrom_peaks)
        if type(self.extract_and_fit_atds) is dict:
            self.extract_and_fit_atds = _ExtractAndFitChroms(**self.extract_and_fit_atds)
        if type(self.extract_and_fit_ms2_spectra) is dict:
            self.extract_and_fit_ms2_spectra = _ExtractAndFitMs2Spectra(**self.extract_and_fit_ms2_spectra)
        if type(self.deconvolute_ms2_peaks) is dict:
            self.deconvolute_ms2_peaks = _DeconvoluteMs2Peaks(**self.deconvolute_ms2_peaks)


@dataclass
class AnnotationParams:
    """ class for organizing lipid annotation parameters """
    ionization: str   # TODO: Some mechanism to restrict this to only "POS" or "NEG" as valid values?
    sum_comp: _AnnotationComponent
    rt_range_config: YamlFilePath
    ccs_trends: _CcsTrends
    frag_rules: _AnnotationComponent

    def __post_init__(self):
        if type(self.sum_comp) is dict:
            self.sum_comp = _AnnotationComponent(**self.sum_comp)
        if type(self.frag_rules) is dict:
            self.frag_rules = _AnnotationComponent(**self.frag_rules)
        if type(self.ccs_trends) is dict:
            self.ccs_trends = _CcsTrends(**self.ccs_trends)


type Params = Union[DdaParams, DiaParams, AnnotationParams]


class ParamType(enum.Enum):
    DDA = enum.auto()
    DIA = enum.auto()
    ANN = enum.auto()


# -----------------------------------------------------------------------------
# Functions for loading configs


def _load_yaml(config: YamlFilePath
               ) -> Dict[str, Any] :
    """ Helper function that loads the default config as a nested dict """
    with open(config, "r") as yf:
        cfg = yaml.safe_load(yf)
    return cfg


def _load_default(param_type: ParamType
                  ) -> Dict[str, Any] : 
    """ Load the default parameters from built-in configuration files as nested dict """
    match param_type:
        case ParamType.DDA: 
            return _load_yaml(_DEFAULT_DDA_CONFIG)
        case ParamType.DIA: 
            return  _load_yaml(_DEFAULT_DIA_CONFIG)
        case ParamType.ANN:
            return _load_yaml(_DEFAULT_ANN_CONFIG)
        

def load_default(param_type: ParamType
                 ) -> Params: 
    """ Load default parameters from built-in configuration files """
    match param_type:
        case ParamType.DDA: 
            return DdaParams(**_load_default(param_type))
        case ParamType.DIA: 
            return DiaParams(**_load_default(param_type))
        case ParamType.ANN:
            return AnnotationParams(**_load_default(param_type))


def from_config(config: YamlFilePath,
                param_type: ParamType
                ) -> Params :
    """
    Read parameters from a configuration file (YAML) and return an instance of `SlimParams`
    
    Any parameters not explicitly specified in the config are taken from the default config.
    """
    # start by loading the default config
    params = _load_default(param_type)
    # then load the specified config file
    # it needs to exist
    if not os.path.isfile(config):
        raise ValueError(f"config file {config} not found")
    with open(config, "r") as yf:
        config_params = yaml.safe_load(yf)
    # keep track of the current parameter that is being updated (track nested params)
    _current_param = []
    # helper function to overwrite defaults with updated parameters
    def overwrite(default, updated):
        for k, v in updated.items():
            _current_param.append(k)
            if type(v) is not dict: 
                # this should force a KeyError when the key from updated is not present in default
                _ = default[k]
                default[k] = v
            else:
                # recurse
                overwrite(default[k], v)
            # after each item is processed, take it out of the current_param list
            _ = _current_param.pop()
    if config_params is not None:
        # only try to update the parameters if the config file was not empty
        try:
            # update defaults with values from specified config
            overwrite(params, config_params)
        except KeyError as e:
            raise ValueError(
                f"Supplied configuration file ({config}) contains an unrecognized parameter or section: "
                # grab contents of the current_param list to indicate what param caused the problem
                # this should account for nested parameters
                + ".".join(map(str, _current_param))
            ) from e
    match param_type:
        case ParamType.DDA: 
            return DdaParams(**params)
        case ParamType.DIA: 
            return DiaParams(**params)
        case ParamType.ANN:
            return AnnotationParams(**params)