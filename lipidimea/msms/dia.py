"""
pyliquid/msms/dia.py

Dylan Ross (dylan.ross@pnnl.gov)

    module with DIA MSMS utilities

    TODO (Dylan Ross): get rid of all of the "if debug: print(...)" statements and implement 
                       a debug handler instead, implement in and import from msms/_util.py, 
                       will make these functions much cleaner
"""

from sqlite3 import connect

import numpy as np
from scipy import spatial
from mzapy import MZA
from mzapy.peaks import find_peaks_1d_gauss, find_peaks_1d_localmax, calc_gauss_psnr

from pyliquid.msms._util import _check_params, _str_to_ms2, _ms2_to_str


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


def _lerp_together(data_a, data_b, dx, normalize=True):
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
                deconvoluted.append((ms2_xic, xic_dist, ms2_atd, atd_dist))
    return deconvoluted
    

def _add_single_target_results_to_db(lipid_ids_db_cursor, 
                                     dda_feat_id, f, 
                                     rt, rt_fwhm, rt_pkht, rt_psnr, xic, 
                                     dt, dt_fwhm, dt_pkht, dt_psnr, atd, 
                                     ms2_n_peaks, ms2_peaks, ms2,
                                     decon_frags,
                                     store_blobs, debug):
    """
    dda_feat_id, f, rt, rt_fwhm, rt_pkht, rt_psnr, xic, dt, dt_fwhm, dt_pkht, dt_psnr, atd, ms2_n_peaks, ms2_peaks, ms2
    """
    if debug:
        print('Adding DIA feature to database')
    # convert xic, atd, ms2 to blobs if store_blobs is True, else make them None
    xic = np.array(xic).tobytes() if store_blobs else None
    atd = np.array(atd).tobytes() if store_blobs else None
    ms2 = np.array(ms2).tobytes() if store_blobs else None
    dia_feats_qry = 'INSERT INTO _DIAFeatures VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);'
    lipid_ids_db_cursor.execute(dia_feats_qry, (None, dda_feat_id, f, 
                                                rt, rt_fwhm, rt_pkht, rt_psnr, xic,
                                                dt, dt_fwhm, dt_pkht, dt_psnr, atd,
                                                ms2_n_peaks, ms2_peaks, ms2))
    # fetch the DIA feature ID that we just added
    dia_feat_id = lipid_ids_db_cursor.lastrowid
    # add deconvoluted fragments (if any) to database and associate with this DIA feature
    if decon_frags is not None:
        decon_frags_qry_1 = 'INSERT INTO DIADeconFragments VALUES (?,?,?,?,?);'
        decon_frags_qry_2 = 'INSERT INTO _DIAFeatsToDeconFrags VALUES (?,?);'
        for fxic, fxic_dist, fatd, fatd_dist in decon_frags:
            # convert xic, atd to blobs if store_blobs is True, else make them None
            fxic = np.array(fxic).tobytes() if store_blobs else None
            fatd = np.array(fatd).tobytes() if store_blobs else None
            lipid_ids_db_cursor.execute(decon_frags_qry_1, (None, fxic, fxic_dist, fatd, fatd_dist))
            lipid_ids_db_cursor.execute(decon_frags_qry_2, (dia_feat_id, lipid_ids_db_cursor.lastrowid))
        


def _ms2_peaks_to_str(ms2_peaks):
    """ convert MS2 peaks (i.e. centroided MS2 spectrum) to string representation """
    mzs, iis, _ = ms2_peaks
    return _ms2_to_str(mzs, iis)


def _single_target_analysis(rdr, lipid_ids_db_cursor, f, dda_fid, dda_mz, dda_rt, dda_ms2, params, debug):
    """
    """
    # unpack parameters
    # precursor XIC extraction
    mzt = params['pre_xic_mz_tol']
    rtt = params['pre_xic_rt_tol']
    # precursor XIC fitting
    xic_fit_params = (
        params['min_rel_height'], 
        params['min_abs_height'],
        params['fwhm_min'], 
        params['fwhm_max'], 
        params['max_peaks'],
    )
    # XIC peak selection
    target_rt_shift = params['target_rt_shift']
    target_rt_tol = params['target_rt_tol']
    # precursor ATD fitting 
    atd_fit_params = (
        params['atd_min_rel_height'], 
        params['atd_min_abs_height'],
        params['atd_fwhm_min'], 
        params['atd_fwhm_max'], 
        params['atd_max_peaks'],
    )
    # MS2 peak fitting parameters
    ms2_fit_params = (
        params['ms2_min_rel_height'],
        params['ms2_min_abs_height'], 
        params['ms2_fwhm_min'], 
        params['ms2_fwhm_max'], 
        params['ms2_min_dist'],
    )
    # MS2 peak matching tolerance
    ms2_mzt = params['ms2_pk_mz_tol']
    # Deconvolution XIC and ATD distance thresholds and metrics
    decon_params = (
        params['decon_xic_dist_threshold'], 
        params['decon_atd_dist_threshold'],
        params['decon_xic_dist_metric'],
        params['decon_atd_dist_metric'],
    )
    store_blobs = params['store_blobs']
    if debug:
        print('DDA feature ID:', dda_fid)
        print('DDA feature m/z: {:.4f}'.format(dda_mz))
        print('DDA feature RT: {:.2f} min'.format(dda_rt))
    # extract the XIC, fit 
    rt_bounds = (dda_rt - rtt, dda_rt + rtt)
    pre_xic = rdr.collect_xic_arrays_by_mz(dda_mz - mzt, dda_mz + mzt, rt_bounds=rt_bounds)
    pre_pkrts, pre_pkhts, pre_pkwts = find_peaks_1d_gauss(*pre_xic, *xic_fit_params, True)
    # determine the closest XIC peak (if any)
    target_rt = dda_rt + target_rt_shift
    xic_rt, xic_ht, xic_wt = _select_xic_peak(target_rt, target_rt_tol, pre_pkrts, pre_pkhts, pre_pkwts)
    # proceed if XIC peak was selected
    if xic_rt is not None:
        if debug:
            print('XIC feature RT: {:.2f} +/- {:.2f} min ({:.2e})'.format(xic_rt, xic_wt, xic_ht))
        xic_psnr = calc_gauss_psnr(*pre_xic, (xic_rt, xic_ht, xic_wt))
        # extract the ATD, fit
        pre_atd = rdr.collect_atd_arrays_by_rt_mz(dda_mz - mzt, dda_mz + mzt, xic_rt - xic_wt, xic_rt + xic_wt)
        pre_pkdts, pre_pkhts, pre_pkwts = find_peaks_1d_gauss(*pre_atd, *atd_fit_params, True)
        # consider each ATD peak as separate features
        for atd_dt, atd_ht, atd_wt in zip(pre_pkdts, pre_pkhts, pre_pkwts):
            if debug:
                print('ATD feature DT: {:.2f} +/- {:.2f} ms ({:.2e})'.format(atd_dt, atd_wt, atd_ht))
            atd_psnr = calc_gauss_psnr(*pre_atd, (atd_dt, atd_ht, atd_wt))
            decon_frags = None
            n_dia_peaks_pre_decon = 0
            if dda_ms2 is not None:
                # extract MS2 spectrum (before deconvolution)
                ms2 = rdr.collect_ms2_arrays_by_rt_dt(xic_rt - xic_wt, xic_rt + xic_wt, atd_dt - atd_wt, atd_dt + atd_wt, mz_bounds=[rdr.min_mz, dda_mz + 25])
                dia_ms2_peaks = find_peaks_1d_localmax(*ms2, *ms2_fit_params)
                n_dia_peaks_pre_decon = len(dia_ms2_peaks[0])
                if n_dia_peaks_pre_decon > 0:
                    if debug: 
                        print('# DIA MS2 peaks:', n_dia_peaks_pre_decon)
                    # try to match peaks from DDA spectrum
                    sel_ms2_mzs = []
                    dda_ms2 = _str_to_ms2(dda_ms2)
                    for ddam, ddai in zip(*dda_ms2):
                        if ddam < dda_mz + 25:  # only consider MS2 peaks that are less than precursor + 25
                            for diam, diah, diaw in zip(*dia_ms2_peaks):
                                if abs(diam - ddam) <= ms2_mzt:
                                    sel_ms2_mzs.append(diam)
                    if debug:
                        print('# DIA MS2 peaks matched with DDA spectrum:', len(sel_ms2_mzs))
                    # deconvolute peaks that were matched from DDA spectrum
                    if len(sel_ms2_mzs) > 0:
                        decon_frags = _deconvolute_ms2_peaks(rdr, sel_ms2_mzs, mzt, pre_xic, xic_rt, xic_wt, pre_atd, *decon_params)
                        if debug:
                            print('# deconvoluted DIA MS2 peaks:', len(decon_frags))
            # add the results for this target to the database
            _add_single_target_results_to_db(lipid_ids_db_cursor, 
                                             dda_fid, f, 
                                             xic_rt, xic_wt, xic_ht, xic_psnr, pre_xic, 
                                             atd_dt, atd_wt, atd_ht, atd_psnr, pre_atd, 
                                             n_dia_peaks_pre_decon, _ms2_peaks_to_str(dia_ms2_peaks), ms2,
                                             decon_frags,
                                             store_blobs, debug)



def extract_dia_features(dia_data_file, lipid_ids_db, params, debug=False):
    """
    Extract features from a raw DIA data file, store them in a database (initialized using ``create_dda_ids_db`` function)

    ``params`` dict must contain:
    * ```` - 

    Parameters
    ----------
    dia_data_file : ``str``
        path to raw DIA data file (MZA format)
    lipid_ids_db : ``str``
        path to lipid ids database
    params : ``dict(...)``
        parameters for the various steps of DIA feature extraction
    debug : ``bool``, default=False
        flag indicating whether to print information about the data processing progress
    """
    if debug:
        print('EXTRACTING DIA FEATURES')
        print('file:', dia_data_file)
    # check parameters before proceeding
    """_check_params(params, ['ms2_pre_mz_tol', 'ms2_mz_bin_min', 'ms2_mz_bin_size', 'ms2_min_rel_height',
                           'ms2_min_abs_height', 'ms2_fwhm_min', 'ms2_fwhm_max', 'ms2_min_dist'])"""
    # initialize the data file reader
    rdr = MZA(dia_data_file)
    # initialize connection to the database
    con = connect(lipid_ids_db, timeout=60)  # increase timeout to avoid errors from database locked by another process
    cur = con.cursor()
    
    # get all of the DDA features, these will be the targets for the DIA data analysis
    dda_feats = [_ for _ in cur.execute("SELECT * FROM DDAFeatures WHERE ms2 IS NOT NULL").fetchall()][300:330]
    # extract DIA features for each DDA feature
    for dda_fid, dda_f, dda_mz, dda_rt, dda_rtwt, dda_rtht, dda_rtsnr, dda_ms2ns, dda_ms2np, dda_ms2 in dda_feats:
        if debug:
            print('-' * 40)
        _single_target_analysis(rdr, cur, dia_data_file, dda_fid, dda_mz, dda_rt, dda_ms2, params, debug)
        # commit DB changes after each target?
        #con.commit()
    if debug:
        print('-' * 40)
        
    # commit DB changes at the end of the analysis?
    con.commit()
    # clean up
    con.close()
    rdr.close()
