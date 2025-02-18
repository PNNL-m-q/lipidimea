"""
lipidimea/_cli/dia.py
Dylan Ross (dylan.ross@pnnl.gov)

    define CLI for dia top-level subcommand
"""


import argparse
import sqlite3
import os
import errno

from lipidimea.params import DiaParams
from lipidimea.msms.dia import (
    extract_dia_features,
    extract_dia_features_multiproc,
    add_calibrated_ccs_to_dia_features
)


#------------------------------------------------------------------------------
# dia process subcommand


_PROCESS_DESCRIPTION = """
    TODO: description for dia process subcommand
"""


def _setup_process_subparser(parser: argparse.ArgumentParser):
    """ set up the subparser for dia process subcommand """
    parser.add_argument(
        "PARAMS_CONFIG",
        help="parameter config file (.yaml)"
    )
    parser.add_argument(
        "RESULTS_DB",
        help="results database file (.db)"
    )
    parser.add_argument(
        "DIA_MZA",
        nargs="*",
        help="DIA data files to process (.mza)"
    )
    parser.add_argument(
        "--n-proc",
        default=1,
        type=int,
        help="set >1 to processes multiple data files in parallel (default=1)"
    )


def _process_run(args: argparse.Namespace):
    """ perform DIA data extraction and processing """
    # load the parameters
    params = DiaParams.from_config(args.PARAMS_CONFIG)
    # extract the DDA features
    if args.n_proc > 1:
        _ = extract_dia_features_multiproc(
            args.DIA_MZA, args.RESULTS_DB, params, n_proc=args.n_proc, debug_flag="text_pid"
        )
    else:
        for dia_data_file in args.DIA_MZA:
            _ = extract_dia_features(
                dia_data_file, args.RESULTS_DB, params, debug_flag="text"
            )


#------------------------------------------------------------------------------
# dia list subcommand


_LIST_DESCRIPTION = """
    TODO: description for dia list subcommand
"""


def _setup_list_subparser(parser: argparse.ArgumentParser):
    """ set up the subparser for dia list subcommand """
    parser.add_argument(
        "list_choice",
        choices=[
            "file_ids"
        ],
        help="which information to fetch"
    )
    parser.add_argument(
        "RESULTS_DB",
        help="results database file (.db)"
    )
    


_QUERIES = {
    "file_id": """--beginsql
        SELECT
            DISTINCT dfile_id,
            dfile_name
        FROM 
            DIAPrecursors
            JOIN DataFiles USING(dfile_id)
        ORDER BY
            dfile_name
    --endsql"""
}

def _list_run(args: argparse.Namespace):
    """ run function for dia list subcommand """
    # ensure results database exists first
    if not os.path.isfile(args.RESULTS_DB):
        raise FileNotFoundError(errno.ENOENT, 
                                os.strerror(errno.ENOENT), 
                                args.RESULTS_DB)
    # connect to database
    con = sqlite3.connect(args.RESULTS_DB)
    cur = con.cursor()
    # fetch requested information
    match args.list_choice:
        case "file_ids":
            print("dfile_id\tdfile_name")
            for dfid, dfname in cur.execute(_QUERIES["file_id"]).fetchall():
                print(f"{dfid}\t{dfname}")
    # clean up
    con.close()

 
#------------------------------------------------------------------------------
# dia calibrate_ccs subcommand


_CCS_DESCRIPTION = """
    TODO: description for dia calibrate_ccs subcommand
"""


def _setup_ccs_subparser(parser: argparse.ArgumentParser):
    """ set up the subparser for dia calibrate_ccs subcommand """
    parser.add_argument(
        "RESULTS_DB",
        help="results database file (.db)"
    )
    parser.add_argument(
        "T_FIX",
        type=float,
        help="t_fix CCS calibration parameter"
    )
    parser.add_argument(
        "BETA",
        type=float,
        help="beta CCS calibration parameter"
    )
    parser.add_argument(
        "DFILE_IDS",
        nargs="+",
        type=int,
        help="DIA data files to process (.mza)"
    )
    

def _ccs_run(args: argparse.Namespace):
    """ run function for dia calibrate_ccs subcommand """
    for dfid in args.DFILE_IDS:
        add_calibrated_ccs_to_dia_features(
            args.RESULTS_DB, dfid, args.T_FIX, args.BETA
        )


#------------------------------------------------------------------------------
# dia subcommand


DIA_DESCRIPTION = """
    TODO: This is a longer description for the dia subcommand
"""


def setup_dia_subparser(parser: argparse.ArgumentParser):
    """ set up the subparsers for dia subcommand """
    _subparsers = parser.add_subparsers(
        title="dia subcommand",
        required=True,
        dest="dia_subcommand"
    )
    # set up params subparser
    _setup_process_subparser(
            _subparsers.add_parser(
            "process", 
            help="extract and process DIA data",
            description=_PROCESS_DESCRIPTION
        )
    )
    # set up params subparser
    _setup_list_subparser(
            _subparsers.add_parser(
            "list", 
            help="get information about DIA data",
            description=_LIST_DESCRIPTION
        )
    )
    # set up params subparser
    _setup_ccs_subparser(
            _subparsers.add_parser(
            "calibrate_ccs", 
            help="add calibrated CCS to DIA precursors",
            description=_CCS_DESCRIPTION
        )
    )


def dia_run(args: argparse.Namespace): 
    """ run function for dia subcommand """
    match args.dia_subcommand:
        case "process":
            _process_run(args)
        case "list":
            _list_run(args)
        case "calibrate_ccs":
            _ccs_run(args)

