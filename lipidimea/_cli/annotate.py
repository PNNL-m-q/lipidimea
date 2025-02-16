"""
lipidimea/_cli/annotate.py
Dylan Ross (dylan.ross@pnnl.gov)

    define CLI for annotation top-level subcommand
"""


import argparse

from lipidimea.annotation import (
    annotate_lipids
)


ANNOTATE_DESCRIPTION = """
    TODO: This is a longer description for the dia subcommand
"""


def setup_annotate_subparser(parser: argparse.ArgumentParser):
    """ set up the subparser for dia subcommand """
    parser.add_argument(
        "PARAMETERS",
        help="parameter config file (.yaml)"
    )
    parser.add_argument(
        "RESULTS_DB",
        help="results database file (.db)"
    )
    #assert False, "do we need anything else?"


def annotate_run(args: argparse.Namespace):
    """ perform lipid annotation """
    print(args)
    assert False, "TODO"

