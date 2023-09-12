# import sys
# import subprocess

# print("Python version")
# print (sys.version)

# print("Version info.")
# print (sys.version_info)



# def install(package):
#     subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# install("pyyaml")

# import json
# import yaml


# # write yaml file.
# inputValues= dict(json.loads(sys.argv[1]))

# with open('data.yaml', 'w') as f:
#     yaml.dump(inputValues, f)



# import sys
# import json
# import yaml


# # write yaml file.
# inputValues= dict(json.loads(sys.argv[1]))

# with open('data.yaml', 'w') as f:
#     yaml.dump(inputValues, f)

from collections import OrderedDict
import yaml
import json
import sys

# Ensure that you maintain order when loading the JSON
input_values = json.loads(sys.argv[1], object_pairs_hook=OrderedDict)





def flatten_to_nested_structure(input_dict):
    nested_structure = {
        "INPUT_OUTPUT": {},
        "PARAMETERS": {
            "dda": {},
            "dia": {},
            "annotation": {}
        }
    }

    for key, value in input_dict.items():
        parts = key.split('_')
        if len(parts) == 2:
            section, param = parts
            nested_structure['PARAMETERS']['dda'][param] = value
        elif len(parts) == 3:
            section, sub_section, param = parts
            if section == "DIA":
                if sub_section not in nested_structure['PARAMETERS']['dia']:
                    nested_structure['PARAMETERS']['dia'][sub_section] = {}
                nested_structure['PARAMETERS']['dia'][sub_section][param] = value
            else:
                nested_structure['PARAMETERS'][section][param] = value

    return nested_structure


input_values = dict(json.loads(sys.argv[1]))
nested_dict = flatten_to_nested_structure(input_values)




# with open('data.yaml', 'w') as f:
#     yaml.dump(input_values, f, default_flow_style=False, sort_keys=False)



save_path = sys.argv[2] if len(sys.argv) > 2 else 'saved_lipidmea_params.yaml'

with open(save_path, 'w') as f:
    yaml.dump(input_values, f, default_flow_style=False, sort_keys=False)