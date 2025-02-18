"""
lipidimea/_cli/annotate.py
Dylan Ross (dylan.ross@pnnl.gov)

    define CLI for annotation top-level subcommand
"""


import argparse

from lipidimea.params import AnnotationParams
from lipidimea.annotation import (
    annotate_lipids
)


ANNOTATE_DESCRIPTION = """
    TODO: This is a longer description for the dia subcommand
"""


def setup_annotate_subparser(parser: argparse.ArgumentParser):
    """ set up the subparser for annotate subcommand """
    parser.add_argument(
        "PARAMS_CONFIG",
        help="parameter config file (.yaml)"
    )
    parser.add_argument(
        "RESULTS_DB",
        help="results database file (.db)"
    )


def annotate_run(args: argparse.Namespace):
    """ perform lipid annotation """
    # load the parameters
    params = AnnotationParams.from_config(args.PARAMS_CONFIG)
    # annotate lipids
    _ = annotate_lipids(args.RESULTS_DB, params, debug_flag="text")

