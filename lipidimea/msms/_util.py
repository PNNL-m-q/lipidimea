"""
pyliquid/msms/_util.py

Dylan Ross (dylan.ross@pnnl.gov)

    internal module with utilities related to MSMS data processing
"""


import numpy as np


def _check_params(params, expected_params):
    """
    Checks parameters (dict) against a list of expected params, raises a ValueError if any are missing
    """
    for ep in expected_params:
        if ep not in params:
            msg = '_check_params: expected parameter {} not present in params'
            raise ValueError(msg.format(ep))
            

def _ms2_to_str(mzs, iis):
    """  
    converts arrays of m/z bins and intensities to flat str representation
    """
    s = ''
    for mz, i in zip(mzs, iis):
        s += '{:.4f}:{:.0f} '.format(mz, i)
    return s.rstrip()


def _str_to_ms2(s):
    """
    converts flat str representation to arrays of m/z and intensities
    """
    ms_, is_ = [], []
    for ms2pk in s.split():
        m_, i_ = [float(_) for _ in ms2pk.split(':')]
        ms_.append(m_)
        is_.append(i_)
    return np.array([ms_, is_])
        

def _debug_handler(debug_flag, message):
    """
    function for handling debugging
    The debug flag can be None, in which case no debugging info is produced, or it can be a reference 
    to a callback function which is called with message as the argument

    Parameters
    ----------
    debug_flag : ``func`` or ``None``
        specify how to handle debugging messages
    message : ``str``
        debugging message  
    """
