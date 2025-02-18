"""
lipidimea/_cli/dda.py
Dylan Ross (dylan.ross@pnnl.gov)

    define CLI for dda top-level subcommand
"""


import argparse

from lipidimea.params import DdaParams
from lipidimea.msms.dda import (
    extract_dda_features,
    extract_dda_features_multiproc,
    consolidate_dda_features
)


DDA_DESCRIPTION = """
    TODO: This is a longer description for the dda subcommand
"""


def setup_dda_subparser(parser: argparse.ArgumentParser):
    """ set up the subparser for dda subcommand """
    parser.add_argument(
        "PARAMS_CONFIG",
        help="parameter config file (.yaml)"
    )
    parser.add_argument(
        "RESULTS_DB",
        help="results database file (.db)"
    )
    parser.add_argument(
        "DDA_MZA",
        nargs="*",
        help="DDA data files to process (.mza)"
    )
    parser.add_argument(
        "--n-proc",
        default=1,
        type=int,
        help="set >1 to processes multiple data files in parallel (default=1)"
    )
    parser.add_argument(
        "--no-consolidate",
        dest="consolidate",
        default=True,
        action="store_false",
        help="do not consolidate DDA features after extraction"
    )


def dda_run(args: argparse.Namespace):
    """ perform DDA data extraction and processing """
    # load the parameters
    params = DdaParams.from_config(args.PARAMS_CONFIG)
    # extract the DDA features
    if args.n_proc > 1:
        _ = extract_dda_features_multiproc(
            args.DDA_MZA, args.RESULTS_DB, params, n_proc=args.n_proc, debug_flag="text_pid"
        )
    else:
        for dda_data_file in args.DDA_MZA:
            _ = extract_dda_features(
                dda_data_file, args.RESULTS_DB, params, debug_flag="text"
            )
    # consolidate DDA features after extraction
    if args.consolidate:
        consolidate_dda_features(args.RESULTS_DB, params, debug_flag="text")