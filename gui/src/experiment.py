#!/usr/bin/env python3
import sys
import json
import subprocess
import os


def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install("pyyaml")
install("h5py")
install("hdf5plugin")
install("pandas")
install("mzapy")
# install("pyyaml")
# install("pyyaml")


#find imports
current_directory = os.path.dirname(os.path.abspath(__file__))
resources_directory = os.path.dirname(os.path.dirname(current_directory))
sys.path.append(resources_directory)


# #for  local:
# sys.path.append("../")

print("AAA: ", sys.path)

print("imports starting")
from LipidIMEA.msms import create_lipid_ids_db, load_params
print("import1 done")
from LipidIMEA.msms.dda import extract_dda_features, consolidate_dda_features
print("import2 done")
from LipidIMEA.msms.dia import extract_dia_features_multiproc
print("import3 done")
print("imports complete")




def convert_str(s):
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s

def convert_nest(d):
    for k, v in d.items():
        if isinstance(v, str):
            d[k] = convert_str(v)
        elif isinstance(v, dict):
            d[k] = convert_nest(v)
    return d

# inputValues= dict(json.loads(sys.argv[1]))

# print(inputValues)




def main():
    """
    Read in Inputs from GUI.
    Make calls to LipidIMEA.
    """
    #setup
    # params = load_params('old_defaults.yml')
    # params= dict(json.loads(sys.argv[1]))

    # print("SRC EXP")
    # print("Inputs:")
    # print(params)

    
    #TO DO - Allow user to create DB name and location.
    # And replace test_Df with it.
        
    
    # # create lipid IDs database, returns the filename
    # lipid_ids_db = create_lipid_ids_db(db_file,
    #                                 'test_db',
    #                                 overwrite=True,
    #                                 )
    # # directory for lipid IDs database, empty string for current directory
    # # base name for the lipid IDs database
    # # create a new database file if one alreadv exists
    
    # #DDA analvsis
    # extract_dda_features_multiproc(dda_files, # list of DDA data files
    # lipid_ids_db, # path to lipid IDs database
    # dda_inputs, # parameters for DDA portion of analysis
    # 1, # number of processes to run analysis with
    # debug_flag='text_pid') # produce text debugging messages with subprocess PIDs
    
    # print("Consolodate Here:")
    # consolidate_dda_features(lipid_ids_db,
    # dda_consol_inputs,
    # debug_flag='text')
    
    
    # # path to lipid IDs database
    # # parameters for DA feature consolidation
    # # produce text debugging messages (single process, no PIDs)
    # # DIA analysis
    
    
    # # print("First")
    # # print(params['PARAMETERS']['INPUT_OUTPUT']['dia_data_files'])
    # # print("Second")
    # # print(lipid_ids_db)
    # # print("Third")
    # # print( params['PARAMETERS']['DIA'])
    
    
    # extract_dia_features_multiproc(dia_files, # list of DIA data files
    # lipid_ids_db, # path to lipid IDs database
    # dia_inputs, # parameters for DIA portion of analvsis
    # 1, #number of processes to run analvsis with
    # debug_flag='text_pid') # produce text debugging messages with subprocess PIDs



    # lipid_ids_db = create_lipid_ids_db('',              # directory for lipid IDs database, empty string for current directory
    #                                    'insert_db_name_here',     # base name for the lipid IDs database
    #                                    overwrite=True,  # create a new database file if one already exists
    #                                    )

    # # DDA analysis
    # extract_dda_features_multiproc(params['INPUT_OUTPUT']['dda_data_files'],  # list of DDA data files
    #                                lipid_ids_db,                              # path to lipid IDs database
    #                                params['PARAMETERS']['DDA'],               # parameters for DDA portion of analysis
    #                                8,                                         # number of processes to run analysis with
    #                                debug_flag='text_pid',                     # produce text debugging messages with subprocess PIDs
    #                                )
    # consolidate_dda_features(lipid_ids_db,                                              # path to lipid IDs database
    #                          params['PARAMETERS']['DDA']['DDA_FEATURE_CONSOLIDATION'],  # parameters for DDA feature consolidation
    #                          debug_flag='text'                                          # produce text debugging messages (single process, no PIDs)
    #                          )

    # # DIA analysis
    # extract_dia_features_multiproc(params['INPUT_OUTPUT']['dia_data_files'],  # list of DIA data files
    #                                lipid_ids_db,                              # path to lipid IDs database
    #                                params['PARAMETERS']['DIA'],               # parameters for DIA portion of analysis
    #                                8,                                         # number of processes to run analysis with
    #                                debug_flag='text_pid',                     # produce text debugging messages with subprocess PIDs
    #                                )
    

    # setup
    # params = load_params('nist_test.yaml')

    # create lipid IDs database, returns the filename
    # input_output, params = load_params('nist_test.yaml')
    
    
    # input_output, params = dict(json.loads(sys.argv[1]))
    inputs_and_params = dict(json.loads(sys.argv[1]))
    input_output = inputs_and_params['input_output']
    params = inputs_and_params['params']
    
    print("input_output :", input_output)
    print("params :", params)
    
    
    params = convert_nest(params)

    # create lipid IDs database, returns the filename
    create_lipid_ids_db(input_output['lipid_ids_db'], overwrite=True)

    # DDA analysis
    if params['misc']['do_dda_processing']:
        for dda_data_file in input_output['dda_data_files']:
            extract_dda_features(dda_data_file,
                                 input_output['lipid_ids_db'],
                                 params,
                                 debug_flag='text')
        consolidate_dda_features(input_output['lipid_ids_db'],
                                 params,
                                 debug_flag='text')

    # DIA analysis
    if params['misc']['do_dia_processing']:
        extract_dia_features_multiproc(input_output['dia_data_files'],
                                       input_output['lipid_ids_db'], 
                                       params, 
                                       4, 
                                       debug_flag='text_pid')
    







if __name__ == '__main__':
    main()