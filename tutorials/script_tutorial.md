# Overview
This tutorial covers complete analysis of example data in an automated fashion using a Python script and the `lipidimea` Python package API:

- Extract and process DDA features from sequential DDA data files
- Using the extracted DDA features as targets, extract and process DIA features from individual DIA data files
- Perform lipid annotation on DIA features
- Export results (DIA features + lipid annotations) to CSV for downstream analysis

This tutorial performs the same analysis as in the [CLI tutorial](cli_tutorial.md).

# Setup

## Directory Structure

To follow this tutorial create the following directories in your desired working directory:

- `configs/` <- for data extraction and processing parameter configuration files
- `mza/` <- for raw data files in MZA format
- `results/` <- results database file and exported CSV

## Python and `lipidimea` package

This tutorial uses Python 3.12 and the `lipidimea` python package to perform analysis

> The `lipidimea` Python package must be either be installed (_i.e._, clone repository, run `pip install lipidimea`) or copied into this directory before running the tutorial. Installation can be performed in a virtual environment as well if desired.

> This tutorial was written using a MacOS system, on which the Python 3.12 executable is named `python3`. This may differ slightly on other plaforms like Windows. Simply substitute `python3` with whatever the correct invocation of the Python 3.12 interpreter is on your system if it differs. 

## Raw Data

- The tutorial expects raw data files (in MZA format) in the `mza/` directory
- Raw data files used in this tutorial can be downloaded from: [URL]()

### DDA

"SuperPool" samples (P96 + P97) with 3 runs of sequential DDA in positive ionization mode
- `mza/CPTAC4_BENCH-2_CompRef_SuperPool_DDA_01_POS_06Sep23_Brandi_WCSH417231.mza`
- `mza/CPTAC4_BENCH-2_CompRef_SuperPool_DDA_02_POS_06Sep23_Brandi_WCSH417231.mza`
- `mza/CPTAC4_BENCH-2_CompRef_SuperPool_DDA_03_POS_06Sep23_Brandi_WCSH417231.mza`

### DIA

3 IMS DIA runs each of individual P96 and P97 samples in positive ionization mode
- `mza/CPTAC4_BENCH-2_CompRef_P96_Pool_01_L_DIA_POS_07Sep23_Brandi_WCSH417231.mza`
- `mza/CPTAC4_BENCH-2_CompRef_P96_Pool_02_L_DIA_POS_07Sep23_Brandi_WCSH417231.mza`
- `mza/CPTAC4_BENCH-2_CompRef_P96_Pool_03_L_DIA_POS_07Sep23_Brandi_WCSH417231.mza`
- `mza/CPTAC4_BENCH-2_CompRef_P97_Pool_01_L_DIA_POS_07Sep23_Brandi_WCSH417231.mza`
- `mza/CPTAC4_BENCH-2_CompRef_P97_Pool_02_L_DIA_POS_07Sep23_Brandi_WCSH417231.mza`
- `mza/CPTAC4_BENCH-2_CompRef_P97_Pool_03_L_DIA_POS_07Sep23_Brandi_WCSH417231.mza`

## Data Analysis Parameter Configuration Files

We will use pre-prepared configuration files to define the various parameters that control the data extraction, processing, and annotation. For convenience, we can use the CLI utility to dump default config files for each of the three main steps and store them in the `configs/` directory.

### DDA Data Extraction and Processing

```shell
python3 -m lipidimea utility params --default-dda configs/dda_pos.yaml
```

### DIA Data Extraction and Processing

```shell
python3 -m lipidimea utility params --default-dia configs/dda_pos.yaml
```

### Lipid Annotation

```shell
python3 -m lipidimea utility params --default-ann configs/dda_pos.yaml
```

> We can use the default parameter config files as-is for the DDA and DIA data extraction and processing steps, but for annotation we need to change one parameter from its default value: `ionization: null` to `ionization: POS` 

# Run the Analysis

The data analysis script [example.py](example.py) will perform all of the data analysis steps outlined above, ultimately producing a results database (`results/pos.db`) and an exported CSV (`results/pos.csv`). 

```shell
python3 example.py
```
