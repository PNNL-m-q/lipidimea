"""
lipidimea/msms/_util.py

Dylan Ross (dylan.ross@pnnl.gov)

    internal module with utilities related to MSMS data processing
"""


import os
import re
from typing import Any, Callable, List, Dict

import numpy as np
import numpy.typing as npt


def ms2_to_str(mzs: npt.NDArray[np.float64], iis: npt.NDArray[np.float64]
               ) -> str :
    """  
    converts arrays of m/z bins and intensities to flat str representation
    with space-separated peaks in format "{mz}:{intensity}"
    
    Parameters
    ----------
    mzs : ``numpy.ndarray(float)``
    iis : ``numpy.ndarray(float)``
        m/z and intensity components of mass spectrum as arrays

    Returns
    -------
    spec_string : ``str``
        string representation of spectrum
    """
    lm, li = len(mzs), len(iis)
    if lm != li:
        msg = f"ms2_to_str: mzs and iis arrays have different lengths ({lm} and {li})"
        raise ValueError(msg)
    if lm < 1:
        msg = f"ms2_to_str: mzs and iis arrays should not be empty"
        raise ValueError(msg)        
    s = ''
    for mz, i in zip(mzs, iis):
        s += '{:.4f}:{:.0f} '.format(mz, i)
    return s.rstrip()


def str_to_ms2(s: str
               ) -> npt.NDArray[np.float64] :
    """
    converts flat str representation (space-separated peaks in format "{mz}:{intensity}") 
    to arrays of m/z and intensities

    Parameters
    ----------
    s : ``str``
        string form of spectrum

    Returns
    -------
    spectrum : ``numpy.ndarray(float)``
        spectrum as 2D array with m/z and intensity components
    """
    # check the format of the spectrum string
    if not re.match(r'^([0-9]+[.][0-9]*:[0-9]+[ ]*)+$', s):
        msg = "str_to_ms2: spectrum string not properly formatted"
        raise ValueError(msg)
    ms_, is_ = [], []
    if ' ' in s:
        for ms2pk in s.split():
            m_, i_ = [float(_) for _ in ms2pk.split(':')]
            ms_.append(m_)
            is_.append(i_)
    else:
        # deal with strings that have only a single mz:intensity pair
        m_, i_ = [float(_) for _ in s.split(':')]
        ms_.append(m_)
        is_.append(i_)
    return np.array([ms_, is_])


def apply_args_and_kwargs(fn: Callable, args: List[Any], kwargs: Dict[Any, Any]
                          ) -> Any:
    """ small helper that enables multiprocessing.Pool.starmap with kwargs """
    return fn(*args, **kwargs)

