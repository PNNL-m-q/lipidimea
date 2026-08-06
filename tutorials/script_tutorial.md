# Overview
This tutorial covers complete analysis of example data in an automated fashion using a Python script and the `lipidimea` Python package API:

- Extract and process DDA features from sequential DDA data files
- Using the extracted DDA features as targets, extract and process DIA features from individual DIA data files
- Perform lipid annotation on DIA features
- Export results (DIA features + lipid annotations) to CSV for downstream analysis

This tutorial performs the same analysis as in the [CLI tutorial](cli_tutorial.md).

# Setup

See [tutorial setup instructions](setup.md)

# Run the Analysis

The data analysis script [example.py](example.py) will perform all of the data analysis steps outlined above, ultimately producing a results database (`compref/results/pos_script.db`) and an exported CSV (`compref/results/pos_script.csv`). 

```shell
python3 example.py
```
