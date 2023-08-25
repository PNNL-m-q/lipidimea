"""
LipidIMEA/msms/dia.py

Dylan Ross (dylan.ross@pnnl.gov)

    module with DIA MSMS utilities

    TODO (Dylan Ross): get rid of all of the "if debug: print(...)" statements and implement 
                       a debug handler instead, implement in and import from msms/_util.py, 
                       will make these functions much cleaner
"""


from sqlite3 import connect
import os
from itertools import repeat
import multiprocessing

import numpy as np
from scipy import spatial
from mzapy import MZA
from mzapy.peaks import find_peaks_1d_gauss, find_peaks_1d_localmax, calc_gauss_psnr

from LipidIMEA.msms._util import str_to_ms2, ms2_to_str, debug_handler, apply_args_and_kwargs


def _select_xic_peak(target_rt, target_rt_tol, pkrts, pkhts, pkwts):
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


def _lerp_together(data_a, data_b, dx, 
                   normalize=True):
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


def _decon_distance(pre_data, frag_data, metric, lerp_dx):
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
    return dist_funcs[metric](y_pre, y_frg)


def _deconvolute_ms2_peaks(rdr, sel_ms2_mzs, mz_tol, pre_xic, pre_xic_rt, pre_xic_wt, pre_atd, 
                           xic_dist_threshold, atd_dist_threshold, xic_dist_metric, atd_dist_metric):
    """
    Deconvolute MS2 peak m/zs, if the XIC and ATD are similar enough to the precursor, 
    they are returned as deconvoluted peak m/zs
    
    Parameters
    ----------
    rdr : ``mzapy.MZA``
        interface to raw data
    sel_ms2_mzs : ``list(float)``
        list of selected MS2 peak m/zs
    mz_tol : ``float``
        m/z tolerance for XIC extraction
    pre_xic : ``numpy.ndarray(...)``
        precursor XIC
     pre_xic_rt : ``float``
        precursor XIC retention time for ATD extraction
    pre_xic_wt : ``float``
        precursor XIC peak width for ATD extraction
    rt_tol : ``float``
        RT tolerance for XIC extraction
    pre_atd : ``numpy.ndarray(...)``
        precursor ATD
    xic_dist_threshold : ``float``
        distance threshold for accepting fragment using precursor and fragments XICs
    atd_dist_threshold : ``float``
        distance threshold for accepting fragment using precursor and fragments ATDs
    xic_dist_metric : ``str``
        distance metric for XIC comparison
    atd_dist_metric : ``str``
        distance metric for ATD comparison
    Returns
    -------
    decon_ms2_mzs : ``list(float)``
        deconvoluted MS2 peak m/zs 
    """
    deconvoluted = []
    for ms2_mz in sel_ms2_mzs:
        mz_bounds = (ms2_mz - mz_tol, ms2_mz + mz_tol)
        rt_bounds = (pre_xic_rt - pre_xic_wt, pre_xic_rt + pre_xic_wt)
        # extract fragment XIC 
        ms2_xic = rdr.collect_xic_arrays_by_mz(*mz_bounds, rt_bounds=rt_bounds, mslvl=2)
        # compute XIC distance
        xic_dist = _decon_distance(pre_xic, ms2_xic, xic_dist_metric, 0.05)
        if xic_dist <= xic_dist_threshold:
            # extract fragment ATD 
            ms2_atd = rdr.collect_atd_arrays_by_rt_mz(*mz_bounds, *rt_bounds, mslvl=2)
            # compute ATD distance
            atd_dist = _decon_distance(pre_atd, ms2_atd, atd_dist_metric, 0.25)
            if atd_dist <= atd_dist_threshold:
                # accept fragment
                deconvoluted.append((ms2_mz, ms2_xic, xic_dist, ms2_atd, atd_dist))
    return deconvoluted
    

def _add_single_target_results_to_db(lipid_ids_db_cursor, 
                                     dda_feat_id, f, 
                                     ms1,
                                     rt, rt_fwhm, rt_pkht, rt_psnr, xic, 
                                     dt, dt_fwhm, dt_pkht, dt_psnr, atd, 
                                     ms2_n_peaks, ms2_peaks, ms2,
                                     decon_frags,
                                     store_blobs):
    """ add all of the DIA data to DB for single target """
    # convert xic, atd, ms2 to blobs if store_blobs is True, else make them None
    ms1 = np.array(ms1).tobytes() if store_blobs else None
    xic = np.array(xic).tobytes() if store_blobs else None
    atd = np.array(atd).tobytes() if store_blobs else None
    ms2 = np.array(ms2).tobytes() if store_blobs else None
    dia_feats_qry = 'INSERT INTO _DIAFeatures VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);'
    lipid_ids_db_cursor.execute(dia_feats_qry, (None, dda_feat_id, f,
                                                ms1,
                                                rt, rt_fwhm, rt_pkht, rt_psnr, xic,
                                                dt, dt_fwhm, dt_pkht, dt_psnr, atd,
                                                ms2_n_peaks, ms2_peaks, ms2))
    # fetch the DIA feature ID that we just added
    dia_feat_id = lipid_ids_db_cursor.lastrowid
    # add deconvoluted fragments (if any) to database and associate with this DIA feature
    if decon_frags is not None:
        decon_frags_qry_1 = 'INSERT INTO DIADeconFragments VALUES (?,?,?,?,?,?);'
        decon_frags_qry_2 = 'INSERT INTO _DIAFeatsToDeconFrags VALUES (?,?);'
        for fmz, fxic, fxic_dist, fatd, fatd_dist in decon_frags:
            # convert xic, atd to blobs if store_blobs is True, else make them None
            fxic = np.array(fxic).tobytes() if store_blobs else None
            fatd = np.array(fatd).tobytes() if store_blobs else None
            lipid_ids_db_cursor.execute(decon_frags_qry_1, (None, fmz, fxic, fxic_dist, fatd, fatd_dist))
            lipid_ids_db_cursor.execute(decon_frags_qry_2, (dia_feat_id, lipid_ids_db_cursor.lastrowid))
        

def _ms2_peaks_to_str(ms2_peaks):
    """ convert MS2 peaks (i.e. centroided MS2 spectrum) to string representation """
    if ms2_peaks is None:
        return None
    mzs, iis, _ = ms2_peaks
    return ms2_to_str(mzs, iis)


def _single_target_analysis(rdr, lipid_ids_db_cursor, f, dda_fid, dda_mz, dda_rt, dda_ms2, params, debug_flag, debug_cb):
    """
    Perform a complete analysis of a single target
    """
    pid = os.getpid()
    # unpack parameters
    # precursor XIC extraction
    mzt = params['dia']['dia_chrom_ext_fit']['dia_cxf_pre_xic_mz_tol']
    rtt = params['dia']['dia_chrom_ext_fit']['dia_cxf_pre_xic_rt_tol']
    # precursor XIC fitting
    xic_fit_params = (
        params['dia']['dia_chrom_ext_fit']['dia_cxf_min_rel_height'], 
        params['dia']['dia_chrom_ext_fit']['dia_cxf_min_abs_height'],
        params['dia']['dia_chrom_ext_fit']['dia_cxf_fwhm_min'], 
        params['dia']['dia_chrom_ext_fit']['dia_cxf_fwhm_max'], 
        params['dia']['dia_chrom_ext_fit']['dia_cxf_max_peaks'],
    )
    # XIC peak selection
    target_rt_shift = params['dia']['dia_sel_xic_pks']['dia_sxp_target_rt_shift']
    target_rt_tol = params['dia']['dia_sel_xic_pks']['dia_sxp_target_rt_tol']
    # precursor ATD fitting 
    atd_fit_params = (
        params['dia']['dia_atd_ext_fit']['dia_axf_min_rel_height'], 
        params['dia']['dia_atd_ext_fit']['dia_axf_min_abs_height'],
        params['dia']['dia_atd_ext_fit']['dia_axf_fwhm_min'], 
        params['dia']['dia_atd_ext_fit']['dia_axf_fwhm_max'], 
        params['dia']['dia_atd_ext_fit']['dia_axf_max_peaks'],
    )
    # MS2 peak fitting parameters
    ms2_fit_params = (
        params['dia']['dia_ms2_ext_fit']['dia_mxf_min_rel_height'],
        params['dia']['dia_ms2_ext_fit']['dia_mxf_min_abs_height'], 
        params['dia']['dia_ms2_ext_fit']['dia_mxf_fwhm_min'], 
        params['dia']['dia_ms2_ext_fit']['dia_mxf_fwhm_max'], 
        params['dia']['dia_ms2_ext_fit']['dia_mxf_min_dist'],
    )
    # MS2 peak matching tolerance
    ms2_mzt = params['dia']['dia_ms2_pk_mat']['dia_mpm_mz_tol']
    # Deconvolution XIC and ATD distance thresholds and metrics
    decon_params = (
        params['dia']['dia_ms2_decon']['dia_md_xic_dist_threshold'], 
        params['dia']['dia_ms2_decon']['dia_md_atd_dist_threshold'],
        params['dia']['dia_ms2_decon']['dia_md_xic_dist_metric'],
        params['dia']['dia_ms2_decon']['dia_md_atd_dist_metric'],
    )
    store_blobs = params['misc']['dia_store_blobs']
    msg = 'DDA feature ID: {}, m/z: {:.4f}, RT: {:.2f} min -> '.format(dda_fid, dda_mz, dda_rt)
    # extract the XIC, fit 
    rt_bounds = (dda_rt - rtt, dda_rt + rtt)
    pre_xic = rdr.collect_xic_arrays_by_mz(dda_mz - mzt, dda_mz + mzt, rt_bounds=rt_bounds)
    pre_pkrts, pre_pkhts, pre_pkwts = find_peaks_1d_gauss(*pre_xic, *xic_fit_params, True)
    # determine the closest XIC peak (if any)
    target_rt = dda_rt + target_rt_shift
    xic_rt, xic_ht, xic_wt = _select_xic_peak(target_rt, target_rt_tol, pre_pkrts, pre_pkhts, pre_pkwts)
    # proceed if XIC peak was selected
    if xic_rt is not None:
        rtmsg = msg + 'RT: {:.2f} +/- {:.2f} min ({:.2e}) -> '.format(xic_rt, xic_wt, xic_ht)
        xic_psnr = calc_gauss_psnr(*pre_xic, (xic_rt, xic_ht, xic_wt))
        # extract the ATD, fit
        rt_min, rt_max = xic_rt - xic_wt, xic_rt + xic_wt
        pre_atd = rdr.collect_atd_arrays_by_rt_mz(dda_mz - mzt, dda_mz + mzt, rt_min, rt_max)
        pre_pkdts, pre_pkhts, pre_pkwts = find_peaks_1d_gauss(*pre_atd, *atd_fit_params, True)
        # consider each ATD peak as separate features
        for atd_dt, atd_ht, atd_wt in zip(pre_pkdts, pre_pkhts, pre_pkwts):
            dtmsg = rtmsg +  'DT: {:.2f} +/- {:.2f} ms ({:.2e}) -> '.format(atd_dt, atd_wt, atd_ht)
            atd_psnr = calc_gauss_psnr(*pre_atd, (atd_dt, atd_ht, atd_wt))
            # extract partial MS1 spectrum from M-1.5 to M+2.5, with RT and DT selection
            ms1 = rdr.collect_ms1_arrays_by_rt_dt(rt_min, rt_max, atd_dt - atd_wt, atd_dt + atd_wt, 
                                                  mz_bounds=(dda_mz - 1.5, dda_mz + 2.5))
            ms2 = None
            dia_ms2_peaks = None
            decon_frags = None
            n_dia_peaks_pre_decon = None
            if dda_ms2 is not None:
                # extract MS2 spectrum (before deconvolution)
                ms2 = rdr.collect_ms2_arrays_by_rt_dt(xic_rt - xic_wt, xic_rt + xic_wt, atd_dt - atd_wt, atd_dt + atd_wt, 
                                                      mz_bounds=[rdr.min_mz, dda_mz + 25])
                dia_ms2_peaks = find_peaks_1d_localmax(*ms2, *ms2_fit_params)
                n_dia_peaks_pre_decon = len(dia_ms2_peaks[0])
                if n_dia_peaks_pre_decon > 0:
                    dtmsg += '# DIA MS2 peaks: {} -> '.format(n_dia_peaks_pre_decon)
                    # try to match peaks from DDA spectrum
                    sel_ms2_mzs = []
                    dda_ms2_arr = str_to_ms2(dda_ms2)
                    for ddam, ddai in zip(*dda_ms2_arr):
                        if ddam < dda_mz + 25:  # only consider MS2 peaks that are less than precursor + 25
                            for diam, diah, diaw in zip(*dia_ms2_peaks):
                                if abs(diam - ddam) <= ms2_mzt:
                                    sel_ms2_mzs.append(diam)
                    dtmsg += 'matched with DDA: {}'.format(len(sel_ms2_mzs))
                    # deconvolute peaks that were matched from DDA spectrum
                    if len(sel_ms2_mzs) > 0:
                        decon_frags = _deconvolute_ms2_peaks(rdr, sel_ms2_mzs, mzt, pre_xic, xic_rt, xic_wt, pre_atd, *decon_params)
                        dtmsg += ' -> deconvoluted: {}'.format(len(decon_frags))
            debug_handler(debug_flag, debug_cb, dtmsg, pid)
            # add the results for this target to the database
            _add_single_target_results_to_db(lipid_ids_db_cursor, 
                                             dda_fid, f,
                                             ms1,
                                             xic_rt, xic_wt, xic_ht, xic_psnr, pre_xic, 
                                             atd_dt, atd_wt, atd_ht, atd_psnr, pre_atd, 
                                             n_dia_peaks_pre_decon, _ms2_peaks_to_str(dia_ms2_peaks), ms2,
                                             decon_frags,
                                             store_blobs)


def extract_dia_features(dia_data_file, lipid_ids_db, params, 
                         debug_flag=None, debug_cb=None):
    """
    Extract features from a raw DIA data file, store them in a database (initialized using ``create_dda_ids_db`` function)

    Parameters
    ----------
    dia_data_file : ``str``
        path to raw DIA data file (MZA format)
    lipid_ids_db : ``str``
        path to lipid ids database
    params : ``dict(...)``
        parameters for the various steps of DIA feature extraction
    debug_flag : ``str``, optional
        specifies how to dispatch debugging messages, None to do nothing
    debug_cb : ``func``, optional
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'
    """
    pid = os.getpid()
    debug_handler(debug_flag, debug_cb, 'Extracting DIA FEATURES', pid)
    debug_handler(debug_flag, debug_cb, 'file: {}'.format(dia_data_file), pid)
    # initialize the data file reader
    rdr = MZA(dia_data_file, io_threads=1, cache_scan_data=True)
    # initialize connection to the database
    con = connect(lipid_ids_db, timeout=60)  # increase timeout to avoid errors from database locked by another process
    cur = con.cursor()
    # get all of the DDA features, these will be the targets for the DIA data analysis
    pre_sel_qry = 'SELECT dda_feat_id, mz, rt, ms2_peaks FROM DDAFeatures'
    dda_feats = [_ for _ in cur.execute(pre_sel_qry).fetchall()]  
    # extract DIA features for each DDA feature
    for dda_fid,dda_mz, dda_rt, dda_ms2 in dda_feats:
        _single_target_analysis(rdr, cur, dia_data_file, dda_fid, dda_mz, dda_rt, dda_ms2, params, debug_flag, debug_cb)
        # commit DB changes after each target? Yes.
        con.commit()
    # commit DB changes at the end of the analysis? No.
    #con.commit()
    # clean up
    con.close()
    rdr.close()


# TODO (Dylan Ross): Is there something wrong with using multiprocessing with the MZA object that uses multithreaded IO
#                       that keeps causing this to hang after some number of targets? Need to maybe implement an option
#                       for MZA not to use multithreaded IO for cases such as this... But then again, I was able to run
#                       LipidOz with multiprocessing without issue and LipidOz uses MZA for file access as well... need
#                       to dig into this some more and figure out why the hanging keeps happening. In any case, having
#                       this multiprocessing option for DIA analysis is a must for real applications as there will be
#                       multiple DIA files to analyze.
def extract_dia_features_multiproc(dia_data_files, lipid_ids_db, params, n_proc, 
                                   debug_flag=None, debug_cb=None):
    """
    extracts dda features from multiple DDA files in parallel

    ``params`` dict must contain:
    * ``?``

    Parameters
    ----------
    dda_data_files : ``list(str)``
        paths to raw DDA data file (MZA format)
    lipid_ids_db : ``str``
        path to lipid ids database
    params : ``dict(...)``
        parameters for the various steps of DDA feature extraction
    n_proc : ``int``
        number of CPU threads to use (number of processes)
    debug_flag : ``str``, optional
        specifies how to dispatch debugging messages, None to do nothing
    debug_cb : ``func``, optional
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'
    """
    n_proc = min(n_proc, len(dia_data_files))  # no need to use more processes than the number of inputs
    args = [(dia_data_file, lipid_ids_db, params) for dia_data_file in dia_data_files]
    args_for_starmap = zip(repeat(extract_dia_features), args, repeat({'debug_flag': debug_flag, 'debug_cb': debug_cb}))
    with multiprocessing.Pool(processes=n_proc) as p:
        p.starmap(apply_args_and_kwargs, args_for_starmap)
