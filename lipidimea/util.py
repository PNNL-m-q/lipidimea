"""
LipidIMEA/util.py

Dylan Ross (dylan.ross@pnnl.gov)

    module with general utilities
"""


import os
from sqlite3 import connect

import yaml


def create_results_db(f, overwrite=False):
    """
    creates a sqlite database for results from DDA/DDA data analysis

    raises a RuntimeError if the database already exists

    Parameters
    ----------
    f : ``str``
        filename/path of the database
    overwrite : ``bool``, default=False
        if the database file already exists and this flag is True, then overwrite existing database 
        and do not raise the RuntimeError
    """
    # see if the file exists
    if os.path.exists(f):
        if overwrite:
            os.remove(f)
        else:
            msg = '_create_dda_ids_db: results database file ({}) already exists'
            raise RuntimeError(msg.format(f))
    # initial connection creates the DB
    con = connect(f)  
    cur = con.cursor()
    # execute SQL script to set up the database
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_include/results.sql'), 'r') as sql_f:
        cur.executescript(sql_f.read())
    # save and close the database
    con.commit()
    con.close()


def load_default_params():
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


def load_params(params_file):
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


def save_params(input_output, params, params_file):
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

