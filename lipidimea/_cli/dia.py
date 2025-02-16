"""
lipidimea/_cli/dia.py
Dylan Ross (dylan.ross@pnnl.gov)

    define CLI for dia top-level subcommand
"""


import argparse

from lipidimea.msms.dia import (
    extract_dia_features,
    extract_dia_features_multiproc
)


DIA_DESCRIPTION = """
    TODO: This is a longer description for the dia subcommand
"""


def setup_dia_subparser(parser: argparse.ArgumentParser):
    """ set up the subparser for dia subcommand """
    parser.add_argument(
        "PARAMETERS",
        help="parameter config file (.yaml)"
    )
    parser.add_argument(
        "RESULTS_DB",
        help="results database file (.db)"
    )
    #assert False, "Collect .mza DIA data files somehow..."


def dia_run(args: argparse.Namespace):
    """ perform DIA data extraction and processing """
    print(args)
    assert False, "TODO"
