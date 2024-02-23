"""
lipidimea/params.py

Dylan Ross (dylan.ross@pnnl.gov)

    module for organizing/handling parameters 
"""


from typing import Dict, Any, Tuple
from dataclasses import dataclass
import os

import yaml


@dataclass
class ExtractAndFitChromsParams:
    """ parameters for extracting and fitting chromatograms """
    mz_ppm: float
    min_rel_height: float
    min_abs_height: float
    fwhm_min: float 
    fwhm_max: float
    max_peaks: int
    min_psnr: float


@dataclass
class ConsolidateChromFeatsParams:
    """ parameters for consolidating chromatographic features """
    mz_ppm: float
    rt_tol: float


@dataclass
class ExtractAndFitMS2SpectraParams:
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
class ConsolidateDdaFeaturesParams:
    """ parameters for consolidating DDA features """
    mz_ppm: float
    rt_tol: float
    drop_if_no_ms2: bool


@dataclass
class DdaParams:
    """ class for organizing DDA data processing parameters """
    extract_and_fit_chrom_params: ExtractAndFitChromsParams
    consolidate_chrom_feats_params: ConsolidateChromFeatsParams
    extract_and_fit_ms2_spectra_params: ExtractAndFitMS2SpectraParams
    consolidate_dda_features_params: ConsolidateDdaFeaturesParams


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
        params[top_lvl] = {section: {param: value['default'] for param, value in sec_params.items() if param != 'display_name'} for section, sec_params in defaults[top_lvl].items() if section != 'display_name'}
    params['misc'] = {param: value['default'] for param, value in defaults['misc'].items() if param != 'display_name'}
    return params


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

