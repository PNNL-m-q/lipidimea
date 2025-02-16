"""
lipidimea/_cli/dda.py
Dylan Ross (dylan.ross@pnnl.gov)

    define CLI for dda top-level subcommand
"""


import argparse

from lipidimea.msms.dda import (
    extract_dda_features,
    extract_dda_features_multiproc
)


DDA_DESCRIPTION = """
    TODO: This is a longer description for the dda subcommand
"""


def setup_dda_subparser(parser: argparse.ArgumentParser):
    """ set up the subparser for dda subcommand """
    parser.add_argument(
        "PARAMETERS",
        help="parameter config file (.yaml)"
    )
    parser.add_argument(
        "RESULTS_DB",
        help="results database file (.db)"
    )
    #assert False, "Collect .mza DDA data files somehow..."



def dda_run(args: argparse.Namespace):
    """ perform DDA data extraction and processing """
    print(args)
    assert False, "TODO"
