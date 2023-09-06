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

