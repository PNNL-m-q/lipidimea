"""
LipidIMEA/msms/dda.py

Dylan Ross (dylan.ross@pnnl.gov)

    module with DDA MSMS utilities

"""


from sqlite3 import connect
from time import time, sleep
from itertools import repeat
import multiprocessing
import os

import h5py
import hdf5plugin
import numpy as np
import pandas as pd
from mzapy.peaks import find_peaks_1d_gauss, find_peaks_1d_localmax, calc_gauss_psnr

from LipidIMEA.msms._util import ms2_to_str, apply_args_and_kwargs
from LipidIMEA.util import debug_handler


class _MSMSReaderDDA():
    """
    object for accessing DDA MSMS data from MZA (HDF5) formatted files

    The MZA files created from qTOF DDA data have some peculiarities so a
    small, purpose-built reader is better than shoehorning the main MZA object for
    this purpose

    Attributes
    ----------
    h5 : ``h5py.File``
        interface to MZA file (HDF5)
    f : ``str``
        path to MZA file
    metadata : ``pandas.DataFrame``
        metadata dataframe
    arrays_mz : ``pandas.DataFrame``
        m/z dataframe
    arrays_i : ``pandas.DataFrame``
        intensity dataframe
    ms1_scans : ``numpy.ndarray(int)``
        array of MS1 scans
    min_rt, max_rt : ``float``
        minimum/maximum retention time
    """

    def __init__(self, mza_file):
        """
        initialize the reader
    
        Parameters
        ----------
        mza_file : ``str``
            path to MZA file
        """
        self.h5 = h5py.File(mza_file, 'r')
        self.f = mza_file
        self.metadata = pd.DataFrame(self.h5['Metadata'][:]).set_index('Scan')
        self.arrays_mz = pd.DataFrame(self.h5['Arrays_mz'].items(), columns=['Scan', 'Data']).set_index('Scan')
        self.arrays_mz.index = self.arrays_mz.index.astype('int64')
        self.arrays_i = pd.DataFrame(self.h5['Arrays_intensity'].items(), columns=['Scan', 'Data']).set_index('Scan')
        self.arrays_i.index = self.arrays_i.index.astype('int64')
        self.ms1_scans = self.metadata[self.metadata['PrecursorScan'] == 0].index.to_numpy()
        self.ms2_scans = self.metadata[self.metadata['PrecursorScan'] != 0].index.to_numpy()
        rt = self.metadata[self.metadata['PrecursorScan'] == 0].loc[:, 'RetentionTime'].to_numpy()
        self.min_rt, self.max_rt = min(rt), max(rt)
    
    def close(self):
        """
        close connection to the MZA file
        """
        self.h5.close()
        
    def get_chrom(self, mz, mz_tol):
        """
        Select a chromatogram (MS1 only) for a target m/z with specified tolerance

        Parameters
        ----------
        mz : ``float``
            target m/z
        mz_tol : ``float``
            m/z tolerance

        Returns
        -------
        chrom_rts : ``np.ndarray(float)``
        chrom_ins : ``np.ndarray(float)``
            chromatogram retention time and intensity components 
        """
        rts, ins = [], []
        mz_min, mz_max = mz - mz_tol, mz + mz_tol
        for scan, rt in zip(self.ms1_scans, self.metadata.loc[self.ms1_scans, 'RetentionTime']):
            smz, sin = np.array([self.arrays_mz.loc[scan, 'Data'], self.arrays_i.loc[scan, 'Data']])
            rts.append(rt)
            ins.append(np.sum(sin[(smz >= mz_min) & (smz <= mz_max)]))
        return np.array([rts, ins])

    def get_msms_spectrum(self, mz, mz_tol, rt_min, rt_max, mz_bin_min, mz_bin_max, mz_bin_size):
        """
        Selects all MS2 scans with precursor m/z within tolerance of a target value and retention time 
        between specified bounds, sums spectra together returning the accumulated spectrum and some 
        metadata about how many scans were included and what precursor m/zs were included
        
        Parameters
        ----------
        mz : ``float``
            target m/z for precursor
        mz_tol : ``float``
            m/z tolerance for precursor
        rt_min : ``float``
            minimum RT for precursor
        rt_max : ``float``
            maximum RT for precursor
        mz_bin_min : ``float``
            minimum m/z for m/z binning
        mz_bin_max : ``float``
            maximum m/z for m/z binning
        mz_bin_size : ``float``
            size of bins for m/z binning
            
        Returns
        -------
        ms2_mz, ms2_i : ``np.ndarray(float)``
            mass spectrum
        n_ms2_scans : ``int``
            number of ms2 scans in spectrum
        scan_pre_mzs : ``list(float)``
            list of precursor m/zs for selected MS/MS spectrum
        """
        mz_min, mz_max = mz - mz_tol, mz + mz_tol
        # get peak precursor scans
        peak_pre_scans = self.metadata[(self.metadata['PrecursorScan'] == 0) & (self.metadata['RetentionTime'] >= rt_min) & (self.metadata['RetentionTime'] <= rt_max)].index.to_numpy()
        # get peak fragmentation scans
        peak_frag_scans = self.metadata[np.isin(self.metadata['PrecursorScan'], peak_pre_scans) & (self.metadata['PrecursorMonoisotopicMz'] >= mz_min) & (self.metadata['PrecursorMonoisotopicMz'] <= mz_max)].index.to_numpy()
        # precursor m/zs and count of MS2 scans
        scan_pre_mzs = self.metadata.loc[peak_frag_scans, 'PrecursorMonoisotopicMz'].tolist()
        # m/z binning parameters
        mz_bin_range = mz_bin_max - mz_bin_min
        n_bins = int((mz_bin_max - mz_bin_min) / mz_bin_size) + 1
        mz_bins = np.linspace(mz_bin_min, mz_bin_max, n_bins)
        i_bins = np.zeros(mz_bins.shape)
        mz_to_bin_idx = lambda mz: int(round((mz - mz_bin_min) / mz_bin_range * n_bins, 0))
        # accumulate MS2 scans together
        for scan in peak_frag_scans:
            for m, i in zip(self.arrays_mz.loc[scan, 'Data'], self.arrays_i.loc[scan, 'Data']):
                idx = mz_to_bin_idx(m)
                if idx >= 0 and idx < n_bins:
                    i_bins[idx] += i
        # return accumulated spectrum
        return mz_bins, i_bins, len(scan_pre_mzs), scan_pre_mzs

    def get_tic(self):
        """
        TIC

        Returns
        -------
        tic_rts : ``np.ndarray(float)``
        tic_ins : ``np.ndarray(float)``
            TIC retention time and intensity components 
        """
        tic_x = self.metadata[self.metadata['PrecursorScan'] == 0].loc[:, 'RetentionTime'].to_numpy()
        tic_y = self.metadata[self.metadata['PrecursorScan'] == 0].loc[:, 'TIC'].to_numpy()
        return tic_x, tic_y

    def get_pre_mzs(self):
        """
        returns the set of unique m/z values for all MS/MS scan precursors in this file

        Returns
        -------
        pre_mzs : ``set(float)``
            sorted unique precursor m/zs
        """
        return sorted(set(self.metadata.loc[self.ms2_scans, 'PrecursorMonoisotopicMz'].tolist()))


class _MSMSReaderDDA_Cached(_MSMSReaderDDA):
    """
    _MSMSReaderDDA with all arrays_mz and arrays_i data pre-read into memory to reduce 
    disk access, applicable primarily to extracting chromatograms (MS1) since that takes 
    much longer than MS2 spectra

    This takes up too much memory when there are multiple processes...
    """

    def __init__(self, mza_file):
        """
        initialize the reader
    
        Parameters
        ----------
        mza_file : ``str``
            path to MZA file
        """
        super().__init__(mza_file)
        self.arrays_mz_cached = {}
        self.arrays_i_cached = {}
        for scan in self.ms1_scans:
            scan_mz = self.arrays_mz.loc[scan, 'Data']
            scan_i = self.arrays_i.loc[scan, 'Data']
            a_mz, a_i = np.zeros(shape=(2, scan_mz.size))
            scan_mz.read_direct(a_mz)
            scan_i.read_direct(a_i)
            self.arrays_mz_cached[scan] = a_mz
            self.arrays_i_cached[scan] = a_i

    def get_chrom(self, mz, mz_tol):
        """
        Select a chromatogram (MS1 only) for a target m/z with specified tolerance

        Parameters
        ----------
        mz : ``float``
            target m/z
        mz_tol : ``float``
            m/z tolerance

        Returns
        -------
        chrom_rts : ``np.ndarray(float)``
        chrom_ins : ``np.ndarray(float)``
            chromatogram retention time and intensity components 
        """
        rts, ins = [], []
        mz_min, mz_max = mz - mz_tol, mz + mz_tol
        for scan, rt in zip(self.ms1_scans, self.metadata.loc[self.ms1_scans, 'RetentionTime']):
            smz, sin = self.arrays_mz_cached[scan], self.arrays_i_cached[scan]
            rts.append(rt)
            ins.append(np.sum(sin[(smz >= mz_min) & (smz <= mz_max)]))
        return np.array([rts, ins])


def _extract_and_fit_chroms(rdr, pre_mzs, params, debug_flag, debug_cb):
    """
    extracts and fits chromatograms for a list of precursor m/zs 

    Parameters
    ----------
    rdr : ``_MSMSReaderDDA``
        object for accessing DDA MSMS data from MZA
    pre_mzs : ``set(float)``
        sorted unique precursor m/zs
    params : ``dict(...)``
        analysis parameters dict
    debug_flag : ``str``
        specifies how to dispatch debugging messages, None to do nothing
    debug_cb : ``func``
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'

    Returns
    -------
    features : ``list(tuple(...))``
        list of chromatographic features (pre_mz, peak RT, peak FWHM, peak height, pSNR)
    """
    pid = os.getpid()
    # unpack parameters
    mz_tol = params['dda']['dda_chrom_ext_fit']['dda_cxf_mz_tol']
    min_rel_height = params['dda']['dda_chrom_ext_fit']['dda_cxf_min_rel_height']
    min_abs_height = params['dda']['dda_chrom_ext_fit']['dda_cxf_min_abs_height']
    fwhm_min = params['dda']['dda_chrom_ext_fit']['dda_cxf_fwhm_min']
    fwhm_max = params['dda']['dda_chrom_ext_fit']['dda_cxf_fwhm_max']
    max_peaks = params['dda']['dda_chrom_ext_fit']['dda_cxf_max_peaks']
    min_psnr = params['dda']['dda_chrom_ext_fit']['dda_cxf_min_psnr']
    # extract chromatograms
    debug_handler(debug_flag, debug_cb, 'EXTRACTING AND FITTING CHROMATOGRAMS', pid)
    features = []
    t0 = time()
    n = len(pre_mzs)
    for i, pre_mz in enumerate(pre_mzs): 
        msg = '({}/{}) precursor m/z: {:.4f} -> '.format(i + 1, n, pre_mz)
        # extract chromatogram
        chrom = rdr.get_chrom(pre_mz, mz_tol)
        # try fitting chromatogram (up to 2 peaks)
        _pkrts, _pkhts, _pkwts = find_peaks_1d_gauss(*chrom, 
                                                     min_rel_height, min_abs_height, 
                                                     fwhm_min, fwhm_max, 
                                                     max_peaks, True)
        # calc pSNR for each fitted peak, make sure they meet a threshold
        pkrts, pkhts, pkwts, psnrs = [], [], [], []
        for pkparams in zip(_pkrts, _pkhts, _pkwts):
            psnr = calc_gauss_psnr(*chrom, pkparams)
            if psnr > min_psnr:
                pkrts.append(pkparams[0])
                pkhts.append(pkparams[1])
                pkwts.append(pkparams[2])
                psnrs.append(psnr)
        if len(pkrts) > 0:
            for r, h, w, s in zip(pkrts, pkhts, pkwts, psnrs):
                debug_handler(debug_flag, debug_cb, msg + ' RT: {:.2f} +/- {:.2f} min ({:.1e}, {:.1f})'.format(r, w, h, s), pid)
                features.append((pre_mz, r, h, w, s))
        else: 
            debug_handler(debug_flag, debug_cb, msg + 'no peaks found', pid)
    debug_handler(debug_flag, debug_cb, 'EXTRACTING AND FITTING CHROMATOGRAMS: elapsed: {:.1f} s'.format(time() - t0), pid)
    return features


def _consolidate_chrom_feats(feats, params, debug_flag, debug_cb):
    """
    consolidate chromatographic features that have very similar m/z and RT
    only keep highest intensity features

    Parameters
    ----------
    feats : ``list(tuple(...))``
        list of chromatographic features (pre_mz, peak RT, peak FWHM, peak height, pSNR)
    params : ``dict(...)``
        analysis parameters dict
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
    # unpack parameters
    fc_mz_tol = params['dda']['dda_chrom_feat_cons']['dda_cfc_mz_tol']
    fc_rt_tol = params['dda']['dda_chrom_feat_cons']['dda_cfc_rt_tol']
    # consolidate features
    features_consolidated = []
    for feat in feats:
        add = True
        for i in range(len(features_consolidated)):
            fc_i = features_consolidated[i]
            if abs(feat[0] - fc_i[0]) <= fc_mz_tol and abs(feat[1] - fc_i[1]) <= fc_rt_tol:
                add = False
                if feat[2] > fc_i[2]:
                    features_consolidated[i] = feat
        if add:
            features_consolidated.append(feat)
    debug_handler(debug_flag, debug_cb, 'CONSOLIDATING CHROMATOGRAPHIC FEATURES: {} features -> {} features'.format(len(feats), len(features_consolidated)), pid)
    return features_consolidated


def _extract_and_fit_ms2_spectra(rdr, chrom_feats_consolidated, params, debug_flag, debug_cb):
    """
    extracts MS2 spectra for consolidated chromatographic features, tries to fit spectra peaks,
    returns query data for adding features to database

    Parameters
    ----------
    rdr : ``_MSMSReaderDDA``
        object for accessing DDA MSMS data from MZA
    cur : ``sqlite3.Cursor``
        cursor for making queries into the lipid ids database
    chrom_feats_consolidated : ``list(tuple(...))``
        list of consolidated chromatographic features (pre_mz, peak RT, peak FWHM, peak height, pSNR)
    params : ``dict(...)``
        analysis parameters dict
    debug_flag : ``str``
        specifies how to dispatch debugging messages, None to do nothing
    debug_cb : ``func``
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'

    Returns
    -------
    qdata : ``list(tuple(...))``
        list of query data for all of the features
    """
    pid = os.getpid()
    # unpack parameters
    ms2_pre_mz_tol = params['dda']['dda_ms2_ext_fit']['dda_mxf_pre_mz_tol']
    ms2_mz_bin_min = params['dda']['dda_ms2_ext_fit']['dda_mxf_mz_bin_min']
    ms2_mz_bin_size = params['dda']['dda_ms2_ext_fit']['dda_mxf_mz_bin_size']
    ms2_min_rel_height = params['dda']['dda_ms2_ext_fit']['dda_mxf_min_rel_height']
    ms2_min_abs_height = params['dda']['dda_ms2_ext_fit']['dda_mxf_min_abs_height']
    ms2_fwhm_min = params['dda']['dda_ms2_ext_fit']['dda_mxf_fwhm_min']
    ms2_fwhm_max = params['dda']['dda_ms2_ext_fit']['dda_mxf_fwhm_max']
    ms2_min_dist = params['dda']['dda_ms2_ext_fit']['dda_mxf_min_dist']
    # extract and fit MS2 spectra, then add info to the database
    debug_handler(debug_flag, debug_cb, 'EXTRACTING AND FITTING MS2 SPECTRA', pid)
    t0 = time()
    qdata = []
    n = len(chrom_feats_consolidated)
    for i, (fmz, frt, fht, fwt, fsnr) in enumerate(chrom_feats_consolidated):
        msg = '({}/{}) m/z: {:.4f} RT: {:.2f} +/- {:.2f} min ({:.1e}, {:.1f}) -> '.format(i + 1, n, fmz, frt, fwt, fht, fsnr)
        rt_min, rt_max = frt - fwt, frt + fwt  # RT range is peak RT +/- peak FWHM
        ms2_mz_bin_max = fmz + 5  # only extract MS2 spectrum up to precursor m/z + 5 Da
        # (try to) extract MS2 spectrum
        ms2 = rdr.get_msms_spectrum(fmz, ms2_pre_mz_tol, rt_min, rt_max, 
                                    ms2_mz_bin_min, ms2_mz_bin_max, ms2_mz_bin_size)
        mz_bins, i_bins, n_scan_pre_mzs, scan_pre_mzs = ms2
        msg += '# MS2 scans: {}'.format(n_scan_pre_mzs)
        if n_scan_pre_mzs > 0:
            # find peaks
            pkmzs, pkhts, pkwts = find_peaks_1d_localmax(mz_bins, i_bins,
                                                        ms2_min_rel_height, ms2_min_abs_height, 
                                                        ms2_fwhm_min, ms2_fwhm_max, 
                                                        ms2_min_dist)
            if len(pkmzs) > 0:
                ms2_str = ms2_to_str(pkmzs, pkhts)
                qdata.append((None, rdr.f, fmz, frt, fwt, fht, fsnr, n_scan_pre_mzs, len(pkmzs), ms2_str))
            else:
                qdata.append((None, rdr.f, fmz, frt, fwt, fht, fsnr, n_scan_pre_mzs, 0, None))
            debug_handler(debug_flag, debug_cb, msg + " -> # MS2 peaks: {}".format(len(pkmzs)), pid)
        else:
            qdata.append((None, rdr.f, fmz, frt, fwt, fht, fsnr, n_scan_pre_mzs, None, None))
            debug_handler(debug_flag, debug_cb, msg, pid)
    debug_handler(debug_flag, debug_cb, 'EXTRACTING AND FITTING MS2 SPECTRA: elapsed: {:.1f} s'.format(time() - t0), pid)
    return qdata


def _add_features_to_db(cur, qdata, debug_flag, debug_cb):
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


def extract_dda_features(dda_data_file, results_db, params, 
                         cache_ms1=True, debug_flag=None, debug_cb=None):
    """
    Extract features from a raw DDA data file, store them in a database (initialized using ``create_dda_ids_db`` function)

    Parameters
    ----------
    dda_data_file : ``str``
        path to raw DDA data file (MZA format)
    results_db : ``str``
        path to DDA-DIA analysis results database
    params : ``dict(...)``
        analysis parameters dict
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
    """
    pid = os.getpid()
    debug_handler(debug_flag, debug_cb, 'EXTRACTING DDA FEATURES', pid)
    debug_handler(debug_flag, debug_cb, 'file: {}'.format(dda_data_file), pid)
    # initialize the MSMS reader
    rdr = _MSMSReaderDDA_Cached(dda_data_file) if cache_ms1 else _MSMSReaderDDA(dda_data_file)
    # get the list of precursor m/zs
    pre_mzs = rdr.get_pre_mzs()
    debug_handler(debug_flag, debug_cb, '# precursor m/zs: {}'.format(len(pre_mzs)), pid)
    # extract chromatographic features
    chrom_feats = _extract_and_fit_chroms(rdr, pre_mzs, params, debug_flag, debug_cb)
    # consolidate chromatographic features
    chrom_feats_consolidated = _consolidate_chrom_feats(chrom_feats, params, debug_flag, debug_cb)
    # extract MS2 spectra
    qdata = _extract_and_fit_ms2_spectra(rdr, chrom_feats_consolidated, params, debug_flag, debug_cb)
    # initialize connection to DDA ids database
    con = connect(results_db, timeout=60)  # increase timeout to avoid errors from database locked by another process
    cur = con.cursor()
    # add features to database
    _add_features_to_db(cur, qdata, debug_flag, debug_cb)
    # clean up
    con.commit()
    con.close()
    rdr.close()


def extract_dda_features_multiproc(dda_data_files, results_db, params, n_proc,
                                   cache_ms1=False, debug_flag=None, debug_cb=None):
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
    """
    n_proc = min(n_proc, len(dda_data_files))  # no need to use more processes than the number of inputs
    args = [(dda_data_file, results_db, params) for dda_data_file in dda_data_files]
    args_for_starmap = zip(repeat(extract_dda_features), args, repeat({'cache_ms1': cache_ms1, 'debug_flag': debug_flag, 'debug_cb': debug_cb}))
    with multiprocessing.Pool(processes=n_proc) as p:
        p.starmap(apply_args_and_kwargs, args_for_starmap)


def consolidate_dda_features(results_db, params, 
                             debug_flag=None, debug_cb=None):
    """
    consolidates DDA features from lipid IDs database based on feature m/z and RT using the following criteria:

    * for groups of features having very similar m/z and RT, if none have MS2 scans then only the feature with 
      the highest intensity in each group is kept
    * if at least one feature in a group has MS2 scans, then features in that group that do not have MS2 scans 
      are dropped

    Parameters
    ----------
    results_db : ``str``
        path to DDA-DIA analysis results database
    params : ``dict(...)``
        analysis parameters dict
    debug_flag : ``str``, optional
        specifies how to dispatch debugging messages, None to do nothing
    debug_cb : ``func``, optional
        callback function that takes the debugging message as an argument, can be None if
        debug_flag is not set to 'textcb' or 'textcb_pid'
    """
    # no need to get the PID, this should only ever be run in the main process
    # unpack params
    mzt = params['dda']['dda_feat_cons']['dda_fc_mz_tol']
    rtt = params['dda']['dda_feat_cons']['dda_fc_rt_tol']
    # connect to the database
    con = connect(results_db)
    cur = con.cursor()
    # step 1, create groups of features based on similar m/z and RT
    qry_sel = "SELECT dda_feat_id, mz, rt, rt_pkht, ms2_n_scans FROM DDAFeatures"
    grouped = []
    n_dda_features = 0
    for d in cur.execute(qry_sel).fetchall():
        n_dda_features += 1
        _, mz, rt, *_ = d
        add = True
        for i in range(len(grouped)):
            for _, mz_i, rt_i, *_ in grouped[i]:
                if abs(mz - mz_i) <= mzt and abs(rt - rt_i) <= rtt:
                    grouped[i].append(d)
                    add = False
                    break
            if not add:
                break
        if add:
            grouped.append([d])
    # step 2, determine which features to drop
    drop_fids = []
    for group in grouped:
        if len(group) > 1:
            # only consider groups with multiple features in them
            if sum([_[4] for _ in group]) > 0:
                # at least one feature has MSMS
                for feat in group:
                    if feat[4] < 1:
                        # drop any features in the group that do not have MSMS
                        drop_fids.append(feat[0])
                        # There is a potential here for redundant features that have MSMS spectra because all such
                        # features in a group are kept. I do not really want to change this though, since I do want
                        # to keep the connection between a feature and its mass spectrum, extracted from a particular
                        # data file. Just a note.
            else:
                # none of the features have MSMS
                # only keep the feature with the highest intensity of the group
                # or exclude entirely if params['dda']['dda_feat_cons']['dda_fc_drop_if_no_ms2'] is set
                max_fint = 0
                keep_ffid = None
                for feat in group:
                    ffid, fint = feat[0], feat[3]
                    if not params['dda']['dda_feat_cons']['dda_fc_drop_if_no_ms2']:
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
    debug_handler(debug_flag, debug_cb, 'CONSOLIDATING DDA FEATURES: {} features -> {} features'.format(n_dda_features, n_dda_features - len(drop_fids)))
    # step 3, drop features from database
    qry_drop = "DELETE FROM DDAFeatures WHERE dda_feat_id=?"
    for fid in drop_fids:
        cur.execute(qry_drop, (fid,))
    # commit changes to the database
    con.commit()
    con.close()

    