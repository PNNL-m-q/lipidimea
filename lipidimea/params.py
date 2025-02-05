"""
lipidimea/params.py

Dylan Ross (dylan.ross@pnnl.gov)

    module for organizing/handling parameters 
"""


from typing import Dict, Any, Tuple
from dataclasses import dataclass
import os
from os import path as op

import yaml

from lipidimea.typing import YamlFilePath


# define paths to default sum composition lipid DB config files
DEFAULT_POS_SCDB_CONFIG: YamlFilePath = op.join(op.dirname(op.abspath(__file__)), 
                                                '_include/scdb/pos.yml')
DEFAULT_NEG_SCDB_CONFIG: YamlFilePath = op.join(op.dirname(op.abspath(__file__)), 
                                                '_include/scdb/neg.yml')

# define path to default RT ranges config
DEFAULT_RP_RT_RANGE_CONFIG: YamlFilePath = op.join(op.dirname(op.abspath(__file__)), 
                                                   '_include/rt_ranges/RP.yml')

# define path to literature CCS trends file
LITERATURE_CCS_TREND_PARAMS: YamlFilePath = op.join(op.dirname(op.abspath(__file__)), 
                                                    '_include/literature_ccs_trend_params.yml')


@dataclass
class DdaExtractAndFitChromsParams:
    """ parameters for extracting and fitting chromatograms """
    mz_ppm: float
    min_rel_height: float
    min_abs_height: float
    fwhm_min: float 
    fwhm_max: float
    max_peaks: int
    min_psnr: float


@dataclass
class DdaConsolidateChromFeatsParams:
    """ parameters for consolidating chromatographic features """
    mz_ppm: float
    rt_tol: float


@dataclass
class DdaExtractAndFitMs2SpectraParams:
    """ parameters for extracting and fitting MS2 spectra """
    pre_mz_ppm: float
    mz_bin_min: float
    mz_bin_size: float
    min_rel_height: float
    min_abs_height: float
    fwhm_min: float
    fwhm_max: float
    peak_min_dist: float


@dataclass
class DdaConsolidateFeaturesParams:
    """ parameters for consolidating DDA features """
    mz_ppm: float
    rt_tol: float
    drop_if_no_ms2: bool


# TODO (Dylan Ross): Refactor parameter dataclasses to work more like AnnotationParams

@dataclass
class DdaParams:
    """ class for organizing DDA data processing parameters """
    min_precursor_mz: float
    max_precursor_mz: float
    extract_and_fit_chrom_params: DdaExtractAndFitChromsParams
    consolidate_chrom_feats_params: DdaConsolidateChromFeatsParams
    extract_and_fit_ms2_spectra_params: DdaExtractAndFitMs2SpectraParams
    consolidate_dda_features_params: DdaConsolidateFeaturesParams


@dataclass
class DiaExtractAndFitChromsParams:
    """ parameters for extracting and fitting chromatograms """
    mz_ppm: float
    rt_tol: float
    min_rel_height: float
    min_abs_height: float
    fwhm_min: float 
    fwhm_max: float
    max_peaks: int
    

@dataclass
class DiaChromPeakSelectionParams:
    """ parameters for selecting chromatographic peaks """
    target_rt_shift: float
    target_rt_tol: float


@dataclass
class DiaAtdFitParams:
    """ parameters for fitting ATDs """
    min_rel_height: float
    min_abs_height: float
    fwhm_min: float 
    fwhm_max: float
    max_peaks: int


@dataclass
class DiaMs2FitParams:
    min_rel_height: float
    min_abs_height: float
    fwhm_min: float 
    fwhm_max: float
    min_dist: float


@dataclass
class DiaDeconvoluteMs2PeaksParams:
    """ parameters for deconvoluting MS2 peaks """
    mz_ppm: float
    xic_dist_threshold: float
    atd_dist_threshold: float 
    xic_dist_metric: str
    atd_dist_metric: str


# TODO (Dylan Ross): Refactor parameter dataclasses to work more like AnnotationParams

@dataclass
class DiaParams:
    """ class for organizing DIA data processing parameters """
    extract_and_fit_chrom_params: DiaExtractAndFitChromsParams
    select_chrom_peaks_params: DiaChromPeakSelectionParams
    atd_fit_params: DiaAtdFitParams
    ms2_fit_params: DiaMs2FitParams
    ms2_peak_matching_ppm: float
    deconvolute_ms2_peaks_params: DiaDeconvoluteMs2PeaksParams
    store_blobs: bool


@dataclass
class SumCompAnnParams:
    """ parameters for initial annotation based on sum composition """
    fa_min_c: int
    fa_max_c: int
    fa_odd_c: bool
    mz_ppm: float
    config: YamlFilePath
    

@dataclass
class FragRuleAnnParams:
    """ parameters for annotation using fragmentation rules """
    mz_ppm: float
    fa_min_c: int
    fa_max_c: int
    fa_odd_c: bool


@dataclass
class AnnotationParams:
    """ class for organizing lipid annotation parameters """
    SumCompAnnParams: SumCompAnnParams
    rt_range_config: YamlFilePath
    ccs_trend_percent: float
    FragRuleAnnParams: FragRuleAnnParams
    ionization: str


def load_default_params(
                        ) -> Dict[Any, Any]:
    """
    load the default parameters (only the analysis parameters component, not the complete parameters 
    with input/output component)
    
    Returns
    -------
    params : ``dict(...)``
        analysis parameter dict component of parameters, with all default values
    """
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_include/default_params.yml'), 'r') as yf:
        defaults = yaml.safe_load(yf)
    params = {}
    for top_lvl in ['dda', 'dia', 'annotation']:
        params[top_lvl] = {
            section: {
                param: value['default'] for param, value in sec_params.items() if param != 'display_name'
            } 
            for section, sec_params in defaults[top_lvl].items() 
            if section != 'display_name'
        }
    params['misc'] = {
        param: value['default'] 
        for param, value in defaults['misc'].items() 
        if param != 'display_name'
    }
    return params


# TODO (Dylan Ross): The load params function should return a tuple of the top level 
#                    dataclasses, at present this is (DdaParams, DiaParams) but will
#                    add AnnotationParams and InputOutput Params?

def load_params(params_file: str
                ) -> Tuple[Dict[Any, Any], Dict[Any, Any]]:
    """
    load parameters from a YAML file, returns a dict with the params
    
    Parameters
    ----------
    params_file : ``str``
        filename/path of parameters file to load (as YAML)

    Returns
    -------
    input_output : ``dict(...)``
        input/output component of parameters
    params : ``dict(...)``
        analysis parameter dict component of parameters
    """
    with open(params_file, 'r') as yf:
        params = yaml.safe_load(yf)
    return params['input_output'], params['params']


def save_params(input_output: Dict[Any, Any], params: Dict[Any, Any], params_file: str
                ) -> None:
    """
    save analysis parameters along with input/output info

    Parameters
    ----------
    input_output : ``dict(...)``
        input/output component of parameters
    params : ``dict(...)``
        analysis parameter dict component of parameters
    params_file : ``str``
        filename/path to save parameters file (as YAML)
    """
    with open(params_file, 'w') as out:
        yaml.dump({'input_output': input_output, 'params': params}, out, default_flow_style=False)

