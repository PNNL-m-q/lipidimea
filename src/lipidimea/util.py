"""
lipidimea/util.py
Dylan Ross (dylan.ross@pnnl.gov)

    module with general utilities
"""


import os
import errno
from typing import (
    Optional, Callable, Dict, Union, Tuple, List, Generator, Any, Literal
)
import sqlite3
import enum
import json
import contextlib

import polars as pl
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist
import numpy as np
from numpy import typing as npt

from lipidimea.typing import (
    ResultsDbPath, ResultsDbCursor, MzaFilePath, MzaFileId
)


INCLUDE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_include")


#------------------------------------------------------------------------------
# results database


# define path to results DB schema file
_RESULTS_DB_SCHEMA = os.path.join(INCLUDE_DIR, 'results.sql')


def create_results_db(results_file: ResultsDbPath,
                      overwrite: bool = False,
                      strict: bool = True
                      ) -> None :
    """
    creates a sqlite database for results from DDA/DDA data analysis

    raises a RuntimeError if the database already exists

    Parameters
    ----------
    results_file
        filename/path of the database
    [overwrite]
        if the database file already exists and this flag is True, then overwrite existing database
        and do not raise the RuntimeError
    [strict]
        use STRICT constraint on all data tables in results database, set this to False to exclude
        this constraint and enable backward compatibility with older versions of Python/sqlite3
        since 3.12 is the first Python version to support the STRICT mode
    """
    # see if the file exists
    if os.path.exists(results_file):
        if overwrite:
            os.remove(results_file)
        else:
            msg = f"create_results_db: results database file ({results_file}) already exists"
            raise RuntimeError(msg)
    # initial connection creates the DB
    con = sqlite3.connect(results_file)
    cur = con.cursor()
    # execute SQL script to set up the database
    with open(_RESULTS_DB_SCHEMA, 'r') as sql_f:
        content = sql_f.read()
        # patch schema in-place to remove STRICT constraints if strict flag set to False
        if not strict:
            content = content.replace("STRICT", "")
        cur.executescript(content)
    # save and close the database
    con.commit()
    con.close()


def add_data_file_to_db(cur: ResultsDbCursor,
                        data_file_type: str,
                        data_file_path: MzaFilePath, 
                        data_file_id: Optional[int] = None
                        ) -> MzaFileId :
    """
    add a data file to the results database (DataFiles table) and return the corresponding
    data file identifier (`int`)
    """
    qry = """--beginsql
        INSERT INTO DataFiles VALUES (?,?,?,?,?)
    --endsql"""
    cur.execute(qry, (data_file_id, data_file_type, data_file_path, None, None))
    rowid = cur.lastrowid
    # lastrowid can be None, but that should not happen because we run an insert
    # query first. lastrowid should only be None if something goes wrong with the
    # insert, so go ahead and get mad if that is the case
    assert type(rowid) is int
    return rowid


class AnalysisStep(enum.Enum):
    DDA_EXT = "DDA feature extraction"
    DDA_CONS = "DDA feature consolidation"
    DIA_EXT = "DIA feature extraction"
    DIA_FEAT_GRP = "DIA feature grouping"
    CCS_CAL = "CCS calibration"
    LIPID_ANN = "lipid annotation"


def check_analysis_log(cur: ResultsDbCursor,
                       step: AnalysisStep
                       ) -> None :
    """
    Raise a RuntimeError if the specified step has not been completed
    """
    qry = """--beginsql
        SELECT step FROM AnalysisLog;
    --endsql"""
    if (step.value,) not in cur.execute(qry).fetchall():
        cur.connection.close()
        raise RuntimeError(f"analysis step {step.value} not found in results database")
    

def update_analysis_log(cur: ResultsDbCursor,
                        step: AnalysisStep, 
                        notes: Optional[Dict[str, Union[str, int, float]]] = None
                        ) -> None :
    """
    update analysis log in results database, include optional notes as dict with key:value pairs 
    (gets converted to JSON)
    """
    qry = """--beginsql
        INSERT INTO AnalysisLog VALUES (?,?,?);
    --endsql"""
    qdata = (
        None,  # n gets autoincremented, keeps track of step completion order
        step.value,
        json.dumps(notes, indent=2) if notes is not None else None
    )
    _ = cur.execute(qry, qdata)


#------------------------------------------------------------------------------
# debug handler


def debug_handler(debug_flag: Optional[str], debug_cb: Optional[Callable], msg: str,
                  pid: Optional[int] = None
                  ) -> None :
    """
    deal with different debugging states automatically

    debug_flag:

    - ``None``: do nothing
    - ``'text'``: prints text debugging messages only
    - ``'text_pid'``: prints text debugging messages, with PID prepended on the DEBUG label
    - ``'textcb'``: produces text debugging messages but instead of printing it calls the
      debug_cb callback with the message as an argument
    - ``'textcb_pid'``: produces text debugging messages but instead of printing it calls
      the debug_cb callback with the message as an argument, with PID prepended on the DEBUG label

    Parameters
    ----------
    debug_flag
        specifies how to dispatch the message, `None` to do nothing
    debug_cb
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'
    msg
        debugging message (automatically prepended with "DEBUG: ")
    [pid]
        PID for individual process, may be omitted if debug flag does not have "_pid" in it
    """
    if debug_flag is not None:
        pid_flag = 'pid' in debug_flag
        lbl = f"<pid: {pid}> " if pid_flag else ""
        msg = lbl + "DEBUG: " + msg
        if debug_flag in ["text", "text_pid"]:
            print(msg, flush=True)
        if debug_flag in ["textcb", "textcb_pid"]:
            if debug_cb is not None:
                debug_cb(msg)
            else:
                ve = '_debug_handler: debug_flag was set to "textcb" or "textcb_pid" but no debug_cb was provided'
                raise ValueError(ve)


#------------------------------------------------------------------------------
# group DIA precursors


def _clear_existing_feature_groups(
        cur: ResultsDbCursor
):
    """
    remove all entries from DIAFeatureGroups and DIAPrecursorToGroup tables
    """
    cur.execute("DELETE FROM DIAFeatureGroups;")
    cur.execute("DELETE FROM DIAPrecursorToGroup;")


def _fetch_dia_precursor_arrays(
        cur: ResultsDbCursor
) -> Tuple[npt.NDArray[np.intp], npt.NDArray[np.floating]] :
    """
    fetch DIA precursor IDs, m/z, rt, dt and convert to numpy arrays
    """
    qry = """--beginsql
        SELECT
            dia_pre_id,
            mz, 
            rt,
            dt
        FROM
            DIAPrecursors
    --endsql"""
    # query and unpack results into arrays, one per column
    pre_ids, mzs, rts, dts = np.array(cur.execute(qry).fetchall()).T
    # precursor IDs should be ints
    pre_ids = pre_ids.astype(int)
    # combine the m/zs rts and dts into one array with shape: (n_features, 3)
    mz_rt_dt = np.array([mzs, rts, dts]).T
    # return the formatted array data
    return pre_ids, mz_rt_dt
    

def _precursor_group_average_properties(
        cur: ResultsDbCursor,
        pre_ids: List[int]
) -> Tuple[int, float, float, float, Optional[float]] : 
    """
    fetch the count of unique data file IDs in the group as well as
    mz, rt, dt, and ccs data for grouped features 
    """
    qry = """--beginsql
        SELECT 
            dfile_id,
            mz, 
            rt, 
            dt, 
            ccs
        FROM
            DIAPrecursors
        WHERE 
            dia_pre_id IN ({})
    --endsql""".format(",".join(map(str, pre_ids)))
    # fetch and unpack the properties
    dfids, mzs, rts, dts, ccss = (
        pl.read_database(qry, cur)
        .to_numpy()
        .T
    )
    return (
        len(set(dfids)),
        mzs.mean(),
        rts.mean(),
        dts.mean(),
        ccs if not np.isnan(ccs := ccss.mean()) else None
    )


def group_dia_precursors(
        results_db: ResultsDbPath,
        mz_tol: float,
        rt_tol: float,
        dt_tol: float,
):
    """
    Group DIA precursors into features across all samples (file IDs) based on 
    similar m/z, RT, and DT. Stored grouped feature info in the results database
    in the DIAFeatureGroups and DIAPrecursorToGroup tables.

    Parameters
    ----------
    results_db
        results database with annotated DIA features
    mz_tol, rt_tol, dt_tol
        tolerances (m/z, RT, arrival time) for combining DIA precursors
    """
    # ensure results database file exists
    if not os.path.isfile(results_db):
        raise FileNotFoundError(errno.ENOENT,
                                os.strerror(errno.ENOENT),
                                results_db)
    # connect to results database
    con = sqlite3.connect(results_db)
    cur = con.cursor()
    # clear out any existing groupings
    _clear_existing_feature_groups(cur)
    # extract the DIA precursor IDs, m/z, rt, dts and convert to numpy arrays
    all_pre_ids, mz_rt_dt = _fetch_dia_precursor_arrays(cur)
    # scale m/z, rt, and dt using tolerances to make the multidimensional linkage work
    mz_rt_dt /= np.array([mz_tol, rt_tol, dt_tol])
    # compute linkage
    Z = linkage(pdist(mz_rt_dt, metric="chebyshev"), method="complete")
    # create the clusters
    labels = fcluster(Z, t=1.0, criterion="distance")
    # iterate through labels, fetch all group members, compute average m/z 
    # rt, dt values, create the grouped feauture (ID is cluster ID), add the mapping
    # for all of the individual features to the newly created grouped feauture.
    for label, pre_ids in (
        pl.DataFrame({"label": labels, "pre_ids": all_pre_ids})
        .group_by("label")
        .agg("pre_ids")
        .iter_rows()
    ):
        # fetch the average properties for the group
        n, avg_mz, avg_rt, avg_dt, avg_ccs = _precursor_group_average_properties(cur, pre_ids)
        # add an entry to DIAFeatureGroups
        cur.execute(
            "INSERT INTO DIAFeatureGroups VALUES (?,?,?,?,?,?);", 
            (label, avg_mz, avg_rt, avg_dt, avg_ccs, n)
        )
        # add mapping from individual precursors to this group
        # TODO: In the cases where there are somehow multiple DIA features from the same
        #       data file that have really close m/z, rt, and dt and that are members of
        #       the same group, only include the feature with the highest dt peak height
        #       in the mapping.
        for pre_id in pre_ids:
            cur.execute(
                "INSERT INTO DIAPrecursorToGroup VALUES (?,?);", 
                (label, pre_id)
            )
    # update the analysis log
    update_analysis_log(
        cur, 
        AnalysisStep.DIA_FEAT_GRP,
        {
            "mz_tol": mz_tol,
            "rt_tol": rt_tol,
            "dt_tol": dt_tol
        }
    )
    # clean up
    con.commit()
    con.close()


#------------------------------------------------------------------------------
# results export


# TODO: Feature grouping logic is now a separate function. Do not repeat it here, 
#       the export logic should just take those existing feature groups, apply any
#       necessary filtering and reformatting, then dump to file.




def export_results_table(results_db: ResultsDbPath,
                         out_csv: str,
                         select_data_file_ids: List[int],
                         abundance_value: Literal["dt_area", "dt_height"] = "dt_area",
                         include_unknowns: bool = False,
                         limit_precursor_mz_ppm: float = 40.,
                         ) -> int :
    """
    Aggregate the results (DIA) from the database and output in a tabular format (.csv).

    The intensities will be the arrival time peak areas by default,
    but this can be changed to arrival time peak heights by setting abundance_value="dt_height".

    Parameters
    ----------
    results_db
        results database with annotated DIA features
    out_csv
        output results file (.csv)
    select_data_file_ids
        estrict the results to only include the specified list of data file IDs
    [abundance_value]
        "dt_area" = use arrival time peak area for abundance values (default) or "dt_height" = use 
        arrival time peak heights instead
    [include_unknowns]
        flag indicating whether to include DIA features that do not have any associated annotations
    [limit_precursor_mz_ppm]
        limit the absolute m/z ppm error when selecting lipid annotations 
    
    Returns
    -------
    n_rows
        the number of rows in the exported table
    """
    qry = """--beginsql
        SELECT 
            dia_fgroup_id, 
            DIAFeatureGroups.mz, DIAFeatureGroups.rt, DIAFeatureGroups.dt, DIAFeatureGroups.ccs, 
            lipid, adduct, mz_ppm_err, 
            {} AS abundance, 
            dfile_name 
        FROM 
            DIAFeatureGroups 
            {} JOIN Lipids USING(dia_fgroup_id) 
            LEFT JOIN DIAPrecursorToGroup USING(dia_fgroup_id) 
            JOIN DIAPrecursors USING(dia_pre_id) 
            JOIN DataFiles USING(dfile_id)
        WHERE 
            dfile_id IN ({})
    --endsql""".format(
        {
            "dt_height": "dt_pkht",
            "dt_area": "(dt_pkht * dt_fwhm * 1.064467)"
        }[abundance_value],
        "LEFT" if include_unknowns else "",
        ",".join(map(str, select_data_file_ids))
    )
    # ensure results database file exists
    if not os.path.isfile(results_db):
        raise FileNotFoundError(errno.ENOENT,
                                os.strerror(errno.ENOENT),
                                results_db)
    # connect to results database, fetch the data
    with contextlib.closing(sqlite3.connect(results_db)) as con: 
        rdf = pl.read_database(
            qry,
            con
        )
    # assemble into a table
    to_export = (
        rdf
        .sort("dfile_name")
        .pivot(
            on="dfile_name",
            index=[
                "dia_fgroup_id", "mz", "rt", "dt", "ccs", "lipid", 
                "adduct", "mz_ppm_err"
            ],
            values="abundance",
            aggregate_function="mean"
        )
        .filter(pl.col("mz_ppm_err") <= limit_precursor_mz_ppm)
        # this group by performs merging of features with the same feature ID
        .group_by("dia_fgroup_id")
        .agg(
            (   
                pl.concat_str(
                    "lipid", "adduct",
                    separator="@"
                )
                .unique()
                .alias("lipid")
            ),
            pl.col("mz").mean(),
            pl.col("rt").mean(),
            pl.col("dt").mean(),
            pl.col("ccs").mean(),
            pl.col("mz_ppm_err").mean(),
            pl.exclude(["dia_fgroup_id", "mz", "rt", "dt", "ccs", "lipid", "mz_ppm_err"]).mean()
        )
        .select(
            "dia_fgroup_id", pl.col("lipid").list.join("|"), "mz", "rt", "dt", "ccs", "mz_ppm_err",
            pl.exclude(["dia_fgroup_id", "mz", "rt", "dt", "ccs", "lipid", "mz_ppm_err"])
        )
        .sort("lipid", "rt")
    )
    to_export.write_csv(out_csv)
    return to_export.shape[0]
