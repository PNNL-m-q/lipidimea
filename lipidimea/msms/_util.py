"""
LipidIMEA/msms/_util.py

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


def debug_handler(debug_flag, debug_cb, msg, pid=None):
    """
    deal with different debugging states automatically 
    
    debug_flag:

    - ``None``: do nothing
    - ``'text'``: prints text debugging messages only
    - ``'text_pid'``: prints text debugging messages, with PID prepended on the DEBUG label 
    - ``'textcb'``: produces text debugging messages but instead of printing it calls the 
      debug_cb callback with the message as an argument
    - ``'textcb_pid'``: produces text debugging messages but instead of printing it calls 
      the debug_cb callback with the message as an argument, with PID prepended on the DEBUG label 
    
    Parameters
    ----------
    debug_flag : ``str``
        specifies how to dispatch the message, `None` to do nothing
    debug_cb : ``func``
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb'
    msg : ``str``
        debugging message (automatically prepended with "DEBUG: ")
    pid : ``int``, optional
        PID for individual process, may be omitted if debug flag does not have "_pid" in it
    """
    if debug_flag is not None:
        pid_flag = 'pid' in debug_flag
        lbl = '<pid: {}> '.format(pid) if pid_flag else ''
        msg = lbl + 'DEBUG: ' + msg
        if debug_flag in ['text', 'text_pid']:
            print(msg, flush=True)
        if debug_flag in ['textcb', 'textcb_pid']:
            if debug_cb is not None:
                debug_cb(msg)
            else:
                ve = '_debug_handler: debug_flag was set to "textcb" or "textcb_pid" but no debug_cb was provided'
                raise ValueError(ve)


def apply_args_and_kwargs(fn, args, kwargs):
    """ small helper that enables multiprocessing.Pool.starmap with kwargs """
    return fn(*args, **kwargs)

