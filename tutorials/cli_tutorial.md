# Overview

This tutorial covers complete analysis of example data using the command-line interface (CLI) from the `lipidimea` Python package:

- Extract and process DDA features from sequential DDA data files
- Using the extracted DDA features as targets, extract and process DIA features from individual DIA data files
- Perform lipid annotation on DIA features
- Export results (DIA features + lipid annotations) to CSV for downstream analysis

See [CLI documentation](../cli.md) for more information on the commands.


# Setup

See [tutorial setup instructions](setup.md)

## Initialize Results Database

Create the empty results database, which will store intermediate results from DDA and DIA data extraction and processing, in addition to lipid annotations. 

```shell
python3 -m lipidimea utility create_db --overwrite compref/results/pos_cli.db
```

# Process Data

> When examples of the results from the various steps are noted below, these come from analysis using the default parameters with a specific codebase version and on a specific platform (MacOS). As such, the exact feature counts and other details of the results may differ from your own when working through the tutorial.

## DDA

### Process DDA Data

#### Extract DDA Features

We extract the DDA features from each of the sequential DDA runs individually.

> We include the `--no-consolidate` when we process the individual DDA runs because there is no point in consolidating the DDA features until after we have extracted them from all runs first. We instead explicitly consolidate all DDA features after DDA feature extraction is complete for all runs.

#### Run 1

```shell
python3 -m lipidimea dda --no-consolidate compref/configs/dda_pos.yaml compref/results/pos_cli.db compref/mza/SuperPool_DDA_01.mza
```

__Result__: 2681 DDA features added to the database.

#### Run 2

```shell
python3 -m lipidimea dda --no-consolidate compref/configs/dda_pos.yaml compref/results/pos_cli.db compref/mza/SuperPool_DDA_02.mza
```

__Result__: 2293 DDA features added to the database.

#### Run 3

```shell
python3 -m lipidimea dda --no-consolidate compref/configs/dda_pos.yaml compref/results/pos_cli.db compref/mza/SuperPool_DDA_03.mza
```

__Result__: 2936 DDA features added to the database.

#### Consolidate DDA Features 

> Omit `--no-consolidate` flag and do not specify any MZA files to perform consolidation of DDA features only, without extracting any new features.

```shell
python3 -m lipidimea dda compref/configs/dda_pos.yaml compref/results/pos_cli.db
```

__Result__: Consolidated 7910 -> 5320 DDA features

#### Process Data in a Single Step

> For this tutorial we processed each of the sequential DDA data files individually, but it is possible to perform complete DDA feature extraction from all sequential runs and perform consolidation of DDA features in a single step using the command below. This is achieved by omitting the `--no-consolidate` flag and providing all of the MZA files as input.

```shell
python3 -m lipidimea dda compref/configs/dda_pos.yaml compref/results/pos_cli.db compref/mza/SuperPool_DDA_01.mza compref/mza/SuperPool_DDA_02.mza compref/mza/SuperPool_DDA_03.mza
```

## DIA

### Process DIA Data

#### Extract DIA Features

We extract the DIA features from each of the DIA runs in parallel.

> For this example there are 6 input DIA data files and my system has more than 6 CPU cores so I am able to run them all in parallel at once. If the number of DIA data files exceeds the number of available CPU cores, set `--n-proc` to the number of available cores and the DIA files will be queued and processed across those available cores until the entire list is complete.

```shell
python3 -m lipidimea dia process --n-proc 6 compref/configs/dia_pos.yaml compref/results/pos_cli.db compref/mza/P96_DIA_01.mza compref/mza/P96_DIA_02.mza compref/mza/P96_DIA_03.mza compref/mza/P97_DIA_01.mza compref/mza/P97_DIA_02.mza compref/mza/P97_DIA_03.mza
```


#### Apply CCS Calibration to DIA Features

First, we need to fetch the `file_id`s that correspond to the DIA data files, so we can specify that the CCS calibration should be applied to those. This accommodates analysis of larger datasets where different sets of DIA data files may require use of different CCS calibration parameters (_e.g._ batches run on different days).

```shell
python3 -m lipidimea dia list file_ids compref/results/pos_cli.db
```

__Result__: 4 5 6 7 8 9

The CCS calibration parameters we will apply to the DIA features for this data are: 

| t_fix     | beta     |
|-----------|----------|
| -0.038937 | 0.131846 |

We apply the CCS calibration to the extracted DIA features:

```shell
python3 -m lipidimea dia calibrate_ccs compref/results/pos_cli.db -0.038937 0.131846 4 5 6 7 8 9
```

#### Group DIA Features

Group DIA features based on _m/z_, retention time, and drift time

```shell
python3 -m lipidimea utility group_features compref/results/pos_cli.db 0.02 0.2 2.0
```

## Annotate Lipids

### Perform Lipid Annotation

```shell
python3 -m lipidimea annotate compref/configs/ann_pos.yaml ./compref/results/pos_cli.db
```

## Export Results to CSV

> For this example we use the more conservative "intersection" strategy for combining annotations across different DIA data files. This keeps only lipid annotations for each aligned feature that are in common across all included DIA data files. We could instead use the "union" strategy which keeps all lipid annotations for each feature, but this may include more spurious lipid annotations. 

> We specify the file IDs of the DIA data files that we want to include in the exported table. We could export only a subset of the DIA data files if we wanted to by specifying only their file IDs.

```shell
python3 -m lipidimea utility export --annotation-combine-strategy intersection --max-precursor-ppm 20. compref/results/pos_cli.db compref/results/pos_cli.csv 4 5 6 7 8 9
```

The resulting CSV with DIA features aligned across DIA data files and with lipid annotations included can be used for downstream data analysis and interpretation.
