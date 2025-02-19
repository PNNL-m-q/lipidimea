"""
lipidimea/_cli/utility.py
Dylan Ross (dylan.ross@pnnl.gov)

    define CLI for utility top-level subcommand
"""


import argparse

from lipidimea.params import DdaParams, DiaParams, AnnotationParams
from lipidimea.util import create_results_db, export_results_table


#------------------------------------------------------------------------------
# utility params subcommand


_PARAMS_DESCRIPTION = """
    Load default parameter configs
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
    Initialize the results database
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
# utility export subcommand


_EXPORT_DESCRIPTION = """
    Export analysis results to CSV
"""


def _setup_export_subparser(parser: argparse.ArgumentParser):
    """ setup subparser for utility export subcommand """
    parser.add_argument(
        "RESULTS_DB",
        help="results database file (.db)"
    )
    parser.add_argument(
        "OUT_CSV",
        help="export to file name (.csv)"
    )
    parser.add_argument(
        "--mz-tol", 
        type=float,
        default=0.025,
        help="m/z tolerance for grouping features (default=0.025)"
    )
    parser.add_argument(
        "--rt-tol", 
        type=float,
        default=0.25,
        help="retention time tolerance for grouping features (default=0.25)"
    )
    parser.add_argument(
        "--at-tol", 
        type=float,
        default=2.5,
        help="arrival time tolerance for grouping features (default=2.5)"
    )
    parser.add_argument(
        "--abundance",
        choices=[
            "height", "area"
        ],
        default="area",
        help="use arrival time peak height or area for feature abundance (default='area')"
    )
    parser.add_argument(
        "--annotation-combine-strategy",
        choices=[
            "intersection", "union"
        ],
        default="union",
        help="strategy for combining annotations among grouped features (default='union')"
    )
    parser.add_argument(
        "--max-precursor-ppm",
        type=float,
        default=40.,
        help="max ppm error for annotated precursor m/z (default=40.)"
    )
    parser.add_argument(
        "--include-unknowns",
        action="store_true",
        default=False,
        help="set this to export DIA features that do not have any lipid annotations"
    )
    parser.add_argument(
        "DFILE_ID",
        nargs="+",
        type=int,
        help="DIA data file IDs to include in exported results"
    )


def _export_run(args: argparse.Namespace):
    """ run function for utility export subcommand """
    _ = export_results_table(
        args.RESULTS_DB, 
        args.OUT_CSV, 
        (args.mz_tol, args.rt_tol, args.at_tol), 
        args.DFILE_ID, 
        # it's dt_height or dt_area, add the dt_ to the front
        abundance_value="dt_" + args.abundance, 
        include_unknowns=args.include_unknowns, 
        limit_precursor_mz_ppm=args.max_precursor_ppm, 
        annotation_combine_strategy=args.annotation_combine_strategy
    )


#------------------------------------------------------------------------------
# utility subcommand


UTILITY_DESCRIPTION = """
    General utilities
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
    # set up create_db subparser
    _setup_create_db_subparser(
            _subparsers.add_parser(
            "create_db", 
            help="create results database",
            description=_CREATE_DB_DESCRIPTION
        )
    )
    # set up export subparser
    _setup_export_subparser(
            _subparsers.add_parser(
            "export", 
            help="export results to CSV",
            description=_EXPORT_DESCRIPTION
        )
    )


def utility_run(args: argparse.Namespace): 
    """ run function for utility subcommand """
    match args.utility_subcommand:
        case "params":
            _params_run(args)
        case "create_db":
            # no need for separate "run" function
            create_results_db(args.RESULTS_DB, overwrite=args.overwrite)
        case "export":
            _export_run(args)