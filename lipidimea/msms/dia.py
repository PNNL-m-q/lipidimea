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

import numpy as np
import numpy.typing as npt
from scipy import spatial
from mzapy import MZA
from mzapy.peaks import find_peaks_1d_gauss, find_peaks_1d_localmax, calc_gauss_psnr

from lipidimea.msms._util import apply_args_and_kwargs, tol_from_ppm
from lipidimea.util import debug_handler, add_data_file_to_db
from lipidimea.params import (
    DiaParams
)
from lipidimea.typing import (
    Xic, Atd, Ms1, 
    ResultsDbPath, ResultsDbCursor,
    MzaFilePath, MzaFileId
)


# TODO (Dylan Ross): Change the behavior of the DDA data extraction functions to be more like 
#                    the lipid annotation functions: pass around one big DdaParams dataclass
#                    instance and let the functions fetch the parameters they need from it rather
#                    than passing around different parameter subsets.


# general query for inserting data into the Raw table of the results DB
_RAW_INSERT_QRY = """--beginsql
    INSERT INTO Raw VALUES (?,?,?,?,?,?)
--endsql"""


def _select_xic_peak(target_rt: float, 
                     target_rt_tol: float, 
                     pkrts: List[float], 
                     pkhts: List[float], 
                     pkwts: List[float]
                     ) -> Tuple[Optional[float], Optional[float], Optional[float]] :
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
    return x, np.interp(x, x_a, y_a), np.interp(x, x_b, y_b)  # type: ignore


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
                           params: DiaParams
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
    # unpack parameters
    P = params.deconvolute_ms2_peaks
    deconvoluted = []
    raws = []
    for ms2_mz in sel_ms2_mzs:
        flag = False
        xic_dist = None
        ms2_xic = None
        atd_dist = None
        ms2_atd = None
        mz_tol = tol_from_ppm(ms2_mz, params.deconvolute_ms2_peaks.mz_ppm)
        mz_bounds = (ms2_mz - mz_tol, ms2_mz + mz_tol)
        rt_bounds = (pre_xic_rt - pre_xic_wt, pre_xic_rt + pre_xic_wt)
        # extract fragment XIC 
        ms2_xic = rdr.collect_xic_arrays_by_mz(*mz_bounds, rt_bounds=rt_bounds, mslvl=2)
        # compute XIC distance
        xic_dist = _decon_distance(pre_xic, ms2_xic, P.xic_dist_metric, 0.05)
        if xic_dist <= P.xic_dist_threshold:
            # extract fragment ATD 
            ms2_atd = rdr.collect_atd_arrays_by_rt_mz(*mz_bounds, *rt_bounds, mslvl=2)
            # compute ATD distance
            atd_dist = _decon_distance(pre_atd, ms2_atd, P.atd_dist_metric, 0.25)
            if atd_dist <= P.atd_dist_threshold:
                # accept fragment
                flag = True
        deconvoluted.append((flag, xic_dist, atd_dist))
        raws.append((ms2_xic, ms2_atd))
    return deconvoluted, raws
    

def _add_single_target_results_to_db(cur: ResultsDbCursor, 
                                     dda_pre_id: Optional[int], 
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
                                     pre_raws: Tuple[Ms1, Xic, Atd],
                                     sel_ms2_mzs: List[float], 
                                     sel_ms2_ints: List[float], 
                                     deconvoluted: List[Tuple[bool, Optional[float], Optional[float]]],
                                     frag_raws: List[Tuple[Optional[Xic], Optional[Atd]]],
                                     store_blobs: bool
                                     ) -> None :
    """ add all of the DIA data to DB for single target """
    ms2_n_peaks: Optional[int] = npks if (npks := len(sel_ms2_mzs)) > 0 else None
    # add the precursor info to the DB
    dia_precursors_qry = """--beginsql
        INSERT INTO DIAPrecursors VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    --endsql"""
    dia_pre_qdata = (
        None,                           # dia_pre_id will be automatically generated
        dda_pre_id,                     # DDA precursor identifier
        dia_file_id,                    # DIA file identifier
        mz,                             # precursor m/z
        rt, rt_fwhm, rt_pkht, rt_psnr,  # XIC peak parameters (from fit)
        dt, dt_fwhm, dt_pkht, dt_psnr,  # ATD peak parameters (from fit)
        None,                           # no CCS for now, that can be added later using calibration
        ms2_n_peaks                     # number of peaks in the centroided spectrum (can be None if no peaks selected)
    )
    cur.execute(dia_precursors_qry, dia_pre_qdata)
    # fetch the DIA feature ID that we just added
    dia_pre_id = cur.lastrowid
    assert dia_pre_id is not None
    # add the fragments to the db
    dia_frag_qry = """--beginsql
        INSERT INTO DIAFragments VALUES (?,?,?,?,?,?,?)
    --endsql"""
    for fmz, fint, (decon_flag, xic_dist, atd_dist), (fxic, fatd) in zip(
        sel_ms2_mzs, sel_ms2_ints, deconvoluted, frag_raws
    ):
        # add the fragment info
        frag_qdata = (
            None,               # fragment identifier gets generated automatically
            dia_pre_id,         # DIA precursor identifier
            fmz,                # fragment m/z
            fint,               # fragment intensity
            int(decon_flag),    # deconvoluted flag, converted from bool to int to store in DB
            xic_dist,           # xic distance metric (rel. to precursor), can be None
            atd_dist            # atd distance metric (rel. to precursor), can be None
        )
        cur.execute(dia_frag_qry, frag_qdata)
        # optionally add some raw data
        if store_blobs:
            # grab the fragment identifier
            dia_frag_id = cur.lastrowid
            assert dia_frag_id is not None, "last row ID should not be none"
            for farr, raw_type in [(fxic, "DIA_FRAG_XIC"), (fatd, "DIA_FRAG_ATD")]:
                if farr is not None:
                    fblob: bytes = np.array(farr).tobytes()
                    fn: int = len(farr[0])
                    raw_qdata = (
                        None,           # raw_id will be automatically generated
                        raw_type,       # type of raw data being stored (like MS1, XIC, etc.)   
                        "dia_frag_id",  # type of feature identifier to associate with this raw data
                        dia_frag_id,    # feature identifier (DIA fragment)
                        fn,             # number of points in the 2 arrays, makes unpacking easier later on
                        fblob,          # binary data for the arrays (BLOB)
                    )
                    cur.execute(_RAW_INSERT_QRY, raw_qdata)
    # if specified, add raw data to the database
    if store_blobs:
        # unpack and convert precursor raw data to blobs
        for pre_arr, raw_type in zip(pre_raws, ["DIA_PRE_MS1", "DIA_PRE_XIC", "DIA_PRE_ATD"]):
            pre_blob: bytes = np.array(pre_arr).tobytes()
            pre_n: int = len(pre_arr[0])
            raw_qdata = (
                None,           # raw_id will be automatically generated
                raw_type,       # type of raw data being stored (like MS1, XIC, etc.)   
                "dia_pre_id",   # type of feature identifier to associate with this raw data
                dia_pre_id,     # feature identifier (DIA precursor)
                pre_n,          # number of points in the 2 arrays, makes unpacking easier later on
                pre_blob,       # binary data for the arrays (BLOB)
            )
            cur.execute(_RAW_INSERT_QRY, raw_qdata)
   

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
                            dda_rts: str, 
                            dda_ms2_n_peaks: Optional[int], 
                            params: DiaParams, 
                            debug_flag: Optional[str], debug_cb: Optional[Callable]
                            ) -> int :
    """
    Perform a complete analysis of DIA data for a single target DDA feature 
    
    Parameters
    ----------
    n 
        total number of DDA targets we are processing
    i 
        index of DDA target we are currently processing
    rdr 
        MZA instance for extracting raw data
    cur
        cursor for querying into results database
    dia_file_id
        DIA data file ID
    dda_pid 
        ID of the DDA precursor we are currently processing
    dda_mz 
        precursor m/z of the DDA precursor we are currently processing
    dda_rts 
        retention time(s) of the DDA precursor we are currently processing, comma separated string
    dda_ms2_n_peaks : ``int`` or ``None``
        number of MS2 peaks in the DDA MS/MS spectrum for the precursor we are currently processing, 
        can be None in cases where there were no MS/MS scans found for the precursor
    params 
        DIA analysis params 
    debug_flag
        specifies how to dispatch debugging messages, None to do nothing
    debug_cb
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'

    Returns
    -------
    n_features 
        number of features extracted
    """
    # TODO: If ignoring the DDA precursor RT works, then get rid of all of the RT-related stuff left over in
    #       this function. Things like unused parameters, the whole RT peak selecting logic, etc.
    qry_sel_min_max_dda_frags = """--beginsql
        SELECT MIN(fmz), MAX(fmz) FROM DDAFragments WHERE dda_pre_id IN ({})
    --endsql"""
    qry_sel_dda_frags = """--beginsql
        SELECT fmz, fint FROM DDAFragments WHERE dda_pre_id IN ({})
    --endsql"""
    n_features: int = 0
    pid = os.getpid()
    msg = f"({i + 1}/{n}) DDA precursor ID: {dda_pid}, m/z: {dda_mz:.4f}, RT: {dda_rts} min -> "
    # extract the XIC, fit 
    # still use some bounds on XIC extraction, saves time
    _dda_rts: List[float] = [float(_) for _ in dda_rts.split(",")]
    assert params.extract_and_fit_chroms.rt_tol is not None, "extract_and_fit_chroms.rt_tol must be set"
    rt_bounds = (min(_dda_rts) - params.extract_and_fit_chroms.rt_tol, 
                 max(_dda_rts) + params.extract_and_fit_chroms.rt_tol)
    assert params.extract_and_fit_chroms.mz_ppm is not None, "the m/z ppm parameter must be set"
    pre_mzt = tol_from_ppm(dda_mz, params.extract_and_fit_chroms.mz_ppm)
    pre_xic = rdr.collect_xic_arrays_by_mz(dda_mz - pre_mzt, dda_mz + pre_mzt, rt_bounds=rt_bounds)
    # handle case where XIC is empty 
    # (tight enough bounds and high enough threshold can do that)
    if len(pre_xic[0]) < 2:
        debug_handler(debug_flag, debug_cb, msg +  'empty XIC', pid)
        return 0
    pre_pkrts, pre_pkhts, pre_pkwts = find_peaks_1d_gauss(*pre_xic,
                                                          params.extract_and_fit_chroms.min_rel_height,
                                                          params.extract_and_fit_chroms.min_abs_height,
                                                          params.extract_and_fit_chroms.fwhm.min,
                                                          params.extract_and_fit_chroms.fwhm.max,
                                                          params.extract_and_fit_chroms.max_peaks, 
                                                          True)
    # determine the closest XIC peak (if any)
    # target_rt = dda_rt + params.select_chrom_peaks_params.target_rt_shift
    # xic_rt, xic_ht, xic_wt = _select_xic_peak(target_rt, params.select_chrom_peaks_params.target_rt_tol,
    #                                           pre_pkrts, pre_pkhts, pre_pkwts)
    # proceed if XIC peak was selected
    # if xic_rt is not None:
    # Proceed with all XIC peaks, regardless of whether they were matched with DDA feature. We can assign later on.
    for xic_rt, xic_ht, xic_wt in zip(pre_pkrts, pre_pkhts, pre_pkwts):
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
                                                              params.extract_and_fit_atds.min_rel_height,
                                                              params.extract_and_fit_atds.min_abs_height,
                                                              params.extract_and_fit_atds.fwhm.min,
                                                              params.extract_and_fit_atds.fwhm.max,
                                                              params.extract_and_fit_atds.max_peaks, 
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
                # use those as targets? Not really. Currently we are just extracting the whole
                # MS2 spectrum then doing peak picking and trying to match those up with the DDA
                # MS2 peaks. So, not really a targeted approach.
                # one thing we can do though is grab the min/max mz from the DDA MS2 spectrum peaks
                # and only extract from that range. Could really reduce the amount of data we need 
                # to pull out of the DIA file, therefore speeding things up.
                min_fmz, max_fmz = cur.execute(qry_sel_min_max_dda_frags.format(dda_pid)).fetchall()[0]
                ms2 = rdr.collect_ms2_arrays_by_rt_dt(xic_rt - xic_wt, xic_rt + xic_wt, 
                                                      atd_dt - atd_wt, atd_dt + atd_wt, 
                                                      mz_bounds=[min_fmz - 1, max_fmz + 1])
                if len(ms2[0]) > 1:
                    dia_ms2_peaks = find_peaks_1d_localmax(*ms2,
                                                           params.extract_and_fit_ms2_spectra.min_rel_height,
                                                           params.extract_and_fit_ms2_spectra.min_abs_height,
                                                           params.extract_and_fit_ms2_spectra.fwhm.min,
                                                           params.extract_and_fit_ms2_spectra.fwhm.max,
                                                           params.extract_and_fit_ms2_spectra.peak_min_dist)
                    n_ms2_peaks = len(dia_ms2_peaks[0])
                    if n_ms2_peaks > 0:
                        dtmsg += f"# DIA MS2 peaks: {n_ms2_peaks} -> "
                        # try to match peaks from DDA spectrum
                        # do it this way in an attempt to avoid overcounting fragments
                        # not perfect but should help
                        dda_fmzs = set([
                            round(r[0], 3) 
                            for r in cur.execute(qry_sel_dda_frags.format(dda_pid)).fetchall()
                        ])
                        for ddam in dda_fmzs:
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
                                                                            params)
                            dtmsg += f" -> deconvoluted: {len([_ for _ in deconvoluted if _[0]])}"
            debug_handler(debug_flag, debug_cb, dtmsg, pid)
            # add the results for this target to the database
            # NOTE: No need to store the full MS2 spectrum as a blob, as it may only be a partial spectrum anyways
            #       because the data extraction is semi-targeted based on fragments from the DDA MS2 spectrum.
            #       The fragment info that already gets stored is more than sufficient. Plus at a conceptual level
            #       we are only dealing in centroided MS2 spectra in this package as a whole, so it does not make
            #       sense to store the profile data as well (plus plus it takes up a ton of space).
            _add_single_target_results_to_db(cur, 
                                             None, 
                                             dia_file_id,
                                             dda_mz,
                                             xic_rt, xic_wt, xic_ht, xic_psnr, 
                                             atd_dt, atd_wt, atd_ht, atd_psnr, 
                                             (ms1, pre_xic, pre_atd),
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
    con = sqlite3.connect(results_db, timeout=300)  
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
    # NOTE: We group by precursor m/z, keep all dda_pre_ids, and sum together ms2_n_peaks which
    #       means that we are only going by unique m/z value and combining all the rest of the 
    #       info for all matching precursors from DDA. This goes with the change in the DIA feature
    #       extraction procedure where instead of trying to select the XIC peak that most closely
    #       matches a particular DDA feature RT we just consider all XIC peaks for the DIA feature
    #       separately and a mapping between the DDA and DIA features can be done later based on 
    #       m/z and RT of the DDA and DIA features.
    pre_sel_qry = """--beginsql
        SELECT 
            GROUP_CONCAT(dda_pre_id) AS dda_pre_ids, 
            mz, 
            GROUP_CONCAT(rt) AS rts, 
            SUM(ms2_n_peaks) AS sum_ms2_n_peaks 
        FROM 
            DDAPrecursors
        GROUP BY
            mz
    --endsql"""
    dda_feats = [_ for _ in cur.execute(pre_sel_qry).fetchall()]
    # extract DIA features for each DDA feature
    n = len(dda_feats)
    n_dia_features: int = 0
    for i, (dda_fids, dda_mz, dda_rts, dda_ms2_n_peaks) in enumerate(dda_feats):
        n_dia_features += _single_target_analysis(n, i, rdr, cur, dia_file_id, dda_fids, 
                                                  dda_mz, dda_rts, dda_ms2_n_peaks, 
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
                                       dfile_id: int,
                                       t_fix: float, 
                                       beta: float
                                       ) -> None :
    """
    Uses calibration parameters to calculate calibrated CCS values from m/z and arrival times of DIA features

    Applies calibration to a features from a single DIA data file (specified by dfile_id)

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
    sel_qry = """--beginsql
        SELECT dia_pre_id, mz, dt FROM DIAPrecursors WHERE dfile_id=?
    --endsql"""
    upd_qry = """--beginsql
        UPDATE DIAPrecursors SET ccs=? WHERE dia_pre_id=?
    --endsql"""
    for dia_pre_id, mz, dt in cur1.execute(sel_qry, (dfile_id,)).fetchall():
        cur2.execute(upd_qry, (ccs(mz, dt, t_fix, beta), dia_pre_id))
    # clean up
    con.commit()
    con.close()
    
