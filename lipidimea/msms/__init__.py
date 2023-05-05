"""
LipidIMEA/msms/__init__.py

Dylan Ross (dylan.ross@pnnl.gov)

    sub-module for handling MS/MS related functionality

"""

import os
from sqlite3 import connect


def create_lipid_ids_db(dir, label, overwrite=False):
    """
    creates a sqlite database for lipid IDs from DDA/DDA data

    raises a RuntimeError if the database already exists

    Parameters
    ----------
    dir : ``str``
        directory to create database in
    label : ``str``
        label for the database -> "{label}_dda_ids.db" 
    overwrite : ``bool``, default=False
        if the database file already exists and this flag is True, then overwrite existing database 
        and do not raise the RuntimeError

    Returns
    -------
    db_path : ``str``
        path to the initialized database
    """
    # database file name
    f = os.path.join(dir, '{}_lipid_ids.db'.format(label))
    # see if the file exists
    if os.path.exists(f):
        if overwrite:
            os.remove(f)
        else:
            msg = '_create_dda_ids_db: DDA lipid IDs database file ({}) already exists'
            raise RuntimeError(msg.format(f))
    # initial connection creates the DB
    con = connect(f)  
    cur = con.cursor()
    # execute SQL script to set up the database
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lipid_ids.sql'), 'r') as sql_f:
        cur.executescript(sql_f.read())
    # save and close the database
    con.commit()
    con.close()
    # return the path
    return f
