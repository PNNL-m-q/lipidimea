import os

from lipidimea.params import DdaParams, DiaParams, AnnotationParams
from lipidimea.util import create_results_db
from lipidimea.msms.dda import extract_dda_features, consolidate_dda_features
from lipidimea.msms.dia import extract_dia_features_multiproc, add_calibrated_ccs_to_dia_features
from lipidimea.annotation import annotate_lipids
from lipidimea.util import export_results_table


# define paths to the raw data files
_MZA_DIR = "mza/"
_DDA_MZAS = list(map(lambda mzaf: os.path.join(_MZA_DIR, mzaf), [
    "CPTAC4_BENCH-2_CompRef_SuperPool_DDA_01_POS_06Sep23_Brandi_WCSH417231.mza",
    "CPTAC4_BENCH-2_CompRef_SuperPool_DDA_02_POS_06Sep23_Brandi_WCSH417231.mza", 
    "CPTAC4_BENCH-2_CompRef_SuperPool_DDA_03_POS_06Sep23_Brandi_WCSH417231.mza",
]))
_DIA_MZAS = list(map(lambda mzaf: os.path.join(_MZA_DIR, mzaf), [
    "CPTAC4_BENCH-2_CompRef_P96_Pool_01_L_DIA_POS_07Sep23_Brandi_WCSH417231.mza",
    "CPTAC4_BENCH-2_CompRef_P96_Pool_02_L_DIA_POS_07Sep23_Brandi_WCSH417231.mza",
    "CPTAC4_BENCH-2_CompRef_P96_Pool_03_L_DIA_POS_07Sep23_Brandi_WCSH417231.mza",
    "CPTAC4_BENCH-2_CompRef_P97_Pool_01_L_DIA_POS_07Sep23_Brandi_WCSH417231.mza",
    "CPTAC4_BENCH-2_CompRef_P97_Pool_02_L_DIA_POS_07Sep23_Brandi_WCSH417231.mza",
    "CPTAC4_BENCH-2_CompRef_P97_Pool_03_L_DIA_POS_07Sep23_Brandi_WCSH417231.mza",
]))


def _main():

    # load parameters from config files
    dda_params = DdaParams.from_config("configs/dda_pos.yaml")
    dia_params = DiaParams.from_config("configs/dia_pos.yaml")
    ann_params = AnnotationParams.from_config("configs/ann_pos.yaml")

    # create the results database
    results_dbf = "results/pos2.db"
    create_results_db(results_dbf)

    # DDA feature extraction and processing
    for dda_mza in _DDA_MZAS:
        out = extract_dda_features(
            dda_mza, 
            results_dbf, 
            dda_params, 
            debug_flag="text"
        )
        print(out)

    # consolidate DDA features
    out = consolidate_dda_features(results_dbf, dda_params, debug_flag="text")
    print(out)

    # DIA feature extraction and processing
    out = extract_dia_features_multiproc(
        _DIA_MZAS,
        results_dbf, 
        dia_params,
        6,
        debug_flag="text_pid"
    )
    print(out)

    # Add calibrated CCS to DIA features
    for dfile_id in range(4, 10):
        # dfile_ids are 4-9 for DIA data
        add_calibrated_ccs_to_dia_features(results_dbf, dfile_id, -0.038937, 0.131846)

    # Add lipid annotations to DIA features
    out = annotate_lipids(results_dbf, ann_params, debug_flag="text")
    print(out)

    # Export results to CSV
    out = export_results_table(
        results_dbf, 
        "results/pos2.csv", 
        (0.025, 0.25, 2.5), 
        list(range(4, 10)), 
        annotation_combine_strategy="intersection"
    )
    print(out)


if __name__ == "__main__":
    _main()

