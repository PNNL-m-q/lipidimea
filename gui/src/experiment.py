#!/usr/bin/env python3
import sys
import json
import subprocess
import os
import shutil


def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install("pyyaml")
install("h5py")
install("hdf5plugin")
install("pandas")
install("mzapy")



#find imports
current_directory = os.path.dirname(os.path.abspath(__file__))
resources_directory = os.path.dirname(os.path.dirname(current_directory))
sys.path.append(resources_directory)


# #for  local:
# sys.path.append("../")

print("AAA: ", sys.path)

print("imports starting")
from LipidIMEA.util import create_results_db, load_params
print("import1 done")
from LipidIMEA.msms.dda import extract_dda_features, consolidate_dda_features
print("import2 done")
from LipidIMEA.msms.dia import extract_dia_features_multiproc
print("import3 done")
from LipidIMEA.lipids.annotation import annotate_lipids_sum_composition, filter_annotations_by_rt_range
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

def generate_new_db_name(directory, db_name):
    base_name = db_name
    version = 1
    while os.path.exists(os.path.join(directory, db_name + '.db')):
        db_name = f"{base_name}_v{version}"
        version += 1
    return db_name + '.db'



def main():
    """
    Read in Inputs from GUI.
    Make calls to LipidIMEA.
    """
 
    inputs_and_params = dict(json.loads(sys.argv[1]))
    input_output = inputs_and_params['input_output']
    params = inputs_and_params['params']
    options = inputs_and_params['options']
    
    print("input_output :", input_output)
    print("params :", params)
    print("options :", options)
    
        
    # if input_output['lipid_class_scdb_config']:
    #     params["annotation"]["ann_sum_comp"]["ann_sc_lipid_class_params"] = input_output['annotation_file']

    print("\n new params :", params)
    
    # db_pick: getSelectedDatabaseOption(),
    # db_name: document.getElementById("experiment-name"),
    # save_loc: document.getElementById("selected-directory")
    
    
    params = convert_nest(params)
    
    
    print("check here before:",input_output)
    #assign False if 'results_db' not present.
    if input_output.get('results_db') is None:
        input_output['results_db'] = None
        
    print("check here after:",input_output)
    # create lipid IDs database, returns the filename
    
    

        
        
    #If database is present, append.
    if options["db_pick"] == "append" and input_output['results_db']:
        pass
    elif options["db_pick"] == "overwrite" and input_output['results_db']:
        create_results_db(input_output['results_db'], overwrite=True)
    elif options["db_pick"] == "create_new" and not input_output['results_db']:
        generate_new_db_name(options['save_loc'], options['db_name'])
        exp_name = os.path.join(options["save_loc"], options["db_name"] + ".db")
        create_results_db(exp_name, overwrite=True)
        input_output['results_db'] = exp_name
    else:
        print("conditions incorrect. exiting")
        sys.exit()


    if input_output['lipid_class_scdb_config'] == []:
        input_output['lipid_class_scdb_config'] = None
        
    if 'lipid_class_rt_ranges' not in input_output:
        input_output['lipid_class_rt_ranges'] = None
    



    # DDA analysis
    if params['misc']['do_dda_processing']:
        for dda_data_file in input_output['dda_data_files']:
            extract_dda_features(dda_data_file,
                                 input_output['results_db'],
                                 params,
                                 debug_flag='text')
            consolidate_dda_features(input_output['results_db'],
                                 params,
                                 debug_flag='text')

    # DIA analysis
    if params['misc']['do_dia_processing']:
        extract_dia_features_multiproc(input_output['dia_data_files'],
                                       input_output['results_db'], 
                                       params, 
                                       4, 
                                       debug_flag='text_pid')
    


    print("\n\nExtraction Complete\n\n")


    #  Annotation
    if params['misc']['do_annotation']:
        annotate_lipids_sum_composition(input_output['results_db'],
                                        input_output['lipid_class_scdb_config'],
                                        params,
                                        debug_flag='text')
        #  input_output['lipid_class_rt_ranges'] doesn't exist yet.
        filter_annotations_by_rt_range(input_output['results_db'],
                                       input_output['lipid_class_rt_ranges'],
                                       params, 
                                       debug_flag='text')



    print("\n\Annotation Complete\n\n")


if __name__ == '__main__':
    main()