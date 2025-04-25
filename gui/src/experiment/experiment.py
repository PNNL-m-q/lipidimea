#!/usr/bin/env python3
import argparse
import subprocess
import sys

def execute_command(cmd):
    """Execute a command and exit on error."""
    print("Executing:", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit(result.returncode)

def create_db(db_name):
    execute_command(["python3.12", "-m", "lipidimea", "utility", "create_db", db_name])

def load_params(default_dda, default_dia, default_ann):
    if default_dda:
        execute_command(["python3.12", "-m", "lipidimea", "utility", "params", "--default-dda", default_dda])
    if default_dia:
        execute_command(["python3.12", "-m", "lipidimea", "utility", "params", "--default-dia", default_dia])
    if default_ann:
        execute_command(["python3.12", "-m", "lipidimea", "utility", "params", "--default-ann", default_ann])

def run_dda(config_dda, db_name, dda_files):
    cmd = ["python3.12", "-m", "lipidimea", "dda", config_dda, db_name] + dda_files
    execute_command(cmd)

def run_dia(config_dia, db_name, dia_files):
    cmd = ["python3.12", "-m", "lipidimea", "dia", "process", config_dia, db_name] + dia_files
    execute_command(cmd)

def calibrate_dia(db_name, t_fix, beta, calib_files):
    cmd = ["python3.12", "-m", "lipidimea", "dia", "calibrate_ccs", db_name, t_fix, beta] + calib_files
    execute_command(cmd)

def annotate(config_ann, db_name):
    execute_command(["python3.12", "-m", "lipidimea", "annotate", config_ann, db_name])

def run_all(args):
    # Sequentially run all steps.
    print("=== Creating SQL database ===")
    create_db(args.db_name)

    print("=== Loading default parameters ===")
    load_params(args.config_dda, args.config_dia, args.config_ann)

    print("=== Running DDA Experiment ===")
    run_dda(args.config_dda, args.db_name, args.dda_files)

    print("=== Running DIA Experiment ===")
    run_dia(args.config_dia, args.db_name, args.dia_files)

    if args.calib_files:
        print("=== Calibrating DIA CSS ===")
        calibrate_dia(args.db_name, args.T_FIX_param, args.BETA_param, args.calib_files)

    print("=== Annotating Lipids ===")
    annotate(args.config_ann, args.db_name)

def main():
    parser = argparse.ArgumentParser(
        description="Wrapper for lipidimea CLI commands."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create_db subcommand
    parser_create = subparsers.add_parser("create_db", help="Create SQL database")
    parser_create.add_argument("db_name", help="Name of the database")
    parser_create.set_defaults(func=lambda args: create_db(args.db_name))

    # params subcommand
    parser_params = subparsers.add_parser("params", help="Load default configuration parameters")
    parser_params.add_argument("--default-dda", help="Configuration name for DDA", default=None)
    parser_params.add_argument("--default-dia", help="Configuration name for DIA", default=None)
    parser_params.add_argument("--default-ann", help="Configuration name for Annotation", default=None)
    parser_params.set_defaults(func=lambda args: load_params(args.default_dda, args.default_dia, args.default_ann))

    # dda subcommand
    parser_dda = subparsers.add_parser("dda", help="Run DDA experiment")
    parser_dda.add_argument("config_dda", help="Configuration name for DDA")
    parser_dda.add_argument("db_name", help="Name of the database")
    parser_dda.add_argument("dda_files", nargs="+", help="List of DDA files")
    parser_dda.set_defaults(func=lambda args: run_dda(args.config_dda, args.db_name, args.dda_files))

    # dia subcommand
    parser_dia = subparsers.add_parser("dia", help="Run DIA experiment")
    parser_dia.add_argument("config_dia", help="Configuration name for DIA")
    parser_dia.add_argument("db_name", help="Name of the database")
    parser_dia.add_argument("dia_files", nargs="+", help="List of DIA files")
    parser_dia.set_defaults(func=lambda args: run_dia(args.config_dia, args.db_name, args.dia_files))

    # calibrate subcommand
    parser_calib = subparsers.add_parser("calibrate", help="Calibrate DIA CSS")
    parser_calib.add_argument("db_name", help="Name of the database")
    parser_calib.add_argument("T_FIX_param", help="T_FIX parameter")
    parser_calib.add_argument("BETA_param", help="BETA parameter")
    parser_calib.add_argument("calib_files", nargs="+", help="List of DIA files for calibration")
    parser_calib.set_defaults(func=lambda args: calibrate_dia(args.db_name, args.T_FIX_param, args.BETA_param, args.calib_files))

    # annotate subcommand
    parser_annotate = subparsers.add_parser("annotate", help="Annotate lipids")
    parser_annotate.add_argument("config_ann", help="Configuration name for Annotation")
    parser_annotate.add_argument("db_name", help="Name of the database")
    parser_annotate.set_defaults(func=lambda args: annotate(args.config_ann, args.db_name))

    # all subcommand to run every step sequentially.
    parser_all = subparsers.add_parser("all", help="Run all steps sequentially")
    parser_all.add_argument("db_name", help="Name of the database")
    parser_all.add_argument("config_dda", help="Configuration for DDA (used as default for parameters)")
    parser_all.add_argument("config_dia", help="Configuration for DIA (used as default for parameters)")
    parser_all.add_argument("config_ann", help="Configuration for Annotation (used as default for parameters)")
    parser_all.add_argument("--dda_files", nargs="+", required=True, help="List of DDA files")
    parser_all.add_argument("--dia_files", nargs="+", required=True, help="List of DIA files")
    parser_all.add_argument("--calib_files", nargs="+", help="List of DIA files for calibration (optional)")
    parser_all.add_argument("--T_FIX_param", default="default_T_FIX", help="T_FIX parameter for calibration")
    parser_all.add_argument("--BETA_param", default="default_BETA", help="BETA parameter for calibration")
    parser_all.set_defaults(func=run_all)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()










############################################################################################################
########################### Original Script ########################### 
############################################################################################################


# #!/usr/bin/env python3

# import multiprocessing
# import sys
# import json
# import subprocess
# import os
# import shutil

# from lipidimea.util import create_results_db, load_params
# from lipidimea.msms.dda import extract_dda_features, consolidate_dda_features
# from lipidimea.msms.dia import extract_dia_features_multiproc
# from lipidimea.lipids.annotation import annotate_lipids_sum_composition, filter_annotations_by_rt_range


# #Python Calls to lipidimea



# def convert_str(s):
#     try:
#         return int(s)
#     except ValueError:
#         try:
#             return float(s)
#         except ValueError:
#             return s

# def convert_nest(d):
#     for k, v in d.items():
#         if isinstance(v, str):
#             d[k] = convert_str(v)
#         elif isinstance(v, dict):
#             d[k] = convert_nest(v)
#     return d


# def generate_new_db_name(directory, db_name):
#     base_name = db_name
#     version = 1
#     while os.path.exists(os.path.join(directory, db_name + '.db')):
#         db_name = f"{base_name}_v{version}"
#         version += 1
#     return db_name + '.db'



# def main():
#     """
#     Read in Inputs from GUI.
#     Make calls to lipidimea.
#     """
 
#     inputs_and_params = dict(json.loads(sys.argv[1]))
#     input_output = inputs_and_params['input_output']
#     params = inputs_and_params['params']
#     options = inputs_and_params['options']
    
    
#     params = convert_nest(params)
    

#     #assign False if 'results_db' not present.
#     if input_output.get('results_db') is None:
#         input_output['results_db'] = None
        
        
#     #If database is present, append.
#     if options["db_pick"] == "append" and input_output['results_db']:
#         pass
#     elif options["db_pick"] == "overwrite" and input_output['results_db']:
#         create_results_db(input_output['results_db'], overwrite=True)
#     elif options["db_pick"] == "create_new" and not input_output['results_db']:
#         generate_new_db_name(options['save_loc'], options['db_name'])
#         exp_name = os.path.join(options["save_loc"], options["db_name"] + ".db")
#         create_results_db(exp_name, overwrite=True)
#         input_output['results_db'] = exp_name
#     else:
#         print("conditions incorrect. exiting")
#         sys.exit()


#     if input_output['lipid_class_scdb_config'] == []:
#         input_output['lipid_class_scdb_config'] = None
        
#     if 'lipid_class_rt_ranges' not in input_output:
#         input_output['lipid_class_rt_ranges'] = None
    



#     # DDA analysis
#     if params['misc']['do_dda_processing']:
#         for dda_data_file in input_output['dda_data_files']:
#             extract_dda_features(dda_data_file,
#                                  input_output['results_db'],
#                                  params,
#                                  debug_flag='text')
#             consolidate_dda_features(input_output['results_db'],
#                                  params,
#                                  debug_flag='text')
#         print("\n\nDDA Extraction Complete\n\n")

#     # DIA analysis
#     if params['misc']['do_dia_processing']:
#         extract_dia_features_multiproc(input_output['dia_data_files'],
#                                        input_output['results_db'], 
#                                        params,
#                                        4,
#                                        debug_flag='text_pid')
#         print("\n\nDIA Extraction Complete\n\n")


#     #  Annotation
#     if params['misc']['do_annotation']:
#         annotate_lipids_sum_composition(input_output['results_db'],
#                                         input_output['lipid_class_scdb_config'],
#                                         params,
#                                         debug_flag='text')
#         #  input_output['lipid_class_rt_ranges'] doesn't exist yet.
#         filter_annotations_by_rt_range(input_output['results_db'],
#                                        input_output['lipid_class_rt_ranges'],
#                                        params,
#                                        debug_flag='text')
#         print("\n\nAnnotation Complete\n\n")


# if __name__ == '__main__':
#     print("Starting up Experiment...")
#     multiprocessing.freeze_support()
#     multiprocessing.set_start_method('spawn')
#     main()
