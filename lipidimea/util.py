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

import polars as pl

from lipidimea.typing import (
    ResultsDbPath, ResultsDbCursor, MzaFilePath, MzaFileId
)


INCLUDE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_include")


#------------------------------------------------------------------------------
# results database


# define path to results DB schema file
_RESULTS_DB_SCHEMA = os.path.join(INCLUDE_DIR, 'results.sql3')


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
                        data_file_path: MzaFilePath
                        ) -> MzaFileId :
    """
    add a data file to the results database (DataFiles table) and return the corresponding
    data file identifier (`int`)
    """
    qry = """--beginsql
        INSERT INTO DataFiles VALUES (?,?,?,?,?)
    --endsql"""
    cur.execute(qry, (None, data_file_type, data_file_path, None, None))
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
# results export

def _map_dfile_names_to_ids(data_file_names: List[str],
                            cur: ResultsDbCursor
                            ) -> List[int] :
    """ take a list of data file names and return a list of their corresponding IDs """
    mapping = {
        dfile_name: dfile_id
        for (dfile_name, dfile_id) in cur.execute(
            "SELECT dfile_name, dfile_id FROM DataFiles WHERE dfile_type='LC-IMS-MS/MS (DIA)'"
        )
    }
    return [mapping[name] for name in data_file_names]


def _get_included_dfile_ids(select_data_files: Optional[Union[List[str], List[int]]],
                            cur: ResultsDbCursor,
                            ) -> List[int] :
    """ 
    There are different ways the selected data files may be specified (or not specified),
    so whatever the case is convert to a list of data file IDs 
    """
    include_dfile_ids: List[int]
    if select_data_files is not None:
        # list cannot be empty, gotta check the type of the first element to decide what to do
        assert len(select_data_files) > 0
        if type(select_data_files[0]) is str:
            # map the datafile names to data file IDs
            include_dfile_ids = _map_dfile_names_to_ids(select_data_files, cur)  # type: ignore
        else:
            # otherwise it had better be a list of ints
            assert type(select_data_files[0]) is int
            include_dfile_ids = select_data_files  # type: ignore
    else:
        # default to all data files
        include_dfile_ids = [
            dfid for (dfid,) in cur.execute("SELECT DISTINCT dfile_id FROM DIAPrecursors").fetchall()
        ]
    return include_dfile_ids


def _fetch_dia_precursors(cur: ResultsDbCursor,
                          include_unknowns: bool,
                          include_dfile_ids: List[int],
                          limit_precursor_mz_ppm: float,
                          ) -> Generator[Any, Any, Any] : 
    """ 
    construct a query and fetch the DIA precursors from the database, 
    yields results one row at a time 
    """
    # collect/aggregate the DIA precursors
    qry_sel_precursors = """--beginsql
    SELECT 
        dia_pre_id, 
        dfile_id,
        mz, 
        rt, 
        dt, 
        ccs, 
        dt_pkht, 
        dt_pkht * dt_fwhm * 1.064467 AS dt_area,
        GROUP_CONCAT(lipid || "@" || adduct, "|") AS annotations
    FROM
        DIAPrecursors
        {incl_unk} JOIN Lipids USING(dia_pre_id)
    WHERE
        dfile_id IN ({dfids})
        AND ABS(mz_ppm_err) <= {ppmlim}
    GROUP BY
        dia_pre_id
    ORDER BY
        annotations
    --endsql""".format(
        incl_unk="LEFT" if include_unknowns else "",
        dfids=",".join(map(str, include_dfile_ids)),
        ppmlim=limit_precursor_mz_ppm
    )
    for row in cur.execute(qry_sel_precursors):
        yield row


def _precursor_match(one: Union[Tuple[float, float, float], List[float]], 
                     another: Union[Tuple[float, float, float], List[float]],
                     tols: Union[Tuple[float, float, float], List[float]]
                     ) -> bool :
    """ returns bool indicating if one precursor matches another (within specified tolerances) """
    # unpack
    one_mz, one_rt, one_dt = one
    another_mz, another_rt, another_dt = another
    tol_mz, tol_rt, tol_dt = tols
    return (
        abs(one_mz - another_mz) <= tol_mz
        and abs(one_rt - another_rt) <= tol_rt
        and abs(one_dt - another_dt) <= tol_dt
    )


# TODO: This is a pretty well-defined data structure, maybe it would be
#       worth it to just implement an internal dataclass or something like
#       that? It would make it unecessary to have this type alias and could
#       also support some hinting and stuff from the text editor. Plus the 
#       actual specifications for the data structure would be more apparent
#       and better documented.

# placeholder type alias for grouped results, the intermediate data structure 
# from exporting a results table that has the layout:
#       grouped = [
#             {
#                 "dia_pre_ids": list(int)
#                 "mz_rt_dt": (
#                     678.9012,
#                     12.34,
#                     34.56
#                 ),
#                 "ccs": 234.5 or None,
#                 "annotations": set(str),
#                 "abundance": {
#                     dfile_id: peak area or peak height,
#                     ...
#                 }
#             }, 
#             ...
#       ]
type _GroupedResults = Any


def _extract_intermediate_data(cur: ResultsDbCursor,
                               include_dfile_ids: List[int],
                               tolerances: Tuple[float, float, float],
                               abundance_value: Literal["dt_area", "dt_height"],
                               include_unknowns: bool,
                               limit_precursor_mz_ppm: float,
                               annotation_combine_strategy: Literal["union", "intersection"]
                               ) -> _GroupedResults :
    """
    Performs all the steps for extracting and aggregating data from the results database 
    using the supplied selections and filters and returns an intermediate data structure 
    (type alias _GroupedResults) from which the data may be assembled into actual tabular 
    format and exported. It is useful to have this part of the process in a separate 
    function so that various selection and filtering parameters can be tested out and 
    this intermediate data structure can be inspected instead of the results always being 
    written all the way into a .csv file.
    """
    # group the precursors based on m/z, RT, and DT
    grouped = [
        # {
        #     "dia_pre_ids": list(int)
        #     "mz_rt_dt": (
        #         678.9012,
        #         12.34,
        #         34.56
        #     ),
        #     "ccs": 234.5 or None,
        #     "annotations": set(str),
        #     "abundance": {
        #         dfile_id: peak area or peak height,
        #         ...
        #     }
        # }, 
        # ...
    ]
    # iterate through the DIA precursors and group them
    for dia_pre_id, dfile_id, *mz_rt_dt, ccs, dt_pkht, dt_area, annotations in _fetch_dia_precursors(
        cur, include_unknowns, include_dfile_ids, limit_precursor_mz_ppm
    ):
        # flag indicating if this entry was matched with an entry in the grouped list
        matched = False
        abundance = {"dt_area": dt_area, "dt_height": dt_pkht}[abundance_value]
        anns = set(annotations.split("|"))
        # NOTE: This is a slow way to do this O(N^2), but probably OK for now
        for group in grouped:
            if _precursor_match(group["mz_rt_dt"], mz_rt_dt, tolerances):
                matched = True
                group["dia_pre_ids"].append(dia_pre_id)
                # take the intersection or union of all possible annotations
                match annotation_combine_strategy:
                    case "intersection":
                        group["annotations"] &= anns
                    case "union":
                        group["annotations"] |= anns
                if dfile_id in group["abundance"]:
                    group["abundance"][dfile_id] += abundance
                else:
                    group["abundance"][dfile_id] = abundance
                break
        if not matched:
            grouped.append({
                "dia_pre_ids": [dia_pre_id],
                "mz_rt_dt": mz_rt_dt,
                "ccs": ccs,
                "annotations": anns,
                "abundance": {dfile_id: abundance}
            })
    return grouped


def _setup_alias_mapping(cur: ResultsDbCursor,
                         data_file_aliases: Optional[Dict[Union[int, str], str]],
                         ) -> Dict[int, str] :
    """ set up the mapping between data file aliases and data file names/IDs """
    out_aliases: Dict[int, str]
    # convert whatever was provided into mapping between alias and data file ID
    # (it can be None which means use file names, or dict(str: str) which needs to be converted)
    if data_file_aliases is None: 
        out_aliases = {
            dfile_id: dfile_name
            for (dfile_name, dfile_id) in cur.execute("SELECT dfile_name, dfile_id FROM DataFiles")
        }
    elif type(list(data_file_aliases.keys())[0]) is str:  # type: ignore
        # map the file names to IDs, then IDs to aliases
        name_to_id = {
            dfile_name: dfile_id
            for (dfile_name, dfile_id) in cur.execute("SELECT dfile_name, dfile_id FROM DataFiles")
        }
        out_aliases = {
            name_to_id[dfile_name]: alias
            for dfile_name, alias in data_file_aliases.items()
        }
    else:
        # already correct mapping
        out_aliases = data_file_aliases  # type: ignore
    return out_aliases
    

def _unpack_intermediate_results(grouped: _GroupedResults,
                                 alias_mapping: Dict[int, str],
                                 include_unknowns: bool,
                                 include_dfile_ids: List[int],
                                 ) -> pl.DataFrame :
    """
    unpack all of the info from the intermediate grouped results data structure into
    tabular format and return it in a polars dataframe
    """
    # data dictionary
    # column name: column data
    data = {
        "precursor IDs": [], 
        "m/z": [], 
        "RT (min)": [], 
        "arrival time (ms)": [], 
        "CCS (Ang^2)": [], 
        "Lipid@Adduct": [] 
    } | {
        alias: []
        for dfid, alias in alias_mapping.items() 
        if dfid in include_dfile_ids
    }
    # fill the data dictionary
    for entry in grouped:
        if include_unknowns or len(entry["annotations"]) > 0:
            data["precursor IDs"].append("|".join(map(str, entry["dia_pre_ids"])))
            emz, ert, edt = entry["mz_rt_dt"]
            data["m/z"].append(emz)
            data["RT (min)"].append(ert)
            data["arrival time (ms)"].append(edt)
            data["CCS (Ang^2)"].append(entry["ccs"])
            data["Lipid@Adduct"].append("|".join(entry["annotations"]))
            for dfid, abun in entry["abundance"].items():
                if dfid in include_dfile_ids:
                    # fetch abundances, cast to ints 
                    data[alias_mapping[dfid]].append(int(abun))
            for dfid, alias in alias_mapping.items():
                if dfid in include_dfile_ids:
                    if dfid not in entry["abundance"].keys():
                        data[alias].append(None)
    return pl.DataFrame(data).sort("Lipid@Adduct", "RT (min)", "arrival time (ms)")


def export_results_table(results_db: ResultsDbPath,
                         out_csv: str,
                         tolerances: Tuple[float, float, float],
                         select_data_files: Optional[Union[List[int], List[str]]] = None,
                         abundance_value: Literal["dt_area", "dt_height"] = "dt_area",
                         include_unknowns: bool = False,
                         limit_precursor_mz_ppm: float = 40.,
                         data_file_aliases: Optional[Dict[Union[int, str], str]] = None,
                         annotation_combine_strategy: Literal["union", "intersection"] = "union"
                         ) -> int :
    """
    Aggregate the results (DIA) from the database and output in a tabular format (.csv).

    Aligns features across samples (data files) based on m/z, RT, and arrival time using specified
    tolerances. If more than one feature from a single data file falls within the specified tolerances,
    the features are combined (summed). Annotations for the features from the different DIA data files
    are aggregated by taking the intersection. The feature intensities will be output in separate columns
    for each data file. The column names will be the data file names by default, but this can be
    overridden using the optional data_file_aliases parameter, which maps either data file name (str) or
    data file ID (int) to an alias (str). The intensities will be the arrival time peak areas by default,
    but this can be changed to arrival time peak heights by setting abundance_value="dt_height".

    Parameters
    ----------
    results_db
        results database with annotated DIA features
    out_csv
        output results file (.csv)
    tolerances
        tuple of tolerances (m/z, RT, arrival time) for combining DIA precursors
    [select_data_files]
        If provided, restrict the results to only include the specified list of data files, by data 
        file name if list of str or by data file ID if list of int
    [abundance_value]
        "dt_area" = use arrival time peak area for abundance values (default) or "dt_height" = use 
        arrival time peak heights instead
    [include_unknowns]
        flag indicating whether to include DIA features that do not have any associated annotations
    [limit_precursor_mz_ppm]
        limit the absolute m/z ppm error when selecting lipid annotations 
    [data_file_aliases]
        If provided, map data file ids or names to specified aliases. The mapping may be defined as data
        file name (str) to alias (str) or data file ID (int) to alias (str). 
    [annotation_combine_strategy]
        for cases where there are multiple potential annotations within a group of features, determines 
        the strategy for what annotations to keep. "union" to keep all possible annotations and
        "intersection" to only keep annotations that are common among all features that get combined into
        a group. The latter is much more stringent. 
    
    Returns
    -------
    n_rows
        the number of rows in the exported table
    """
    # ensure results database file exists
    if not os.path.isfile(results_db):
        raise FileNotFoundError(errno.ENOENT,
                                os.strerror(errno.ENOENT),
                                results_db)
    # connect to results database
    con = sqlite3.connect(results_db)
    cur = con.cursor()
    # determine the set of data files to include
    include_dfile_ids = _get_included_dfile_ids(select_data_files, cur)
    # perform the first half of the process to get the _GroupedResults
    # intermediate data structure
    grouped = _extract_intermediate_data(cur,
                                         include_dfile_ids,
                                         tolerances, 
                                         abundance_value, 
                                         include_unknowns, 
                                         limit_precursor_mz_ppm,
                                         annotation_combine_strategy)
    # set up the mapping between data file aliases and data file names/IDs
    alias_mapping = _setup_alias_mapping(cur, data_file_aliases)
    # upack the intermediate data structure into tabular format (as a polars dataframe)
    df = _unpack_intermediate_results(grouped, 
                                      alias_mapping, 
                                      include_unknowns,
                                      include_dfile_ids)  
    # TODO: (filter dataframe? replace NAs?)
    df.write_csv(out_csv)
    return df.shape[0]

