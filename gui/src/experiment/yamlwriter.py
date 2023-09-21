# Importing required libraries
import yaml
import json
import sys


if __name__ == "__main__":
    # Ensure order preservation when loading the JSON
    input_values = dict(json.loads(sys.argv[1]))
    
    # Determine save path, defaulting to 'saved_lipidmea_params.yaml'
    save_path = sys.argv[2] if len(sys.argv) > 2 else 'saved_lipidmea_params.yaml'

    # Write the transformed data to the specified YAML file
    with open(save_path, 'w') as f:
        yaml.dump(input_values, f, default_flow_style=False, sort_keys=False)