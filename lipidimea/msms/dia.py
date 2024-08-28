"""
lipidimea/msms/dia.py

Dylan Ross (dylan.ross@pnnl.gov)

    module with DIA MSMS utilities
    
"""


from typing import List, Tuple, Union, Optional, Any, Callable, Dict
import sqlite3
import os
import errno
from itertools import repeat
import multiprocessing
import time

import numpy as np
import numpy.typing as npt
from scipy import spatial
from mzapy import MZA
from mzapy.peaks import find_peaks_1d_gauss, find_peaks_1d_localmax, calc_gauss_psnr

from lipidimea.msms._util import apply_args_and_kwargs
from lipidimea.util import debug_handler, add_data_file_to_db
from lipidimea.msms._util import tol_from_ppm
from lipidimea.params import (
    DiaDeconvoluteMs2PeaksParams, DiaParams
)
from lipidimea.typing import (
    Xic, Atd, Ms1, Ms2, Spec, SpecStr,
    DiaDeconFragment,
    ResultsDbPath, ResultsDbCursor, ResultsDbConnection,
    MzaFilePath, MzaFileId
)


def _select_xic_peak(target_rt: float, 
                     target_rt_tol: float, 
                     pkrts: List[float], 
                     pkhts: List[float], 
                     pkwts: List[float]
                     ) -> Tuple[float, float, float] :
    """ 
    select the peak with the highest intensity that is within target_rt_tol of target_rt 
    returns peak_rt, peak_height, peak_fwhm of selected peak
    returns None, None, None if no peaks meet criteria
    """
    peaks = [(r, h, w) for r, h, w in zip(pkrts, pkhts, pkwts) if abs(r - target_rt) <= target_rt_tol]
    n_peaks = len(peaks)
    if n_peaks == 0:
        return None, None, None
    elif n_peaks == 1:
        return peaks[0]
    else:
        imax = -1
        hmax = 0
        for i, peak in enumerate(peaks):
            if peak[1] > hmax:
                hmax = peak[1]
                imax = i
        return peaks[imax]


def _lerp_together(data_a: Union[Xic, Atd], 
                   data_b: Union[Xic, Atd], 
                   dx: float, 
                   normalize: bool = True
                   ) -> Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64], npt.NDArray[np.float64]] :
    """
    take two sets of data (XICs or ATDs) and use linear interpolation to 
    put them both on the same scale
    """
    x_a, y_a = data_a
    x_b, y_b = data_b
    # normalize both signals?
    if normalize:
        y_a = y_a / max(y_a)
        y_b = y_b /  max(y_b)
    # only lerp together for regions where both datasets overlap (max of mins and min of maxs)
    min_x, max_x = max(min(x_a), min(x_b)), min(max(x_a), max(x_b))
    x = np.arange(min_x, max_x + dx, dx)
    return x, np.interp(x, x_a, y_a), np.interp(x, x_b, y_b)


def _decon_distance(pre_data: Union[Xic, Atd], 
                    frag_data: Union[Xic, Atd], 
                    dist_func: str, 
                    lerp_dx: float
                    ) -> float :
    """
    Compute a distance between precursor and fragment data (either XICs or ATDs) using
    a specified distance metric
    """
    dist_funcs = {
        'cosine': spatial.distance.cosine,
        'correlation': spatial.distance.correlation,
        'euclidean': spatial.distance.euclidean,
    }
    x, y_pre, y_frg = _lerp_together(pre_data, frag_data, lerp_dx)
    return dist_funcs[dist_func](y_pre, y_frg)


def _deconvolute_ms2_peaks(rdr: MZA, 
                           sel_ms2_mzs: List[float],
                           pre_xic: Xic, 
                           pre_xic_rt: float, 
                           pre_xic_wt: float, 
                           pre_atd: Atd, 
                           params: DiaDeconvoluteMs2PeaksParams
                           ) -> Tuple[List[Tuple[bool, Optional[float], Optional[float]]],
                                      List[Tuple[Optional[Xic], Optional[Atd]]]] :
    """
    Deconvolute MS2 peak m/zs, if the XIC and ATD are similar enough to the precursor, 
    they are returned as deconvoluted peak m/zs
    
    Parameters
    ----------
    rdr : ``mzapy.MZA``
        interface to raw data
    sel_ms2_mzs : ``list(float)``
        list of selected MS2 peak m/zs
    pre_xic : ``numpy.ndarray(...)``
        precursor XIC
    pre_xic_rt : ``float``
        precursor XIC retention time for ATD extraction
    pre_xic_wt : ``float``
        precursor XIC peak width for ATD extraction
    pre_atd : ``numpy.ndarray(...)``
        precursor ATD
    params : ``DeconvoluteMS2PeaksParams``
        parameters for deconvoluting MS2 peaks

    Returns
    -------
    deconvoluted : ``list(tuple(bool, float or None, float or None))``
        deconvoluted fragment info (flag indicating if it was accepted and XIC/ATD distances)
    raws : ``list(tuple(array or None, array or None))``
        list of optional raw array data for fragment XICs and ATDs
    """
    deconvoluted = []
    raws = []
    for ms2_mz in sel_ms2_mzs:
        flag = False
        xic_dist = None
        ms2_xic = None
        atd_dist = None
        ms2_atd = None
        mz_tol = tol_from_ppm(ms2_mz, params.mz_ppm)
        mz_bounds = (ms2_mz - mz_tol, ms2_mz + mz_tol)
        rt_bounds = (pre_xic_rt - pre_xic_wt, pre_xic_rt + pre_xic_wt)
        # extract fragment XIC 
        ms2_xic = rdr.collect_xic_arrays_by_mz(*mz_bounds, rt_bounds=rt_bounds, mslvl=2)
        # compute XIC distance
        xic_dist = _decon_distance(pre_xic, ms2_xic, params.xic_dist_metric, 0.05)
        if xic_dist <= params.xic_dist_threshold:
            # extract fragment ATD 
            ms2_atd = rdr.collect_atd_arrays_by_rt_mz(*mz_bounds, *rt_bounds, mslvl=2)
            # compute ATD distance
            atd_dist = _decon_distance(pre_atd, ms2_atd, params.atd_dist_metric, 0.25)
            if atd_dist <= params.atd_dist_threshold:
                # accept fragment
                flag = True
        deconvoluted.append((flag, xic_dist, atd_dist))
        raws.append((ms2_xic, ms2_atd))
    return deconvoluted, raws
    

def _add_single_target_results_to_db(cur: ResultsDbCursor, 
                                     dda_pre_id: int, 
                                     dia_file_id: MzaFileId, 
                                     mz: float,
                                     rt: float, 
                                     rt_fwhm: float, 
                                     rt_pkht: float, 
                                     rt_psnr: float, 
                                     dt: float, 
                                     dt_fwhm: float, 
                                     dt_pkht: float, 
                                     dt_psnr: float, 
                                     pre_raws: Tuple[Ms1, Xic, Atd, Ms2],
                                     sel_ms2_mzs: List[float], 
                                     sel_ms2_ints: List[float], 
                                     deconvoluted: List[Tuple[bool, Optional[float], Optional[float]]],
                                     frag_raws: List[Tuple[Optional[Xic], Optional[Atd]]],
                                     store_blobs: bool
                                     ) -> None :
    """ add all of the DIA data to DB for single target """
    ms2_n_peaks = len(sel_ms2_mzs)
    # add the precursor info to the DB
    dia_precursors_qry = """--sqlite3
        INSERT INTO DIAPrecursors VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ;"""
    cur.execute(dia_precursors_qry, (None, dda_pre_id, dia_file_id, mz, 
                                     rt, rt_fwhm, rt_pkht, rt_psnr, 
                                     dt, dt_fwhm, dt_pkht, dt_psnr,
                                     None, ms2_n_peaks))
    # fetch the DIA feature ID that we just added
    dia_feat_id = cur.lastrowid
    # add the fragments to the db
    dia_frag_qry = """--sqlite3
        INSERT INTO DIAFragments VALUES (?,?,?,?,?,?,?)
    ;"""
    for fmz, fint, (decon_flag, xic_dist, atd_dist) in zip(sel_ms2_mzs, sel_ms2_ints, deconvoluted):
        cur.execute(dia_frag_qry, (None, dia_feat_id, fmz, fint, int(decon_flag), xic_dist, atd_dist))
    # if specified, add raw data to the database
    # # convert xic, atd, ms2 to blobs if store_blobs is True, else make them None
    # ms1_qd = np.array(ms1).tobytes() if store_blobs else None
    # xic_qd = np.array(xic).tobytes() if store_blobs else None
    # atd_qd = np.array(atd).tobytes() if store_blobs else None
    # ms2_qd = np.array(ms2).tobytes() if store_blobs else None
   

# TODO (Dylan Ross): This function could probably benefit from being broken up into a couple
#                    smaller functions. In particular, probably one for extracting/fitting
#                    chromatograms, and another for extracting/fitting ATDs

def _single_target_analysis(n: int, 
                            i: int, 
                            rdr: MZA, 
                            cur: ResultsDbCursor, 
                            dia_file_id: MzaFileId, 
                            dda_pid: int, 
                            dda_mz: float, 
                            dda_rt: float, 
                            dda_ms2_n_peaks: Optional[int], 
                            params: DiaParams, 
                            debug_flag: Optional[str], debug_cb: Optional[Callable]
                            ) -> int :
    """
    Perform a complete analysis of DIA data for a single target DDA feature 
    
    Parameters
    ----------
    n : ``int``
        total number of DDA targets we are processing
    i : ``int``
        index of DDA target we are currently processing
    rdr : ``mzapy.MZA``
        MZA instance for extracting raw data
    cur : ``ResultsDbCursor``
        cursor for querying into results database
    dia_file_id : ``int``
        DIA data file ID
    dda_pid : ``int``
        ID of the DDA precursor we are currently processing
    dda_mz : ``float``
        precursor m/z of the DDA precursor we are currently processing
    dda_rt : ``float``
        retention time of the DDA precursor we are currently processing
    dda_ms2_n_peaks : ``int`` or ``None``
        number of MS2 peaks in the DDA MS/MS spectrum for the precursor we are currently processing, 
        can be None in cases where there were no MS/MS scans found for the precursor
    params : ``DiaParams``
        DIA analysis params 
    debug_flag : ``str``, optional
        specifies how to dispatch debugging messages, None to do nothing
    debug_cb : ``func``, optional
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'

    Returns
    -------
    n_features : ``int``
        number of features extracted
    """
    qry_sel_dda_frags = """--sqlite3
        SELECT fmz, fint FROM DDAFragments WHERE dda_pre_id=?
    ;"""
    n_features: int = 0
    pid = os.getpid()
    msg = f"({i + 1}/{n}) DDA precursor ID: {dda_pid}, m/z: {dda_mz:.4f}, RT: {dda_rt:.2f} min -> "
    # extract the XIC, fit 
    rt_bounds = (dda_rt - params.extract_and_fit_chrom_params.rt_tol, 
                 dda_rt + params.extract_and_fit_chrom_params.rt_tol)
    pre_mzt = tol_from_ppm(dda_mz, params.extract_and_fit_chrom_params.mz_ppm)
    pre_xic = rdr.collect_xic_arrays_by_mz(dda_mz - pre_mzt, dda_mz + pre_mzt, rt_bounds=rt_bounds)
    # handle case where XIC is empty 
    # (tight enough bounds and high enough threshold can do that)
    if len(pre_xic[0]) < 2:
        debug_handler(debug_flag, debug_cb, msg +  'empty XIC', pid)
        return 0
    pre_pkrts, pre_pkhts, pre_pkwts = find_peaks_1d_gauss(*pre_xic,
                                                          params.extract_and_fit_chrom_params.min_rel_height,
                                                          params.extract_and_fit_chrom_params.min_abs_height,
                                                          params.extract_and_fit_chrom_params.fwhm_min,
                                                          params.extract_and_fit_chrom_params.fwhm_max,
                                                          params.extract_and_fit_chrom_params.max_peaks, 
                                                          True)
    # determine the closest XIC peak (if any)
    target_rt = dda_rt + params.select_chrom_peaks_params.target_rt_shift
    xic_rt, xic_ht, xic_wt = _select_xic_peak(target_rt, params.select_chrom_peaks_params.target_rt_tol,
                                              pre_pkrts, pre_pkhts, pre_pkwts)
    # proceed if XIC peak was selected
    if xic_rt is not None:
        rtmsg = msg + f"RT: {xic_rt:.2f} +/- {xic_wt:.2f} min ({xic_ht:.2e}) -> "
        xic_psnr = calc_gauss_psnr(*pre_xic, (xic_rt, xic_ht, xic_wt))
        # extract the ATD, fit
        rt_min, rt_max = xic_rt - xic_wt, xic_rt + xic_wt
        pre_atd = rdr.collect_atd_arrays_by_rt_mz(dda_mz - pre_mzt, dda_mz + pre_mzt, rt_min, rt_max)
        # handle case where ATD is empty 
        # (tight enough bounds and high enough threshold can do that)
        if len(pre_atd[0]) < 2:
            debug_handler(debug_flag, debug_cb, msg +  'empty ATD', pid)
            return 0
        pre_pkdts, pre_pkhts, pre_pkwts = find_peaks_1d_gauss(*pre_atd, 
                                                              params.atd_fit_params.min_rel_height,
                                                              params.atd_fit_params.min_abs_height,
                                                              params.atd_fit_params.fwhm_min,
                                                              params.atd_fit_params.fwhm_max,
                                                              params.atd_fit_params.max_peaks, 
                                                              True)
        # consider each ATD peak as separate features
        for atd_dt, atd_ht, atd_wt in zip(pre_pkdts, pre_pkhts, pre_pkwts):
            dtmsg = rtmsg +  f"DT: {atd_dt:.2f} +/- {atd_wt:.2f} ms ({atd_ht:.2e}) -> "
            atd_psnr = calc_gauss_psnr(*pre_atd, (atd_dt, atd_ht, atd_wt))
            # extract partial MS1 spectrum from M-1.5 to M+2.5, with RT and DT selection
            ms1 = rdr.collect_ms1_arrays_by_rt_dt(rt_min, rt_max, 
                                                  atd_dt - atd_wt, atd_dt + atd_wt, 
                                                  mz_bounds=(dda_mz - 1.5, dda_mz + 2.5))
            ms2 = None
            n_ms2_peaks = None
            sel_ms2_mzs = []
            sel_ms2_ints = []
            deconvoluted = []
            frag_raws = []
            if dda_ms2_n_peaks is not None and dda_ms2_n_peaks > 0:
                # extract MS2 spectrum (before deconvolution)
                # only if there are MS/MS peaks from DDA spectrum
                # use those as targets
                ms2 = rdr.collect_ms2_arrays_by_rt_dt(xic_rt - xic_wt, xic_rt + xic_wt, 
                                                      atd_dt - atd_wt, atd_dt + atd_wt, 
                                                      mz_bounds=[rdr.min_mz, dda_mz + 25])
                dia_ms2_peaks = find_peaks_1d_localmax(*ms2,
                                                       params.ms2_fit_params.min_rel_height,
                                                       params.ms2_fit_params.min_abs_height,
                                                       params.ms2_fit_params.fwhm_min,
                                                       params.ms2_fit_params.fwhm_max,
                                                       params.ms2_fit_params.min_dist)
                n_ms2_peaks = len(dia_ms2_peaks[0])
                if n_ms2_peaks > 0:
                    dtmsg += f"# DIA MS2 peaks: {n_ms2_peaks} -> "
                    # try to match peaks from DDA spectrum
                    for ddam, ddai in cur.execute(qry_sel_dda_frags, (dda_pid,)):
                        if ddam < dda_mz + 25:  # only consider MS2 peaks that are less than precursor + 25
                            for diam, diah, diaw in zip(*dia_ms2_peaks):
                                frg_tol = tol_from_ppm(ddam, params.ms2_peak_matching_ppm)
                                if abs(diam - ddam) <= frg_tol:
                                    sel_ms2_mzs.append(diam)
                                    sel_ms2_ints.append(diah)
                    dtmsg += f"matched with DDA: {len(sel_ms2_mzs)}"
                    # deconvolute peaks that were matched from DDA spectrum
                    if len(sel_ms2_mzs) > 0:
                        deconvoluted, frag_raws = _deconvolute_ms2_peaks(rdr, 
                                                                         sel_ms2_mzs, 
                                                                         pre_xic, xic_rt, xic_wt, pre_atd,
                                                                         params.deconvolute_ms2_peaks_params)
                        dtmsg += f" -> deconvoluted: {len([_ for _ in deconvoluted if _[0]])}"
            debug_handler(debug_flag, debug_cb, dtmsg, pid)
            # add the results for this target to the database
            _add_single_target_results_to_db(cur, 
                                             dda_pid, dia_file_id,
                                             dda_mz,
                                             xic_rt, xic_wt, xic_ht, xic_psnr, 
                                             atd_dt, atd_wt, atd_ht, atd_psnr, 
                                             (ms1, pre_xic, pre_atd, ms2),
                                             sel_ms2_mzs, sel_ms2_ints, deconvoluted, frag_raws,
                                             params.store_blobs)
            n_features += 1
    else:
        debug_handler(debug_flag, debug_cb, msg + 'no XIC peak found', pid)
    # return the count of features extracted
    return n_features


def extract_dia_features(dia_data_file: MzaFilePath, 
                         results_db: ResultsDbPath, 
                         params: DiaParams, 
                         debug_flag: Optional[str] = None, debug_cb: Optional[Callable] = None,
                         mza_io_threads: int = 4,
                         ) -> int :
    """
    Extract features from a raw DIA data file, store them in a database 
    (initialized using ``lipidimea.util.create_results_db`` function)

    Parameters
    ----------
    dia_data_file : ``str`` or ``int``
        path to raw DIA data file (MZA format)
    results_db : ``ResultsDbPath``
        path to DDA-DIA analysis results database
    params : ``DiaParams``
        parameters for the various steps of DIA feature extraction
    debug_flag : ``str``, optional
        specifies how to dispatch debugging messages, None to do nothing
    debug_cb : ``func``, optional
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'
    mza_io_threads : ``int``, default=4
        number of I/O threads to specify for the MZA reader object

    Returns
    -------
    n_dia_features : ``int``
        number of DIA features extracted
    """
    # ensure the results database exists
    if not os.path.isfile(results_db):    
        raise FileNotFoundError(errno.ENOENT, 
                                os.strerror(errno.ENOENT), 
                                results_db)
    pid = os.getpid()
    debug_handler(debug_flag, debug_cb, 'Extracting DIA FEATURES', pid)
    debug_handler(debug_flag, debug_cb, f"file: {dia_data_file}", pid)
    # initialize connection to the database
    # increase timeout to avoid errors from database locked by another process
    con = sqlite3.connect(results_db, timeout=120)  
    cur = con.cursor()
    # check if the dia_data_file is a path (str) or file ID from the results database (int)
    match dia_data_file:
        case int():
            dia_file_id: int = dia_data_file
        case str():
            # add the MZA data file to the database and get a file identifier for it
            dia_file_id: int = add_data_file_to_db(cur, "LC-IMS-MS/MS (DIA)", dia_data_file)
            # close database connection
            con.commit()
        case _:
            msg = f"extract_dda_features: invalid type for dda_data_file ({type(dia_data_file)})"
            raise ValueError(msg)
    # initialize the data file reader
    rdr: MZA = MZA(dia_data_file, io_threads=mza_io_threads, cache_scan_data=True)
    # get all of the DDA features, these will be the targets for the DIA data analysis
    pre_sel_qry = """--sqlite3
        SELECT dda_pre_id, mz, rt, ms2_n_peaks FROM DDAPrecursors
    ;"""
    dda_feats = [_ for _ in cur.execute(pre_sel_qry).fetchall()]  
    # extract DIA features for each DDA feature
    n = len(dda_feats)
    n_dia_features: int = 0
    for i, (dda_fid, dda_mz, dda_rt, dda_ms2_n_peaks) in enumerate(dda_feats):
        n_dia_features += _single_target_analysis(n, i, rdr, cur, dia_file_id, dda_fid, 
                                                  dda_mz, dda_rt, dda_ms2_n_peaks, 
                                                  params, debug_flag, debug_cb)
        # commit DB changes after each target? Yes.
        con.commit()
    # commit DB changes at the end of the analysis? No.
    #con.commit()
    # clean up
    con.close()
    rdr.close()
    # return the number of features extracted
    return n_dia_features


# TODO (Dylan Ross): Test out different numbers of MZA I/O threads and see if they cause any problems
#                    or provide any benefits when it comes to running this part of the analysis
#                    with multiprocessing. It might be beneficial for each process to have a few I/O
#                    threads since the primary bottleneck has been disk I/O. Multiple I/O threads should
#                    at least keep the disk reads pinned and the multiprocessing context keeps the CPU 
#                    busy with all of the other stuff that needs to happen besides I/O, at least I think
#                    that is how this should work...
    

def extract_dia_features_multiproc(dia_data_files: List[MzaFilePath], 
                                   results_db: ResultsDbPath, 
                                   params: DiaParams, 
                                   n_proc: int, 
                                   debug_flag: Optional[str] = None, debug_cb: Optional[Callable] = None,
                                   mza_io_threads: int = 4
                                   ) -> Dict[str, int] :
    """
    extracts dda features from multiple DDA files in parallel

    Parameters
    ----------
    dia_data_files : ``list(str)``
        paths to raw DIA data file (MZA format)
    results_db : ``str``
        path to DDA-DIA analysis results database
    params : ``dict(...)``
        parameters for the various steps of DDA feature extraction
    n_proc : ``int``
        number of CPU threads to use (number of processes)
    debug_flag : ``str``, optional
        specifies how to dispatch debugging messages, None to do nothing
    debug_cb : ``func``, optional
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'
    mza_io_threads : ``int``, default=4
        number of I/O threads to specify for the MZA reader objects

    Returns
    -------
    dia_features_per_file : ``dict(str:int)``
        dictionary with the number of DIA features mapped to input DIA data files
    """
    n_proc = min(n_proc, len(dia_data_files))  # no need to use more processes than the number of inputs
    args = [(dia_data_file, results_db, params) for dia_data_file in dia_data_files]
    args_for_starmap = zip(repeat(extract_dia_features), args, repeat({'debug_flag': debug_flag, 
                                                                       'debug_cb': debug_cb, 
                                                                       'mza_io_threads': mza_io_threads}))
    with multiprocessing.Pool(processes=n_proc) as p:
        feat_counts = p.starmap(apply_args_and_kwargs, args_for_starmap)
    return {k: v for k, v in zip(dia_data_files, feat_counts)}


def add_calibrated_ccs_to_dia_features(results_db: ResultsDbPath, 
                                       t_fix: float, 
                                       beta: float
                                       ) -> None :
    """
    Uses calibration parameters to calculate calibrated CCS values from m/z and arrival times of DIA features

    Calibration is for single-field DTIMS measurements and the function is of the form:

    ``CCS = z (arrival_time + t_fix) / (beta * mu(m))``

    Where  ``mu(m)`` is the reduced mass of the analyte with nitrogen

    .. note::

        This method assumes charge=1 and the drift gas is nitrogen

    Parameters
    ----------
    results_db : ``str``
        path to DDA-DIA analysis results database
    t_fix : ``float``
    beta : ``float``
        single-field DTIMS calibration parameters
    """
    # ensure the results database exists
    if not os.path.isfile(results_db):    
        raise FileNotFoundError(errno.ENOENT, 
                                os.strerror(errno.ENOENT), 
                                results_db)
    def ccs(mz, dt, t_fix, beta):
        """ calibrated CCS from m/z, arrival time, and calibration parameters """
        # z = 1, so z can be dropped from the function above
        # and also means that m == mz 
        # buffer gas is N2 -> 28.00615 in reduced mass calculation
        return (dt + t_fix) / (beta * np.sqrt(mz / (mz + 28.00615)))
    # connect to the database
    con = sqlite3.connect(results_db) 
    cur1, cur2 = con.cursor(), con.cursor()  # one cursor to select data, another to update the db with ccs
    # select out the IDs, m/zs and arrival times of the features
    sel_qry = """
        --sqlite3
        SELECT dia_feat_id, mz, dt FROM _DIAFeatures JOIN DDAFeatures USING(dda_feat_id);
    """
    upd_qry = """
        --sqlite3
        UPDATE _DIAFeatures SET ccs=? WHERE dia_feat_id=?;
    """
    for dia_feat_id, mz, dt in cur1.execute(sel_qry).fetchall():
        cur2.execute(upd_qry, (ccs(mz, dt, t_fix, beta), dia_feat_id))
    # clean up
    con.commit()
    con.close()
    
