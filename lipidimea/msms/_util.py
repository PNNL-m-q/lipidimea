"""
lipidimea/msms/_util.py

Dylan Ross (dylan.ross@pnnl.gov)

    internal module with utilities related to MSMS data processing
"""


import os

import numpy as np
            

def ms2_to_str(mzs, iis):
    """  
    converts arrays of m/z bins and intensities to flat str representation
    """
    s = ''
    for mz, i in zip(mzs, iis):
        s += '{:.4f}:{:.0f} '.format(mz, i)
    return s.rstrip()


def str_to_ms2(s):
    """
    converts flat str representation to arrays of m/z and intensities
    """
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


def apply_args_and_kwargs(fn, args, kwargs):
    """ small helper that enables multiprocessing.Pool.starmap with kwargs """
    return fn(*args, **kwargs)

