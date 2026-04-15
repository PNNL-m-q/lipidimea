"""
lipidimea/_cli/__init__.py
Dylan Ross (dylan.ross@pnnl.gov)

    internal package defining a command-line interface for performing data extraction and processing
"""


import argparse

from lipidimea._cli.utility import UTILITY_DESCRIPTION, setup_utility_subparser, utility_run
from lipidimea._cli.dda import DDA_DESCRIPTION, setup_dda_subparser, dda_run
from lipidimea._cli.dia import DIA_DESCRIPTION, setup_dia_subparser, dia_run
from lipidimea._cli.annotate import ANNOTATE_DESCRIPTION, setup_annotate_subparser, annotate_run


#------------------------------------------------------------------------------
# top-level


_TOP_LEVEL_DESCRIPTION = """
    Lipidomics Integrated Multi-Experiment Analysis tool
"""


def _setup_top_level_parser():
    """ set up the top-level argument parser """
    parser = argparse.ArgumentParser(
        prog="LipidIMEA",
        description=_TOP_LEVEL_DESCRIPTION
    )
    _subparsers = parser.add_subparsers(
        title="subcommands", 
        required=True,
        dest="subcommand"
    )
    # set up utility subparser
    setup_utility_subparser(
            _subparsers.add_parser(
            "utility", 
            help="utility functions", 
            description=UTILITY_DESCRIPTION
        )
    )
    # set up dda subparser
    setup_dda_subparser(
            _subparsers.add_parser(
            "dda", 
            help="DDA data extraction and processing", 
            description=DDA_DESCRIPTION
        )
    )
    # set up dia subparser
    setup_dia_subparser(
        _subparsers.add_parser(
            "dia", 
            help="DIA data extraction and processing",
            description=DIA_DESCRIPTION
        )
    )
    # set up annotate subparser
    setup_annotate_subparser(
            _subparsers.add_parser(
            "annotate", 
            help="perform lipid annotation", 
            description=ANNOTATE_DESCRIPTION
        )
    )
    return parser


def run():
    args = _setup_top_level_parser().parse_args()
    match args.subcommand:
        case "utility":
            utility_run(args)
        case "dda":
            dda_run(args)
        case "dia":
            dia_run(args)
        case "annotate":
            annotate_run(args)
        