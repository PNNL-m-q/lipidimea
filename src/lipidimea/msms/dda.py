"""
lipidimea/msms/dda.py

Dylan Ross (dylan.ross@pnnl.gov)

    module with DDA MSMS utilities

"""


from typing import List, Any, Set, Callable, Optional, Dict, Tuple, Union
import sqlite3
from time import time
from itertools import repeat
import multiprocessing
import os
import errno

import numpy as np
from mzapy.dda import MsmsReaderDda, MsmsReaderDdaCachedMs1
from mzapy.peaks import find_peaks_1d_gauss, find_peaks_1d_localmax, calc_gauss_psnr

from lipidimea.typing import (
    ResultsDbConnection, ResultsDbCursor, ResultsDbPath, DdaReader, DdaChromFeat, DdaPrecursor,
    MzaFilePath, MzaFileId, Ms2
)
from lipidimea.msms._util import (
    apply_args_and_kwargs, ppm_from_delta_mz, tol_from_ppm
)
from lipidimea.util import (
    add_data_file_to_db, debug_handler, AnalysisStep, update_analysis_log, check_analysis_log
)
from lipidimea.params import (
    DdaParams
)


def _extract_and_fit_chroms(rdr: DdaReader, 
                            pre_mzs: Set[float], 
                            params: DdaParams,
                            debug_flag: Optional[str], debug_cb: Optional[Callable] 
                            ) -> List[DdaChromFeat] :
    """
    extracts and fits chromatograms for a list of precursor m/zs 

    Parameters
    ----------
    rdr
        object for accessing DDA MSMS data from MZA
    pre_mzs
        sorted unique precursor m/zs
    params
        parameters for data extraction and fitting
    [debug_flag]
        specifies how to dispatch debugging messages, None to do nothing
    [debug_cb]
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'

    Returns
    -------
    chrom_feats
        list of chromatographic features (pre_mz, peak RT, peak height, peak FWHM, pSNR)
    """
    # unpack params
    P = params.extract_and_fit_chroms
    pid = os.getpid()
    # extract chromatograms
    debug_handler(debug_flag, debug_cb, 'EXTRACTING AND FITTING CHROMATOGRAMS', pid)
    chrom_feats: List[DdaChromFeat] = []
    t0 = time()
    n: int = len(pre_mzs)
    for i, pre_mz in enumerate(pre_mzs): 
        msg = f"({i + 1}/{n}) precursor m/z: {pre_mz:.4f} -> "
        # extract chromatogram
        assert P.mz_ppm is not None
        chrom = rdr.get_chrom(pre_mz, tol_from_ppm(pre_mz, P.mz_ppm))
        # try fitting chromatogram (up to n peaks)
        _pkrts, _pkhts, _pkwts = find_peaks_1d_gauss(*chrom, 
                                                     P.min_rel_height, P.min_abs_height,  # type: ignore
                                                     P.fwhm.min, P.fwhm.max,              # type: ignore
                                                     P.max_peaks, True)                   # type: ignore
        # calc pSNR for each fitted peak, make sure they meet a threshold
        pkrts, pkhts, pkwts, psnrs = [], [], [], []
        for pkparams in zip(_pkrts, _pkhts, _pkwts):
            psnr = calc_gauss_psnr(*chrom, pkparams) # type: ignore
            if psnr > P.min_psnr:
                pkrts.append(pkparams[0])
                pkhts.append(pkparams[1])
                pkwts.append(pkparams[2])
                psnrs.append(psnr)
        if len(pkrts) > 0:
            for r, h, w, s in zip(pkrts, pkhts, pkwts, psnrs):
                pkinfo = f"RT: {r:.2f} +/- {w:.2f} min ({h:.1e}, {s:.1f}) "
                debug_handler(debug_flag, debug_cb, msg + pkinfo, pid)
                chrom_feats.append((pre_mz, r, h, w, s))
        else: 
            debug_handler(debug_flag, debug_cb, msg + 'no peaks found', pid)
    debug_handler(debug_flag, debug_cb, f"EXTRACTING AND FITTING CHROMATOGRAMS: elapsed: {time() - t0:.1f} s", pid)
    return chrom_feats


def _consolidate_chrom_feats(chrom_feats: List[DdaChromFeat], 
                             params: DdaParams, 
                             debug_flag: Optional[str], debug_cb: Optional[Callable] 
                             ) -> List[DdaChromFeat] :
    """
    consolidate chromatographic features that have very similar m/z and RT
    only keep highest intensity features

    Parameters
    ----------
    chrom_feats
        list of chromatographic features (pre_mz, peak RT, peak FWHM, peak height, pSNR)
    params
        parameters for consolidating chromatographic features
    [debug_flag]
        specifies how to dispatch debugging messages, None to do nothing
    [debug_cb]
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'

    Returns
    -------
    chrom_feats_consolidated
        list of consolidated chromatographic features (pre_mz, peak RT, peak FWHM, peak height, pSNR)
    """
    # unpack params
    P = params.consolidate_chrom_feats
    pid = os.getpid()
    # consolidate features
    chrom_feats_consolidated: List[DdaChromFeat] = []
    for feat in chrom_feats:
        add: bool = True
        for i in range(len(chrom_feats_consolidated)):
            fc_i: DdaChromFeat = chrom_feats_consolidated[i]
            delta_mz: float = abs(feat[0] - fc_i[0])
            if ppm_from_delta_mz(delta_mz, fc_i[0]) <= P.mz_ppm and abs(feat[1] - fc_i[1]) <= P.rt_tol:
                add = False
                if feat[2] > fc_i[2]:
                    chrom_feats_consolidated[i] = feat
        if add:
            chrom_feats_consolidated.append(feat)
    msg = (
        f"CONSOLIDATING CHROMATOGRAPHIC FEATURES: {len(chrom_feats)} features "
        f"-> {len(chrom_feats_consolidated)} features"
    )
    debug_handler(debug_flag, debug_cb, msg, pid)
    return chrom_feats_consolidated


def _extract_and_fit_ms2_spectra(rdr: DdaReader,
                                 dda_file_id: MzaFileId,
                                 chrom_feats_consolidated: List[DdaChromFeat],
                                 params: DdaParams,
                                 debug_flag: Optional[str], debug_cb: Optional[Callable] 
                                 ) -> Tuple[List[DdaPrecursor], List[Optional[Ms2]]] :
    """
    extracts MS2 spectra for consolidated chromatographic features, tries to fit spectra peaks,
    returns query data for adding features to database

    Parameters
    ----------
    rdr
        object for accessing DDA MSMS data from MZA
    dda_file_id
        file ID for DDA data file
    chrom_feats_consolidated
        list of consolidated chromatographic features (pre_mz, peak RT, peak FWHM, peak height, pSNR)
    params
        parameters for mass spectum extraction and fitting
    [debug_flag]
        specifies how to dispatch debugging messages, None to do nothing
    [debug_cb]
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'

    Returns
    -------
    precursors
        list of precursor info (as tuple) for each precursor
            [None, int, float, float, float, float, float, int, Optional[int]]
    spectra
        list of tandem mass spectra (centroided, as 2D arrays) or None if no MS2 peaks were found
    """
    # unpack params
    P = params.extract_and_fit_ms2_spectra
    pid: int = os.getpid()
    # extract and fit MS2 spectra, return query data
    debug_handler(debug_flag, 
                  debug_cb, 
                  'EXTRACTING AND FITTING MS2 SPECTRA', 
                  pid)
    t0 = time()
    precursors: List[DdaPrecursor] = []
    spectra: List[Optional[Ms2]] = []
    n: int = len(chrom_feats_consolidated)
    for i, (fmz, frt, fht, fwt, fsnr) in enumerate(chrom_feats_consolidated):
        msg: str = f"({i + 1}/{n}) m/z: {fmz:.4f} RT: {frt:.2f} +/- {fwt:.2f} min ({fht:.1e}, {fsnr:.1f}) -> "
        # RT range is peak RT +/- peak FWHM
        rt_min: float = frt - fwt  
        rt_max: float = frt + fwt  
        mz_bin_max: float = fmz + 5  # only extract MS2 spectrum up to precursor m/z + 5 Da
        # (try to) extract MS2 spectrum
        assert P.pre_mz_ppm is not None
        ms2 = rdr.get_msms_spectrum(fmz, 
                                    tol_from_ppm(fmz, P.pre_mz_ppm), 
                                    rt_min, 
                                    rt_max, 
                                    P.mz_bin_min, 
                                    mz_bin_max, 
                                    P.mz_bin_size)
        mz_bins, i_bins, n_scan_pre_mzs, scan_pre_mzs = ms2
        msg += f"# MS2 scans: {n_scan_pre_mzs}"
        if n_scan_pre_mzs > 0:
            # find peaks
            pkmzs, pkhts, pkwts = find_peaks_1d_localmax(mz_bins, i_bins,
                                                         P.min_rel_height, P.min_abs_height, 
                                                         P.fwhm.min, P.fwhm.max, 
                                                         P.peak_min_dist)
            if len(pkmzs) > 0:
                precursors.append((None, dda_file_id, fmz, frt, fwt, fht, fsnr, n_scan_pre_mzs, len(pkmzs)))
                spectra.append(np.array([pkmzs, pkhts]))  # type: ignore
            else:
                precursors.append((None, dda_file_id, fmz, frt, fwt, fht, fsnr, n_scan_pre_mzs, 0))
                spectra.append(None)
            debug_handler(debug_flag, 
                          debug_cb, 
                          msg + f"-> # MS2 peaks: {len(pkmzs)}", 
                          pid)
        else:
            precursors.append((None, dda_file_id, fmz, frt, fwt, fht, fsnr, n_scan_pre_mzs, None))
            spectra.append(None)
            debug_handler(debug_flag, 
                          debug_cb, 
                          msg, 
                          pid)
    debug_handler(debug_flag, 
                  debug_cb, 
                  f"EXTRACTING AND FITTING MS2 SPECTRA: elapsed: {time() - t0:.1f} s", 
                  pid)
    return precursors, spectra


def _add_precursors_and_fragments_to_db(cur: ResultsDbCursor, 
                                        precursors: List[DdaPrecursor], 
                                        spectra: List[Optional[Ms2]],
                                        debug_flag: Optional[str], debug_cb: Optional[Callable]
                                        ) -> None:
    """
    adds features and metadata into the DDA ids database. 

    Parameters
    ----------
    cur
        cursor for making queries into the lipid ids database
    precursors
        list of query data for all of the precursors
    spectra
        list of MS/MS spectra (if found) for each precursor
    [debug_flag]
        specifies how to dispatch debugging messages, None to do nothing
    [debug_cb]
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'
    """
    pid = os.getpid()
    debug_handler(debug_flag, debug_cb, f'ADDING {len(precursors)} DDA FEATURES TO DATABASE', pid)
    qry_pre = """--beginsql
        INSERT INTO DDAPrecursors VALUES (?,?,?,?,?,?,?,?,?)
    --endsql"""
    qry_frag = """--beginsql
        INSERT INTO DDAFragments VALUES (?,?,?,?)
    --endsql"""
    for pre, spec in zip(precursors, spectra):
        cur.execute(qry_pre, pre)
        pre_id = cur.lastrowid
        if spec is not None:
            for msms_mz, msms_i in spec.T:  # type: ignore
                cur.execute(qry_frag, (None, pre_id, msms_mz, msms_i))


def extract_dda_features(dda_data_file: Union[MzaFilePath, MzaFileId], 
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
    dda_data_file
        path to raw DDA data file (MZA format) OR a file ID from the results database if analyzing 
        a file that has already been added into the database
    results_db
        path to DDA-DIA analysis results database
    params
        DDA data analysis parameters dict
    [cache_ms1]
        Cache MS1 scan data to reduce disk access. This significantly speeds up extracting the 
        precursor chromatograms, but comes at the cost of very high memory usage. Should work 
        fine with a single process on most machines with 16 GB RAM (in testing the memory 
        footprint of this data is like 10-15 GB) but using multiple processes will quickly use 
        up all of the RAM and start swapping which completely negates the performance gains from 
        caching. Machines with more RAM can support more processes doing this caching at the same
        time, and rule of thumb would be 1 process per 16 GB RAM. 
    [debug_flag]
        specifies how to dispatch debugging messages, None to do nothing
    [debug_cb]
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'

    Returns
    -------
    n_dda_features
        number of DDA features extracted
    """
    # ensure the results database exists
    if not os.path.isfile(results_db):
        raise FileNotFoundError(errno.ENOENT, 
                                os.strerror(errno.ENOENT), 
                                results_db)
    pid: int = os.getpid()
    debug_handler(debug_flag, debug_cb, 'EXTRACTING DDA FEATURES', pid)
    debug_handler(debug_flag, debug_cb, f"file: {dda_data_file}", pid)
    # check if the dda_data_file is a path (str) or file ID from the results database (int)
    match dda_data_file:
        case int():
            dda_file_id: int = dda_data_file
        case str():
            # initialize a connection to results database
            # increase timeout to avoid errors from database locked by another process
            con: ResultsDbConnection = sqlite3.connect(results_db, timeout=60)  
            cur: ResultsDbCursor = con.cursor()
            # add the MZA data file to the database and get a file identifier for it
            dda_file_id: int = add_data_file_to_db(cur, "LC-MS/MS (DDA)", dda_data_file)
            # close database connection
            con.commit()
            con.close()
            # NOTE: A database connection gets opened here briefly then closed right afterwards and this gets
            #       repeated later on to add the extracted features. The reason for doing it this way rather 
            #       than just opening a connection once and leaving it open until we are done with it is that
            #       the process of feature extraction takes a really long time and it seems pretty unnecessary 
            #       to sit with an open database connection that will not be used for a long time. This is 
            #       also important because this function might be running on multiple processes at one time
            #       so might as well keep the database as free as possible when access is not needed. 
        case _:
            msg = f"extract_dda_features: invalid type for dda_data_file ({type(dda_data_file)})"
            raise ValueError(msg)
    # initialize the MSMS reader
    rdr: DdaReader = (
        MsmsReaderDdaCachedMs1(dda_data_file, drop_scans=drop_scans) 
        if cache_ms1 
        else MsmsReaderDda(dda_data_file, drop_scans=drop_scans)
    )
    # get the list of precursor m/zs
    pre_mzs: Set[float] = rdr.get_pre_mzs()  # type: ignore
    # limit to a specified range 
    pre_mzs = set([_ for _ in pre_mzs if (_ >= params.precursor.precursor_mz.min and _ <= params.precursor.precursor_mz.max)])
    debug_handler(debug_flag, debug_cb, f"# precursor m/zs: {len(pre_mzs)}")
    # extract chromatographic features
    chrom_feats: List[DdaChromFeat] = _extract_and_fit_chroms(rdr, 
                                                              pre_mzs, 
                                                              params,
                                                              debug_flag, debug_cb)
    # consolidate chromatographic features
    chrom_feats_consolidated: List[DdaChromFeat] = _consolidate_chrom_feats(chrom_feats, 
                                                                            params, 
                                                                            debug_flag, debug_cb)
    # extract MS2 spectra
    precursors, spectra = _extract_and_fit_ms2_spectra(rdr, 
                                                       dda_file_id,
                                                       chrom_feats_consolidated, 
                                                       params, 
                                                       debug_flag, debug_cb)
    precursors: List[DdaPrecursor]
    n_precursors = len(precursors)
    spectra: List[Optional[Ms2]]
    # do not need the reader anymore
    rdr.close()
    # initialize connection to DDA ids database
    # increase timeout to avoid errors from database locked by another process
    con: ResultsDbConnection = sqlite3.connect(results_db, timeout=60)  
    cur: ResultsDbCursor = con.cursor()
    # add precursors and MS/MS spectra to database
    _add_precursors_and_fragments_to_db(cur, precursors, spectra, debug_flag, debug_cb)
    # update the analysis log
    update_analysis_log(
        cur, 
        AnalysisStep.DDA_EXT,
        {
            "DDA file ID": dda_file_id,
            "precursors": n_precursors
        }
    )
    # close database connection
    con.commit()
    con.close()
    # return the number of features extracted
    return n_precursors
    

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
    dda_data_files
        paths to raw DDA data file (MZA format)
    results_db
        path to DDA-DIA analysis results database
    params
        parameters for the various steps of DDA feature extraction
    n_proc
        number of CPU threads to use (number of processes)
    [cache_ms1]
        Cache MS1 scan data to reduce disk access. This should be turned off when using 
        multiprocessing on most machines. See entry in ``extract_dda_features`` 
        docstring for a more detailed explanation.
    [debug_flag]
        specifies how to dispatch debugging messages, None to do nothing
    [debug_cb]
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'

    Returns
    -------
    dda_features_per_file
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
                             params: DdaParams, 
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
    results_db
        path to DDA-DIA analysis results database
    params
        DDA data analysis parameters 
    [debug_flag]
        specifies how to dispatch debugging messages, None to do nothing
    [debug_cb]
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'
    
    Returns
    -------
    n_features_pre
    n_features_post
        return the number of features before and after consolidating
    """
    # unpack parameters
    P = params.consolidate_dda_feats
    # ensure the results database exists
    if not os.path.isfile(results_db):    
        raise FileNotFoundError(errno.ENOENT, 
                                os.strerror(errno.ENOENT), 
                                results_db)
    # no need to get the PID, this should only ever be run in the main process
    # connect to the database
    con: ResultsDbConnection = sqlite3.connect(results_db)
    cur: ResultsDbCursor = con.cursor()
    # check that DDA feature extraction has been completed first
    check_analysis_log(cur, AnalysisStep.DDA_EXT)
    # step 1, create groups of features based on similar m/z and RT
    qry_sel = """--beginsql
        SELECT dda_pre_id, mz, rt, rt_pkht, ms2_n_scans FROM DDAPrecursors
    --endsql"""
    grouped: List[List[Any]] = []
    n_dda_features: int = 0
    for d in cur.execute(qry_sel).fetchall():
        n_dda_features += 1
        _, mz, rt, *_ = d
        add = True
        mzt = tol_from_ppm(mz, P.mz_ppm)
        for i in range(len(grouped)):
            for _, mz_i, rt_i, *_ in grouped[i]:
                if abs(mz - mz_i) <= mzt and abs(rt - rt_i) <= P.rt_tol:
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
                        # TODO (Dylan Ross): P.S. This is not a problem with the current implementation
                        #                    because all precursors with MS2 spectra are retained, but if 
                        #                    the above change is made, then there will need to be some logic
                        #                    for dealing with entries in DDAFragments that no longer point
                        #                    to an entry in DDAPrecursors after some DDA precursors are 
                        #                    dropped or merged.
            else:
                # none of the features have MSMS
                # only keep the feature with the highest intensity of the group
                # or exclude entirely if params.consolidate_dda_features_params.drop_if_no_ms2 is set
                max_fint: float = 0.
                keep_ffid: Optional[int] = None
                for feat in group:
                    ffid, fint = feat[0], feat[3]
                    if not P.drop_if_no_ms2:
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
    qry_drop = """--beginsql
        DELETE FROM DDAPrecursors WHERE dda_pre_id=?
    --endsql"""
    for fid in drop_fids:
        cur.execute(qry_drop, (fid,))
    # update the analysis log
    update_analysis_log(
        cur, 
        AnalysisStep.DDA_CONS,
        {
            "DDA precursors before": n_dda_features,
            "DDA precursors after": n_post
        }
    )
    # commit changes to the database
    con.commit()
    con.close()
    # return the count of features pre/post consolidating
    return n_dda_features, n_post

    
# TODO (Dylan Ross): Add a function that goes through the DDA precursors and drops the ones in the 
#                    top/bottom X% in terms of the peak FWHMs. The precursor features that have very
#                    large or very small FWHMs are probably not good features and getting rid of them
#                    early will lead to less noisy features being included in downstream analyses.


