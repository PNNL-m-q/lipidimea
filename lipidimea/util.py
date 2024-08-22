"""
lipidimea/util.py

Dylan Ross (dylan.ross@pnnl.gov)

    module with general utilities
"""


import os
from typing import Optional, Callable
from sqlite3 import connect

from lipidimea.typing import (
    ResultsDbPath, ResultsDbCursor, MzaFilePath, MzaFileId
)


# define path to results DB schema file
_RESULTS_DB_SCHEMA = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_include/results.sqlite3')


def create_results_db(results_file: ResultsDbPath, 
                      overwrite: bool = False,
                      strict: bool = True
                      ) -> None:
    """
    creates a sqlite database for results from DDA/DDA data analysis

    raises a RuntimeError if the database already exists

    Parameters
    ----------
    results_file : ``ResultsDbPath``
        filename/path of the database
    overwrite : ``bool``, default=False
        if the database file already exists and this flag is True, then overwrite existing database 
        and do not raise the RuntimeError
    strict : ``bool``, default=True
        use STRICT constraint on all data tables in results database, set this to False to exclude
        this constraint and enable backward compatibility with older versions of Python/sqlite3
        since 3.12 is the first Python version to support the STRICT mode
    """
    # see if the file exists
    if os.path.exists(results_file):
        if overwrite:
            os.remove(results_file)
        else:
            msg = 'create_results_db: results database file ({}) already exists'
            raise RuntimeError(msg.format(results_file))
    # initial connection creates the DB
    con = connect(results_file)  
    cur = con.cursor()
    # execute SQL script to set up the database
    with open(_RESULTS_DB_SCHEMA, 'r') as sql_f:
        content = sql_f.read()
        # patch schema in-place to remove STRICT constraints if strict flag set to False
        if not strict:
            content = content.replace("STRICT", "")
        cur.executescript(content)
    # save and close the database
    con.commit()
    con.close()


def add_data_file_to_db(cur: ResultsDbCursor, 
                        data_file_type: str,
                        data_file_path: MzaFilePath
                        ) -> MzaFileId :
    """
    add a data file to the results database (DataFiles table) and return the corresponding 
    data file identifier (`int`)
    """
    qry = """--sqlite3
        INSERT INTO DataFiles VALUES (?,?,?,?,?)
    ;"""
    cur.execute(qry, (None, data_file_type, data_file_path, None, None))
    return cur.lastrowid


def debug_handler(debug_flag: Optional[str], debug_cb: Optional[Callable], msg: str, 
                  pid: Optional[int] = None
                  ) -> None :
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
        debug_flag is not set to 'textcb' or 'textcb_pid'
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

