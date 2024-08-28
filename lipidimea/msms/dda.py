"""
lipidimea/msms/dda.py

Dylan Ross (dylan.ross@pnnl.gov)

    module with DDA MSMS utilities

"""


from typing import List, Any, Set, Callable, Optional, Dict, Tuple
import sqlite3
from time import time, sleep
from itertools import repeat
import multiprocessing
import os

from mzapy.dda import MsmsReaderDda, MsmsReaderDdaCachedMs1
from mzapy.peaks import find_peaks_1d_gauss, find_peaks_1d_localmax, calc_gauss_psnr
from mzapy.view import plot_spectrum, plot_chrom

from lipidimea.typing import (
    ResultsDbConnection, ResultsDbCursor, ResultsDbPath, DdaReader, DdaChromFeat, DdaFeature,
    MzaFilePath
)
from lipidimea.msms._util import (
    ms2_to_str, apply_args_and_kwargs, ppm_from_delta_mz, tol_from_ppm
)
from lipidimea.util import debug_handler
from lipidimea.params import (
    DdaExtractAndFitChromsParams, DdaConsolidateChromFeatsParams, DdaExtractAndFitMs2SpectraParams,
    DdaParams
)


def _extract_and_fit_chroms(rdr: DdaReader, 
                            pre_mzs: Set[float], 
                            params: DdaExtractAndFitChromsParams,
                            debug_flag: Optional[str], debug_cb: Optional[Callable] 
                            ) -> List[DdaChromFeat] :
    """
    extracts and fits chromatograms for a list of precursor m/zs 

    Parameters
    ----------
    rdr : ``_MSMSReaderDDA``
        object for accessing DDA MSMS data from MZA
    pre_mzs : ``set(float)``
        sorted unique precursor m/zs
    params : ``ExtractAndFitChromsParams``
        parameters for data extraction and fitting
    debug_flag : ``str``
        specifies how to dispatch debugging messages, None to do nothing
    debug_cb : ``func``
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'

    Returns
    -------
    features : ``list(tuple(...))``
        list of chromatographic features (pre_mz, peak RT, peak height, peak FWHM, pSNR)
    """
    pid = os.getpid()
    # extract chromatograms
    debug_handler(debug_flag, debug_cb, 'EXTRACTING AND FITTING CHROMATOGRAMS', pid)
    features: List[DdaChromFeat] = []
    t0 = time()
    n: int = len(pre_mzs)
    for i, pre_mz in enumerate(pre_mzs): 
        msg = f"({i + 1}/{n}) precursor m/z: {pre_mz:.4f} -> "
        # extract chromatogram
        chrom = rdr.get_chrom(pre_mz, tol_from_ppm(pre_mz, params.mz_ppm))
        plot_chrom(*chrom, figname="show")
        # try fitting chromatogram (up to n peaks)
        _pkrts, _pkhts, _pkwts = find_peaks_1d_gauss(*chrom, 
                                                     params.min_rel_height, params.min_abs_height, 
                                                     params.fwhm_min, params.fwhm_max, 
                                                     params.max_peaks, True)
        # calc pSNR for each fitted peak, make sure they meet a threshold
        pkrts, pkhts, pkwts, psnrs = [], [], [], []
        for pkparams in zip(_pkrts, _pkhts, _pkwts):
            psnr = calc_gauss_psnr(*chrom, pkparams)
            if psnr > params.min_psnr:
                pkrts.append(pkparams[0])
                pkhts.append(pkparams[1])
                pkwts.append(pkparams[2])
                psnrs.append(psnr)
        if len(pkrts) > 0:
            for r, h, w, s in zip(pkrts, pkhts, pkwts, psnrs):
                pkinfo = f"RT: {r:.2f} +/- {w:.2f} min ({h:.1e}, {s:.1f}) "
                debug_handler(debug_flag, debug_cb, msg + pkinfo, pid)
                features.append((pre_mz, r, h, w, s))
        else: 
            debug_handler(debug_flag, debug_cb, msg + 'no peaks found', pid)
    debug_handler(debug_flag, debug_cb, f"EXTRACTING AND FITTING CHROMATOGRAMS: elapsed: {time() - t0:.1f} s", pid)
    return features


def _consolidate_chrom_feats(feats: List[DdaChromFeat], 
                             params: DdaConsolidateChromFeatsParams, 
                             debug_flag: Optional[str], debug_cb: Optional[Callable] 
                             ) -> List[DdaChromFeat] :
    """
    consolidate chromatographic features that have very similar m/z and RT
    only keep highest intensity features

    Parameters
    ----------
    feats : ``list(tuple(...))``
        list of chromatographic features (pre_mz, peak RT, peak FWHM, peak height, pSNR)
    params : ``ConsolidateChromFeatsParams``
        parameters for consolidating chromatographic features
    debug_flag : ``str``
        specifies how to dispatch debugging messages, None to do nothing
    debug_cb : ``func``
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'

    Returns
    -------
    feats_consolidated : ``list(tuple(...))``
        list of consolidated chromatographic features (pre_mz, peak RT, peak FWHM, peak height, pSNR)
    """
    pid = os.getpid()
    # consolidate features
    features_consolidated: List[DdaChromFeat] = []
    for feat in feats:
        add: bool = True
        for i in range(len(features_consolidated)):
            fc_i: DdaChromFeat = features_consolidated[i]
            delta_mz: float = abs(feat[0] - fc_i[0])
            if ppm_from_delta_mz(delta_mz, fc_i[0]) <= params.mz_ppm and abs(feat[1] - fc_i[1]) <= params.rt_tol:
                add = False
                if feat[2] > fc_i[2]:
                    features_consolidated[i] = feat
        if add:
            features_consolidated.append(feat)
    msg = f"CONSOLIDATING CHROMATOGRAPHIC FEATURES: {len(feats)} features -> {len(features_consolidated)} features"
    debug_handler(debug_flag, debug_cb, msg, pid)
    return features_consolidated


def _extract_and_fit_ms2_spectra(rdr: DdaReader,
                                 chrom_feats_consolidated: List[DdaChromFeat],
                                 params: DdaExtractAndFitMs2SpectraParams,
                                 debug_flag: Optional[str], debug_cb: Optional[Callable] 
                                 ) -> List[DdaFeature] :
    """
    extracts MS2 spectra for consolidated chromatographic features, tries to fit spectra peaks,
    returns query data for adding features to database

    Parameters
    ----------
    rdr : ``_MSMSReaderDDA``
        object for accessing DDA MSMS data from MZA
    chrom_feats_consolidated : ``list(tuple(...))``
        list of consolidated chromatographic features (pre_mz, peak RT, peak FWHM, peak height, pSNR)
    params : ``ExtractAndFitMS2SpectraParams``
        parameters for mass spectum extraction and fitting
    debug_flag : ``str``
        specifies how to dispatch debugging messages, None to do nothing
    debug_cb : ``func``
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'

    Returns
    -------
    qdata : ``list(tuple(...))``
        list of query data for all of the features
            [None, str, float, float, float, float, float, int, Optional[int], Optional[str]]
    """
    pid: int = os.getpid()
    # extract and fit MS2 spectra, return query data
    debug_handler(debug_flag, debug_cb, 'EXTRACTING AND FITTING MS2 SPECTRA', pid)
    t0 = time()
    qdata: List[DdaFeature] = []
    n: int = len(chrom_feats_consolidated)
    for i, (fmz, frt, fht, fwt, fsnr) in enumerate(chrom_feats_consolidated):
        msg: str = f"({i + 1}/{n}) m/z: {fmz:.4f} RT: {frt:.2f} +/- {fwt:.2f} min ({fht:.1e}, {fsnr:.1f}) -> "
        # RT range is peak RT +/- peak FWHM
        rt_min: float = frt - fwt  
        rt_max: float = frt + fwt  
        mz_bin_max: float = fmz + 5  # only extract MS2 spectrum up to precursor m/z + 5 Da
        # (try to) extract MS2 spectrum
        ms2 = rdr.get_msms_spectrum(fmz, tol_from_ppm(fmz, params.pre_mz_ppm), rt_min, rt_max, 
                                    params.mz_bin_min, mz_bin_max, params.mz_bin_size)
        mz_bins, i_bins, n_scan_pre_mzs, scan_pre_mzs = ms2
        print(f"{n_scan_pre_mzs=}")
        print(f"{scan_pre_mzs=}")
        plot_spectrum(mz_bins, i_bins, figname="show")
        msg += '# MS2 scans: {} '.format(n_scan_pre_mzs)
        if n_scan_pre_mzs > 0:
            # find peaks
            pkmzs, pkhts, pkwts = find_peaks_1d_localmax(mz_bins, i_bins,
                                                         params.min_rel_height, params.min_abs_height, 
                                                         params.fwhm_min, params.fwhm_max, 
                                                         params.peak_min_dist)
            if len(pkmzs) > 0:
                ms2_str: str = ms2_to_str(pkmzs, pkhts)
                qdata.append((None, rdr.f, fmz, frt, fwt, fht, fsnr, n_scan_pre_mzs, len(pkmzs), ms2_str))
            else:
                qdata.append((None, rdr.f, fmz, frt, fwt, fht, fsnr, n_scan_pre_mzs, 0, None))
            debug_handler(debug_flag, debug_cb, msg + "-> # MS2 peaks: {}".format(len(pkmzs)), pid)
        else:
            qdata.append((None, rdr.f, fmz, frt, fwt, fht, fsnr, n_scan_pre_mzs, None, None))
            debug_handler(debug_flag, debug_cb, msg, pid)
    debug_handler(debug_flag, debug_cb, 'EXTRACTING AND FITTING MS2 SPECTRA: elapsed: {:.1f} s'.format(time() - t0), pid)
    return qdata


def _add_features_to_db(cur: ResultsDbCursor, 
                        qdata: List[DdaFeature], 
                        debug_flag: Optional[str], debug_cb: Optional[Callable]
                        ) -> None:
    """
    adds features and metadata into the DDA ids database. 

    Parameters
    ----------
    cur : ``sqlite3.Cursor``
        cursor for making queries into the lipid ids database
    qdata : ``list(tuple(...))``
        list of query data for all of the features
    debug_flag : ``str``
        specifies how to dispatch debugging messages, None to do nothing
    debug_cb : ``func``
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'
    """
    pid = os.getpid()
    debug_handler(debug_flag, debug_cb, 'ADDING DDA FEATURES TO DATABASE', pid)
    qry = 'INSERT INTO DDAFeatures VALUES (?,?,?,?,?,?,?,?,?,?);'
    for qd in qdata:
        cur.execute(qry, qd)


def extract_dda_features(dda_data_file: MzaFilePath, 
                         results_db: ResultsDbPath, 
                         params: DdaParams, 
                         cache_ms1: bool = True, 
                         debug_flag: Optional[str] = None, debug_cb: Optional[Callable] = None, 
                         drop_scans: Optional[List[int]] = None
                         ) -> int :
    """
    Extract features from a raw DDA data file, store them in a database (initialized using ``create_dda_ids_db`` function)

    Parameters
    ----------
    dda_data_file : ``str``
        path to raw DDA data file (MZA format)
    results_db : ``str``
        path to DDA-DIA analysis results database
    params : ``DdaParams``
        DDA data analysis parameters dict
    cache_ms1 : ``bool``, default=True
        Cache MS1 scan data to reduce disk access. This significantly speeds up extracting the 
        precursor chromatograms, but comes at the cost of very high memory usage. Should work 
        fine with a single process on most machines with 16 GB RAM (in testing the memory 
        footprint of this data is like 10-15 GB) but using multiple processes will quickly use 
        up all of the RAM and start swapping which completely negates the performance gains from 
        caching. Machines with more RAM can support more processes doing this caching at the same
        time, and rule of thumb would be 1 process per 16 GB RAM. 
    debug_flag : ``str``, optional
        specifies how to dispatch debugging messages, None to do nothing
    debug_cb : ``func``, optional
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'

    Returns
    -------
    n_dda_features : ``int``
        number of DDA features extracted
    """
    pid: int = os.getpid()
    debug_handler(debug_flag, debug_cb, 'EXTRACTING DDA FEATURES', pid)
    debug_handler(debug_flag, debug_cb, 'file: {}'.format(dda_data_file), pid)
    # initialize the MSMS reader
    rdr: DdaReader = (
        MsmsReaderDdaCachedMs1(dda_data_file, drop_scans=drop_scans) 
        if cache_ms1 
        else MsmsReaderDda(dda_data_file, drop_scans=drop_scans)
    )
    # get the list of precursor m/zs
    pre_mzs: Set[float] = rdr.get_pre_mzs()[4000:4020]  # TODO: TEMPORARY SLICE, REMOVE ME!
    debug_handler(debug_flag, debug_cb, '# precursor m/zs: {}'.format(len(pre_mzs)), pid)
    # extract chromatographic features
    chrom_feats: List[DdaChromFeat] = _extract_and_fit_chroms(rdr, 
                                                              pre_mzs, 
                                                              params.extract_and_fit_chrom_params,
                                                              debug_flag, debug_cb)
    # consolidate chromatographic features
    chrom_feats_consolidated: List[DdaChromFeat] = _consolidate_chrom_feats(chrom_feats, 
                                                                            params.consolidate_chrom_feats_params, 
                                                                            debug_flag, debug_cb)
    # extract MS2 spectra
    qdata: List[DdaFeature] = _extract_and_fit_ms2_spectra(rdr, 
                                                           chrom_feats_consolidated, 
                                                           params.extract_and_fit_ms2_spectra_params, 
                                                           debug_flag, debug_cb)
    # do not need the reader anymore
    rdr.close()
    # initialize connection to DDA ids database
    con: ResultsDbConnection = sqlite3.connect(results_db, timeout=60)  # increase timeout to avoid errors from database locked by another process
    cur: ResultsDbCursor = con.cursor()
    # add features to database
    _add_features_to_db(cur, qdata, debug_flag, debug_cb)
    # close database connection
    con.commit()
    con.close()
    # return the number of features extracted
    return len(qdata)
    

def extract_dda_features_multiproc(dda_data_files: List[MzaFilePath], 
                                   results_db: ResultsDbPath, 
                                   params: DdaParams, 
                                   n_proc: int,
                                   cache_ms1: bool = False, 
                                   debug_flag: Optional[str] = None, debug_cb: Optional[Callable] = None
                                   ) -> Dict[str, int] :
    """
    extracts dda features from multiple DDA files in parallel

    Parameters
    ----------
    dda_data_files : ``list(str)``
        paths to raw DDA data file (MZA format)
    results_db : ``str``
        path to DDA-DIA analysis results database
    params : ``dict(...)``
        parameters for the various steps of DDA feature extraction
    n_proc : ``int``
        number of CPU threads to use (number of processes)
    cache_ms1 : ``bool``, default=False
        Cache MS1 scan data to reduce disk access. This should be turned off when using 
        multiprocessing on most machines. See entry in ``extract_dda_features`` 
        docstring for a more detailed explanation.
    debug_flag : ``str``, optional
        specifies how to dispatch debugging messages, None to do nothing
    debug_cb : ``func``, optional
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'

    Returns
    -------
    dda_features_per_file : ``dict(str:int)``
        dictionary with the number of DDA features mapped to input DDA data files
    """
    n_proc = min(n_proc, len(dda_data_files))  # no need to use more processes than the number of inputs
    args = [(dda_data_file, results_db, params) for dda_data_file in dda_data_files]
    args_for_starmap = zip(repeat(extract_dda_features), args, repeat({'cache_ms1': cache_ms1, 
                                                                       'debug_flag': debug_flag, 
                                                                       'debug_cb': debug_cb}))
    with multiprocessing.Pool(processes=n_proc) as p:
        feat_counts = p.starmap(apply_args_and_kwargs, args_for_starmap)
    return {k: v for k, v in zip(dda_data_files, feat_counts)}


def consolidate_dda_features(results_db: ResultsDbPath, 
                             params: DdaConsolidateChromFeatsParams, 
                             debug_flag: Optional[str] = None, debug_cb: Optional[Callable] = None
                             ) -> Tuple[int, int] :
    """
    consolidates DDA features from lipid IDs database based on feature m/z and RT using the following criteria:

    * for groups of features having very similar m/z and RT, if none have MS2 scans then only the feature with 
      the highest intensity in each group is kept
    * if at least one feature in a group has MS2 scans, then features in that group that do not have MS2 scans 
      are dropped
    * TODO (Dylan Ross) if more than one feature in a group has MS2 scans, then merge those MS2 scans and merge 
      the features, see comment below for details

    Parameters
    ----------
    results_db : ``str``
        path to DDA-DIA analysis results database
    params : ``DdaConsolidateChromFeatsParams``
        DDA data analysis parameters 
    debug_flag : ``str``, optional
        specifies how to dispatch debugging messages, None to do nothing
    debug_cb : ``func``, optional
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'
    
    Returns
    -------
    n_features_pre : ``int``
    n_features_post : ``int``
        return the number of features before and after consolidating
    """
    # no need to get the PID, this should only ever be run in the main process
    # connect to the database
    con: ResultsDbConnection = sqlite3.connect(results_db)
    cur: ResultsDbCursor = con.cursor()
    # step 1, create groups of features based on similar m/z and RT
    qry_sel = "SELECT dda_feat_id, mz, rt, rt_pkht, ms2_n_scans FROM DDAFeatures"
    grouped: List[List[Any]] = []
    n_dda_features: int = 0
    for d in cur.execute(qry_sel).fetchall():
        n_dda_features += 1
        _, mz, rt, *_ = d
        add = True
        mzt = tol_from_ppm(mz, params.mz_ppm)
        for i in range(len(grouped)):
            for _, mz_i, rt_i, *_ in grouped[i]:
                if abs(mz - mz_i) <= mzt and abs(rt - rt_i) <= params.rt_tol:
                    grouped[i].append(d)
                    add = False
                    break
            if not add:
                break
        if add:
            grouped.append([d])
    # step 2, determine which features to drop
    drop_fids: List[int] = []
    for group in grouped:
        if len(group) > 1:
            # only consider groups with multiple features in them
            if sum([_[4] for _ in group]) > 0:
                # at least one feature has MSMS
                for feat in group:
                    if feat[4] < 1:
                        # drop any features in the group that do not have MSMS
                        drop_fids.append(feat[0])
                        # TODO (Dylan Ross): There is a potential here for redundant features that have 
                        #                    MSMS spectra because all such features in a group are kept. 
                        #                    I do want to change this, but since the main thing that this
                        #                    function does is drop rows from the database, it will take 
                        #                    additional logic to properly merge the spectra together and
                        #                    update the database accordingly. Also, with this change this
                        #                    first conditional checking for features that contain spectra
                        #                    would become unnecessary and everything could be handled in 
                        #                    the else branch below
            else:
                # none of the features have MSMS
                # only keep the feature with the highest intensity of the group
                # or exclude entirely if params.consolidate_dda_features_params.drop_if_no_ms2 is set
                max_fint: float = 0.
                keep_ffid: Optional[int] = None
                for feat in group:
                    ffid, fint = feat[0], feat[3]
                    if not params.drop_if_no_ms2:
                        if keep_ffid is None:
                            max_fint = fint
                            keep_ffid = ffid
                        elif fint > max_fint:
                            # replace the current max intensity feature of the group
                            drop_fids.append(keep_ffid)
                            max_fint = fint
                            keep_ffid = ffid
                        else:
                            # drop this feature if it wasn't kept
                            drop_fids.append(ffid)
                    else:
                        # drop all of these features if we are not keeping features that lack MS2 scans
                        drop_fids.append(ffid)
    n_post: int = n_dda_features - len(drop_fids)                        
    debug_handler(debug_flag, debug_cb, f"CONSOLIDATING DDA FEATURES: {n_dda_features} features -> {n_post} features")
    # step 3, drop features from database
    qry_drop = "DELETE FROM DDAFeatures WHERE dda_feat_id=?"
    for fid in drop_fids:
        cur.execute(qry_drop, (fid,))
    # commit changes to the database
    con.commit()
    con.close()
    # return the count of features pre/post consolidating
    return n_dda_features, n_post

    