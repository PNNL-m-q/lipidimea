#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os

# Locate the bundled lipidimea CLI binary (extraResource in package.json)
CLI = os.path.join(os.path.dirname(__file__), "..", "lipidimea")
# Fallback to system‐installed if not found
if not os.path.exists(CLI):
    CLI = "lipidimea"


def execute_command(cmd):
    """Execute a command and exit on error."""
    print("Executing:", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit(result.returncode)


def create_db(db_name):
    execute_command([CLI, "utility", "create_db", db_name])


def load_params(default_dda, default_dia, default_ann):
    if default_dda:
        execute_command([CLI, "utility", "params", "--default-dda", default_dda])
    if default_dia:
        execute_command([CLI, "utility", "params", "--default-dia", default_dia])
    if default_ann:
        execute_command([CLI, "utility", "params", "--default-ann", default_ann])


def run_dda(config_dda, db_name, dda_files):
    cmd = [CLI, "dda", config_dda, db_name] + dda_files
    execute_command(cmd)


def run_dia(config_dia, db_name, dia_files):
    cmd = [CLI, "dia", "process", config_dia, db_name] + dia_files
    execute_command(cmd)


def calibrate_dia(db_name, t_fix, beta, calib_files):
    cmd = [CLI, "dia", "calibrate_ccs", db_name, t_fix, beta] + calib_files
    execute_command(cmd)


def annotate(config_ann, db_name):
    execute_command([CLI, "annotate", config_ann, db_name])


def run_all(args):
    print("=== Creating SQL database ===")
    create_db(args.db_name)

    print("=== Loading default parameters ===")
    load_params(args.config_dda, args.config_dia, args.config_ann)

    if args.dda_files:
        print("=== Running DDA Experiment ===")
        run_dda(args.config_dda, args.db_name, args.dda_files)

    if args.dia_files:
        print("=== Running DIA Experiment ===")
        run_dia(args.config_dia, args.db_name, args.dia_files)

    if args.calib_files:
        print("=== Calibrating DIA CCS ===")
        calibrate_dia(args.db_name, args.T_FIX_param, args.BETA_param, args.calib_files)

    print("=== Annotating Lipids ===")
    annotate(args.config_ann, args.db_name)


def main():
    parser = argparse.ArgumentParser(
        description="Wrapper for lipidimea CLI commands."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create_db
    p = subparsers.add_parser("create_db", help="Create SQL database")
    p.add_argument("db_name", help="Name of the database")
    p.set_defaults(func=lambda args: create_db(args.db_name))

    # params
    p = subparsers.add_parser("params", help="Load default parameter configs")
    p.add_argument("--default-dda", help="Path for default DDA config", default=None)
    p.add_argument("--default-dia", help="Path for default DIA config", default=None)
    p.add_argument("--default-ann", help="Path for default annotation config", default=None)
    p.set_defaults(func=lambda args: load_params(args.default_dda, args.default_dia, args.default_ann))

    # dda
    p = subparsers.add_parser("dda", help="Run DDA experiment")
    p.add_argument("config_dda", help="DDA config file")
    p.add_argument("db_name", help="Database file")
    p.add_argument("dda_files", nargs="+", help="DDA data files")
    p.set_defaults(func=lambda args: run_dda(args.config_dda, args.db_name, args.dda_files))

    # dia
    p = subparsers.add_parser("dia", help="Run DIA experiment")
    p.add_argument("config_dia", help="DIA config file")
    p.add_argument("db_name", help="Database file")
    p.add_argument("dia_files", nargs="+", help="DIA data files")
    p.set_defaults(func=lambda args: run_dia(args.config_dia, args.db_name, args.dia_files))

    # calibrate
    p = subparsers.add_parser("calibrate", help="Calibrate DIA CCS")
    p.add_argument("db_name", help="Database file")
    p.add_argument("T_FIX_param", help="T_FIX CCS parameter")
    p.add_argument("BETA_param", help="BETA CCS parameter")
    p.add_argument("calib_files", nargs="+", help="Files to calibrate")
    p.set_defaults(func=lambda args: calibrate_dia(args.db_name, args.T_FIX_param, args.BETA_param, args.calib_files))

    # annotate
    p = subparsers.add_parser("annotate", help="Run lipid annotation")
    p.add_argument("config_ann", help="Annotation config file")
    p.add_argument("db_name", help="Database file")
    p.set_defaults(func=lambda args: annotate(args.config_ann, args.db_name))

    # all
    p = subparsers.add_parser("all", help="Run all steps sequentially")
    p.add_argument("db_name", help="Database file")
    p.add_argument("config_dda", help="DDA config file")
    p.add_argument("config_dia", help="DIA config file")
    p.add_argument("config_ann", help="Annotation config file")
    p.add_argument("--dda_files", nargs="+", required=True, help="DDA data files")
    p.add_argument("--dia_files", nargs="+", required=True, help="DIA data files")
    p.add_argument("--calib_files", nargs="+", help="Calibration files (optional)")
    p.add_argument("--T_FIX_param", default="default_T_FIX", help="T_FIX param")
    p.add_argument("--BETA_param", default="default_BETA", help="BETA param")
    p.set_defaults(func=run_all)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()