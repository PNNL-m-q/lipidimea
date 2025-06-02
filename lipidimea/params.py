"""
lipidimea/params.py
Dylan Ross (dylan.ross@pnnl.gov)

    module for organizing/handling parameters 
"""


from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
import os
import enum

import yaml

from lipidimea.util import INCLUDE_DIR
from lipidimea.typing import YamlFilePath


# define paths to default config files
_DEFAULT_DDA_CONFIG = os.path.join(INCLUDE_DIR, "default_dda_params.yaml")
_DEFAULT_DIA_CONFIG = os.path.join(INCLUDE_DIR, "default_dia_params.yaml")
_DEFAULT_ANN_CONFIG = os.path.join(INCLUDE_DIR, "default_ann_params.yaml")


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
class _Display:
    display_name: str


@dataclass
class _Precursor:
    precursor_mz: _Range

    def __post_init__(self):
        if type(self.precursor_mz) is dict:
            self.precursor_mz = _Range(**self.precursor_mz)

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
class _MS2PeakMatching:
    mz_ppm: float

@dataclass
class _StoreData:
    blob: bool


@dataclass
class _ConsolidateDdaFeats:
    mz_ppm: float
    rt_tol: float
    drop_if_no_ms2: bool


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
class _SumCompAnnotationComponent:
    fa_cl: _IntRange
    fa_odd_c: bool
    mz_ppm: float
    config: Optional[YamlFilePath] = None

    def __post_init__(self):
        if type(self.fa_cl) is dict:
            self.fa_cl = _IntRange(**self.fa_cl)




@dataclass
class _CcsTrends:
    percent: float 
    config: Optional[YamlFilePath] = None


# -----------------------------------------------------------------------------
# Helper functions for loading/writing configs


type Params = Union[DdaParams, DiaParams, AnnotationParams]


class _ParamType(enum.Enum):
    DDA = enum.auto()
    DIA = enum.auto()
    ANN = enum.auto()


def _load_yaml(config: YamlFilePath
               ) -> Dict[str, Any] :
    """ Helper function that loads the default config as a nested dict """
    with open(config, "r") as yf:
        cfg = yaml.safe_load(yf)
    return cfg


# def _load_default(param_type: _ParamType
#                   ) -> Dict[str, Any] : 
#     """ Load the default parameters from built-in configuration files as nested dict """
#     match param_type:
#         case _ParamType.DDA: 
#             return _load_yaml(_DEFAULT_DDA_CONFIG)
#         case _ParamType.DIA: 
#             return  _load_yaml(_DEFAULT_DIA_CONFIG)
#         case _ParamType.ANN:
#             return _load_yaml(_DEFAULT_ANN_CONFIG)

def _load_default(param_type: _ParamType) -> Dict[str, Any]:
    # Load the raw YAML (with UI metadata)
    raw = {
        _ParamType.DDA:  _DEFAULT_DDA_CONFIG,
        _ParamType.DIA:  _DEFAULT_DIA_CONFIG,
        _ParamType.ANN:  _DEFAULT_ANN_CONFIG
    }[param_type]
    cfg = _load_yaml(raw)
    # Strip out all UI‐only fields, leaving just the pure values
    clean_cfg = _strip_ui_metadata(cfg)
    return clean_cfg


def _from_config(config: YamlFilePath,
                 param_type: _ParamType
                 ) -> Params :
    """
    Read parameters from a configuration file (YAML) and return an instance of parameters dataclass
    
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
        case _ParamType.DDA: 
            return DdaParams(**params)
        case _ParamType.DIA: 
            return DiaParams(**params)
        case _ParamType.ANN:
            print(params)
            return AnnotationParams(**params)
        
def _strip_ui_metadata(cfg: Any, *, _depth: int = 0) -> Any:
    """
    Recursively strip out GUI‑only keys (display_name, type, description, advanced),
    unwrap any { default: … } wrappers, and convert any numeric strings
    (including scientific notation) into floats.
    """
    # 1) If it’s not a dict, try to convert strings to float
    if not isinstance(cfg, dict):
        if isinstance(cfg, str):
            try:
                return float(cfg)
            except ValueError:
                pass
        return cfg

    # 2) If this dict is a metadata wrapper, unwrap it
    if 'default' in cfg:
        return _strip_ui_metadata(cfg['default'], _depth=_depth)


    # 3) Otherwise, recurse into children, dropping GUI‑only keys
    gui_only = {'type', 'description', 'advanced'}
    if _depth > 0:          #   <── drop `display_name` once we’re inside any section
        gui_only.add('display_name')

    return {
        k: _strip_ui_metadata(v, _depth=_depth + 1)
        for k, v in cfg.items()
        if k not in gui_only
    }




def _write_config(current_dc: Params,
                  config: str,
                  include_unchanged: bool, 
                  param_type: _ParamType
                  ) -> None :
    # NOTE: Assume that the instance of this dataclass is valid in terms of its structure. I 
    #       can't imagine how it could get into an invalid state, but it needs to be for 
    #       this approach to saving cofig file to work.
    # convert this instance to a nested dict
    current = asdict(current_dc)
    if include_unchanged:
        # do not bother trying to see which parameters are changed from their defaults
        to_write = current
    else:
        # helper function to recursively find changed entries
        def find_changes(default, updated):
            changes = {}
            for k, v in updated.items():
                if type(k) is not dict:
                    if v != default[k]:
                        changes[k] = v
                else:
                    if (changes_below := find_changes(default[k], v)) != {}:
                        changes[k] = changes_below
            return changes
        # check default parameters and only include the ones that are changed from the default
        to_write = find_changes(_load_default(param_type), current)
    # TODO: If to_write == {} that means nothing was changed from the default config. Should 
    #       we check for this condition and emit a warning or something? 
    # TODO: Does it matter if the specified config file already exists? It will get overwritten.
    # write the dict data to file 
    with open(config, 'w') as yf:
        yaml.dump(to_write, yf, default_flow_style=False, sort_keys=False)


# -----------------------------------------------------------------------------
# Main parameter dataclasses


@dataclass
class DdaParams:
    """ class for organizing DDA data processing parameters """
    display_name: _Display
    precursor: _Precursor
    extract_and_fit_chroms: _ExtractAndFitChroms
    consolidate_chrom_feats: _ConsolidateChromFeats
    extract_and_fit_ms2_spectra: _ExtractAndFitMs2Spectra
    consolidate_dda_feats: _ConsolidateDdaFeats

    def __post_init__(self):
        if type(self.precursor) is dict:
            self.precursor = _Precursor(**self.precursor)
        if type(self.extract_and_fit_chroms) is dict:
            self.extract_and_fit_chroms = _ExtractAndFitChroms(**self.extract_and_fit_chroms)
        if type(self.consolidate_chrom_feats) is dict:
            self.consolidate_chrom_feats = _ConsolidateChromFeats(**self.consolidate_chrom_feats) 
        if type(self.extract_and_fit_ms2_spectra) is dict:
            self.extract_and_fit_ms2_spectra = _ExtractAndFitMs2Spectra(**self.extract_and_fit_ms2_spectra)
        if type(self.consolidate_dda_feats) is dict:
            self.consolidate_dda_feats = _ConsolidateDdaFeats(**self.consolidate_dda_feats)

    # --- static methods ---

    @staticmethod
    def load_default() -> "DdaParams" : return DdaParams(**_load_default(_ParamType.DDA))

    @staticmethod
    def from_config(config: YamlFilePath) -> "DdaParams" : return _from_config(config, _ParamType.DDA)  # type: ignore

    # --- normal methods ---

    def write_config(self,
                     config: YamlFilePath, 
                     include_unchanged: bool = False
                     ) -> None :
        """ Write current parameters to a configuration file """
        _write_config(self, config, include_unchanged, _ParamType.DDA)


@dataclass
class DiaParams:
    """ class for organizing DIA data processing parameters """
    display_name: _Display
    extract_and_fit_chroms: _ExtractAndFitChroms
    extract_and_fit_atds: _ExtractAndFitChroms
    extract_and_fit_ms2_spectra: _ExtractAndFitMs2Spectra
    ms2_peak_matching: _MS2PeakMatching
    deconvolute_ms2_peaks: _DeconvoluteMs2Peaks
    store: _StoreData

    def __post_init__(self):
        if type(self.extract_and_fit_chroms) is dict:
            self.extract_and_fit_chroms = _ExtractAndFitChroms(**self.extract_and_fit_chroms)
        if type(self.extract_and_fit_atds) is dict:
            self.extract_and_fit_atds = _ExtractAndFitChroms(**self.extract_and_fit_atds)
        if type(self.extract_and_fit_ms2_spectra) is dict:
            self.extract_and_fit_ms2_spectra = _ExtractAndFitMs2Spectra(**self.extract_and_fit_ms2_spectra)
        if type(self.ms2_peak_matching) is dict:
            self.ms2_peak_matching = _MS2PeakMatching(**self.ms2_peak_matching)
        if type(self.deconvolute_ms2_peaks) is dict:
            self.deconvolute_ms2_peaks = _DeconvoluteMs2Peaks(**self.deconvolute_ms2_peaks)
        if type(self.store) is dict:
            self.store = _StoreData(**self.store)


    # --- static methods ---

    @staticmethod
    def load_default() -> "DiaParams" : return DiaParams(**_load_default(_ParamType.DIA))

    @staticmethod
    def from_config(config: YamlFilePath) -> "DiaParams" : return _from_config(config, _ParamType.DIA)  # type: ignore

    # --- normal methods ---

    def write_config(self,
                     config: YamlFilePath, 
                     include_unchanged: bool = False
                     ) -> None :
        """ Write current parameters to a configuration file """
        _write_config(self, config, include_unchanged, _ParamType.DIA)


@dataclass
class AnnotationParams:
    """ class for organizing lipid annotation parameters """
    display_name: _Display
    ionization: Optional[str]   # TODO: Some mechanism to restrict this to only "POS" or "NEG" as valid values?
    sum_comp: _SumCompAnnotationComponent
    config_file: Optional[dict]
    ccs_trends: _CcsTrends
    frag_rules: _AnnotationComponent

    def __post_init__(self):
        if type(self.sum_comp) is dict:
            self.sum_comp = _SumCompAnnotationComponent(**self.sum_comp)
        if type(self.frag_rules) is dict:
            self.frag_rules = _AnnotationComponent(**self.frag_rules)
        if type(self.ccs_trends) is dict:
            self.ccs_trends = _CcsTrends(**self.ccs_trends)

    # --- static methods ---

    @staticmethod
    def load_default() -> "AnnotationParams" : return AnnotationParams(**_load_default(_ParamType.ANN))

    @staticmethod
    def from_config(config: YamlFilePath) -> "AnnotationParams" : return _from_config(config, _ParamType.ANN)  # type: ignore

    # --- normal methods ---

    def write_config(self,
                     config: YamlFilePath, 
                     include_unchanged: bool = False
                     ) -> None :
        """ Write current parameters to a configuration file """
        _write_config(self, config, include_unchanged, _ParamType.ANN)