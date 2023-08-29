
import sys
import json

#change directroy system so this is not needed
sys.path.insert(0, '/Users/jaco059/OneDrive - PNNL/Desktop/OZID_DDA_DIA_Project/lipidimea')
print("imports starting")
from LipidIMEA.msms import create_lipid_ids_db, load_params
print("import1 done")
from LipidIMEA.msms.dda import extract_dda_features_multiproc, consolidate_dda_features
print("import2 done")
from LipidIMEA.msms.dia import extract_dia_features_multiproc
print("import3 done")
print("imports complete")




# inputValues= dict(json.loads(sys.argv[1]))

# print("INPUT",inputValues)




def main():
    """
    Read in Inputs from GUI.
    Make calls to LipidIMEA.
    """
    #setup
    params = load_params('old_defaults.yml')
    input_values= dict(json.loads(sys.argv[1]))
    

    print("INPUT",input_values)
    dda_inputs = {}
    dia_inputs = {}
    # dda_files = []
    # dia_files = []
    # db_files = []

    for k, v in input_values.items():
        if "dda_data_files" in k:
            # dda_files.append(v)
            dda_files = v
        elif "dia_data_files" in k:
            # dia_files.append(v)
            dia_files = v
        elif "df_data_files" in k:
            # db_files.append(v)
            db_files = v
        elif "dda" in k:
            dda_inputs[k] = v
        elif "dia" in k:
            dia_inputs[k] = v


    print("\ndda_files: \n")
    print(dda_files)

    print("\ndia_files: \n")
    print(dia_files)
        
    print("\ndb_files: \n")
    print(db_files)
               
    print("\ndda_inputs: \n")
    print(dda_inputs)
                
    print("\ndia_inputs: \n")
    print(dia_inputs)
    
    
    
    
    # print("params:\n", type(params['PARAMETERS']['INPUT_OUTPUT']['dda_data_files']))
    
    
    # create lipid IDs database, returns the filename
    lipid_ids_db = create_lipid_ids_db('',
                                    'test_df',
                                    overwrite=True,
                                    )
    # directory for lipid IDs database, empty string for current directory
    # base name for the lipid IDs database
    # create a new database file if one alreadv exists
    
    
    
    
    # print("First")
    # print(params['PARAMETERS']['INPUT_OUTPUT']['dda_data_files'])
    # print("Second")
    # print(lipid_ids_db)
    # print("Third")
    # print(params['PARAMETERS']['DDA'])
    
    
    
    #DDA analvsis
    extract_dda_features_multiproc(params['PARAMETERS']['INPUT_OUTPUT']['dda_data_files'], # list of DDA data files
    lipid_ids_db, # path to lipid IDs database
    params['PARAMETERS']['DDA'], # parameters for DDA portion of analysis
    1, # number of processes to run analysis with
    debug_flag='text_pid') # produce text debugging messages with subprocess PIDs
    
    print("Consolodate Here:")
    consolidate_dda_features(lipid_ids_db,
    params['PARAMETERS']['DDA']['DDA_FEATURE_CONSOLIDATION'],
    debug_flag='text')
    
    
    # path to lipid IDs database
    # parameters for DA feature consolidation
    # produce text debugging messages (single process, no PIDs)
    # DIA analysis
    
    
    # print("First")
    # print(params['PARAMETERS']['INPUT_OUTPUT']['dia_data_files'])
    # print("Second")
    # print(lipid_ids_db)
    # print("Third")
    # print( params['PARAMETERS']['DIA'])
    
    
    extract_dia_features_multiproc(params['PARAMETERS']['INPUT_OUTPUT']['dia_data_files'], # list of DIA data files
    lipid_ids_db, # path to lipid IDs database
    params['PARAMETERS']['DIA'], # parameters for DIA portion of analvsis
    1, #number of processes to run analvsis with
    debug_flag='text_pid') # produce text debugging messages with subprocess PIDs

if __name__ == '__main__':
    main()