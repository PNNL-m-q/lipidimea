"""
lipidimea/_cli/utility.py
Dylan Ross (dylan.ross@pnnl.gov)

    define CLI for utility top-level subcommand
"""


import argparse

from lipidimea.params import DdaParams, DiaParams, AnnotationParams
from lipidimea.util import create_results_db


#------------------------------------------------------------------------------
# utility params subcommand


_PARAMS_DESCRIPTION = """
    TODO: description for the utility params subcommand
"""


def _setup_params_subparser(parser: argparse.ArgumentParser):
    """ setup subparser for utility params subcommand """
    parser.add_argument(
        "--default-dda",
        metavar="CONFIG",
        dest="DDA_CONFIG",
        default=None,
        help="load the default DDA parameters config (YAML), write to specified path"
    )
    parser.add_argument(
        "--default-dia",
        metavar="CONFIG",
        dest="DIA_CONFIG",
        default=None,
        help="load the default DIA parameters config (YAML), write to specified path"
    )
    parser.add_argument(
        "--default-ann",
        metavar="CONFIG",
        dest="ANN_CONFIG",
        default=None,
        help="load the default lipid annotation parameters config (YAML), write to specified path"
    )


def _params_run(args: argparse.Namespace):
    """ run function for utility params subcommand """
    if args.DDA_CONFIG is not None:
        DdaParams.load_default().write_config(args.DDA_CONFIG, include_unchanged=True)
    if args.DIA_CONFIG is not None:
        DiaParams.load_default().write_config(args.DIA_CONFIG, include_unchanged=True)
    if args.ANN_CONFIG is not None:
        AnnotationParams.load_default().write_config(args.ANN_CONFIG, include_unchanged=True)


#------------------------------------------------------------------------------
# utility create_db subcommand


_CREATE_DB_DESCRIPTION = """
    TODO: description for the utility create_db subcommand
"""


def _setup_create_db_subparser(parser: argparse.ArgumentParser):
    """ setup subparser for utility create_db subcommand """
    parser.add_argument(
        "RESULTS_DB",
        help="results database file (.db)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="overwrite the results database file if it already exists"
    )


#------------------------------------------------------------------------------
# utility subcommand


UTILITY_DESCRIPTION = """
    TODO: This is a longer description for the utility subcommand
"""


def setup_utility_subparser(parser: argparse.ArgumentParser):
    """ set up the subparsers for utility subcommand """
    _subparsers = parser.add_subparsers(
        title="utility subcommand",
        required=True,
        dest="utility_subcommand"
    )
    # set up params subparser
    _setup_params_subparser(
            _subparsers.add_parser(
            "params", 
            help="manage parameters",
            description=_PARAMS_DESCRIPTION
        )
    )
    # set up params subparser
    _setup_create_db_subparser(
            _subparsers.add_parser(
            "create_db", 
            help="create results database",
            description=_CREATE_DB_DESCRIPTION
        )
    )


def utility_run(args: argparse.Namespace): 
    """
    """
    match args.utility_subcommand:
        case "params":
            _params_run(args)
        case "create_db":
            # no need for separate "run" function
            create_results_db(args.RESULTS_DB, overwrite=args.overwrite)