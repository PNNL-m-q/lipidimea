## > `LipidIMEA --help`
```
usage: LipidIMEA [-h] {utility,dda,dia,annotate} ...

Lipidomics Integrated Multi-Experiment Analysis tool

options:
  -h, --help            show this help message and exit

subcommands:
  {utility,dda,dia,annotate}
    utility             utility functions
    dda                 DDA data extraction and processing
    dia                 DIA data extraction and processing
    annotate            perform lipid annotation
```

## > `LipidIMEA utility --help`
```
usage: LipidIMEA utility [-h] {params,create_db,export} ...

General utilities

options:
  -h, --help            show this help message and exit

utility subcommand:
  {params,create_db,export}
    params              manage parameters
    create_db           create results database
    export              export results to CSV
```

### > `LipidIMEA utility params --help`
```
usage: LipidIMEA utility params [-h] [--default-dda CONFIG] [--default-dia CONFIG] [--default-ann CONFIG]

Load default parameter configs

options:
  -h, --help            show this help message and exit
  --default-dda CONFIG  load the default DDA parameters config (YAML), write to specified path
  --default-dia CONFIG  load the default DIA parameters config (YAML), write to specified path
  --default-ann CONFIG  load the default lipid annotation parameters config (YAML), write to specified path
```

### > `LipidIMEA utility create_db --help`
```
usage: LipidIMEA utility create_db [-h] [--overwrite] RESULTS_DB

Initialize the results database

positional arguments:
  RESULTS_DB   results database file (.db)

options:
  -h, --help   show this help message and exit
  --overwrite  overwrite the results database file if it already exists
```

### > `LipidIMEA utility export --help`
```
usage: LipidIMEA utility export [-h] [--mz-tol MZ_TOL] [--rt-tol RT_TOL] [--at-tol AT_TOL] [--abundance {height,area}] [--annotation-combine-strategy {intersection,union}] [--max-precursor-ppm MAX_PRECURSOR_PPM] [--include-unknowns]
                                RESULTS_DB OUT_CSV DFILE_ID [DFILE_ID ...]

Export analysis results to CSV

positional arguments:
  RESULTS_DB            results database file (.db)
  OUT_CSV               export to file name (.csv)
  DFILE_ID              DIA data file IDs to include in exported results

options:
  -h, --help            show this help message and exit
  --mz-tol MZ_TOL       m/z tolerance for grouping features (default=0.025)
  --rt-tol RT_TOL       retention time tolerance for grouping features (default=0.25)
  --at-tol AT_TOL       arrival time tolerance for grouping features (default=2.5)
  --abundance {height,area}
                        use arrival time peak height or area for feature abundance (default='area')
  --annotation-combine-strategy {intersection,union}
                        strategy for combining annotations among grouped features (default='union')
  --max-precursor-ppm MAX_PRECURSOR_PPM
                        max ppm error for annotated precursor m/z (default=40.)
  --include-unknowns    set this to export DIA features that do not have any lipid annotations
```

## > `LipidIMEA dda --help`
```
usage: LipidIMEA dda [-h] [--n-proc N_PROC] [--no-consolidate] PARAMS_CONFIG RESULTS_DB [DDA_MZA ...]

DDA data extraction and processing

positional arguments:
  PARAMS_CONFIG     parameter config file (.yaml)
  RESULTS_DB        results database file (.db)
  DDA_MZA           DDA data files to process (.mza)

options:
  -h, --help        show this help message and exit
  --n-proc N_PROC   set >1 to processes multiple data files in parallel (default=1)
  --no-consolidate  do not consolidate DDA features after extraction
```

## > `LipidIMEA dia --help`
```
usage: LipidIMEA dia [-h] {process,list,calibrate_ccs} ...

DIA data extraction and processing and related functions

options:
  -h, --help            show this help message and exit

dia subcommand:
  {process,list,calibrate_ccs}
    process             extract and process DIA data
    list                get information about DIA data
    calibrate_ccs       add calibrated CCS to DIA precursors
```

### > `LipidIMEA dia process --help`
```
usage: LipidIMEA dia process [-h] [--n-proc N_PROC] PARAMS_CONFIG RESULTS_DB [DIA_MZA ...]

Extract and process DIA data

positional arguments:
  PARAMS_CONFIG    parameter config file (.yaml)
  RESULTS_DB       results database file (.db)
  DIA_MZA          DIA data files to process (.mza)

options:
  -h, --help       show this help message and exit
  --n-proc N_PROC  set >1 to processes multiple data files in parallel (default=1)
```

### > `LipidIMEA dia list --help`
```
usage: LipidIMEA dia list [-h] {file_ids} RESULTS_DB

Fetch information about processed DIA data

positional arguments:
  {file_ids}  which information to fetch
  RESULTS_DB  results database file (.db)

options:
  -h, --help  show this help message and exit
```

### > `LipidIMEA dia calibrate_ccs --help`
```
usage: LipidIMEA dia calibrate_ccs [-h] RESULTS_DB T_FIX BETA DFILE_ID [DFILE_ID ...]

Add calibrated CCS to DIA precursors

positional arguments:
  RESULTS_DB  results database file (.db)
  T_FIX       t_fix CCS calibration parameter
  BETA        beta CCS calibration parameter
  DFILE_ID    DIA data file IDs to apply CCS calibration to

options:
  -h, --help  show this help message and exit
```

## > `LipidIMEA annotate --help`
```
usage: LipidIMEA annotate [-h] PARAMS_CONFIG RESULTS_DB

Add lipid annotations to DIA features

positional arguments:
  PARAMS_CONFIG  parameter config file (.yaml)
  RESULTS_DB     results database file (.db)

options:
  -h, --help     show this help message and exit
```
