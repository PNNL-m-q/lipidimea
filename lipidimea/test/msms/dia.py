"""
lipidimea/test/msms/dia.py
Dylan Ross (dylan.ross@pnnl.gov)

    tests for the lipidimea/msms/dia.py module
"""


import unittest
from unittest.mock import patch
from tempfile import TemporaryDirectory
import os
import sqlite3

import numpy as np
from mzapy.peaks import _gauss

from lipidimea.msms.dia import (
    _select_xic_peak, _lerp_together, _decon_distance, _deconvolute_ms2_peaks,
    _add_single_target_results_to_db, _single_target_analysis,
    extract_dia_features, add_calibrated_ccs_to_dia_features
)
from lipidimea.params import DiaParams
from lipidimea.util import create_results_db


# Use the default params for tests
_DIA_PARAMS = DiaParams.load_default()


class Test_SelectXicPeak(unittest.TestCase):
    """ tests for the _select_xic_peak function """

    def test_empty_peaks(self):
        """ test selecting XIC peaks from empty list of peak params """
        pkrt, pkht, pkwt = _select_xic_peak(12.34, 0.5, [], [], [])
        self.assertIsNone(pkrt)
        self.assertIsNone(pkht)
        self.assertIsNone(pkwt)
    
    def test_one_peak_not_selected(self):
        """ test selecting XIC peaks from list of peak params with one entry but not selected """
        pkrt, pkht, pkwt = _select_xic_peak(12.34, 0.5, [23.45], [1e4], [0.25])
        self.assertIsNone(pkrt)
        self.assertIsNone(pkht)
        self.assertIsNone(pkwt)
    
    def test_one_peak(self):
        """ test selecting XIC peaks from list of peak params with one entry """
        pkrt, pkht, pkwt = _select_xic_peak(12.34, 0.5, [12.54], [1e4], [0.25])
        self.assertEqual(pkrt, 12.54)
        self.assertEqual(pkht, 1e4)
        self.assertEqual(pkwt, 0.25)
    
    def test_multiple_peaks_not_selected(self):
        """ test selecting XIC peaks from list of peak params with multiple entries but none selected """
        pkrt, pkht, pkwt = _select_xic_peak(12.34, 0.5, [23.45, 13.54, 13.94], [2e4, 1e4, 3e4], [0.3, 0.25, 0.2])
        self.assertIsNone(pkrt)
        self.assertIsNone(pkht)
        self.assertIsNone(pkwt)

    def test_multiple_peaks(self):
        """ test selecting XIC peaks from list of peak params with multiple entries """
        pkrt, pkht, pkwt = _select_xic_peak(12.34, 0.5, [23.45, 12.54, 12.94], [2e4, 1e4, 3e4], [0.3, 0.25, 0.2])
        self.assertEqual(pkrt, 12.54)
        self.assertEqual(pkht, 1e4)
        self.assertEqual(pkwt, 0.25)


class Test_LerpTogether(unittest.TestCase):
    """ tests for the _lerp_together function """

    def test_non_overlapping(self):
        """ test lerping together non-overlapping ranges """
        data_a = np.array([[1., 2., 3., 4., 5.], [0., 1., 2., 1., 0]])
        data_b = np.array([[6., 7., 8., 9., 10.], [0., 1., 2., 1., 0]])
        xi, yi_a, yi_b = _lerp_together(data_a, data_b, 0.2)
        # returned arrays should all be empty
        self.assertEqual(xi.tolist(), [])
        self.assertEqual(yi_a.tolist(), [])
        self.assertEqual(yi_b.tolist(), [])

    def test_overlapping(self):
        """ test lerping together overlapping ranges """
        data_a = np.array([[1., 2., 3., 4., 5.], [0., 1., 2., 1., 0]])
        data_b = np.array([[3., 4., 5., 6., 7.], [0., 1., 2., 1., 0]])
        xi, yi_a, yi_b = _lerp_together(data_a, data_b, 0.25, normalize=False)
        # all arrays should have the expected length
        l = 9
        self.assertEqual(len(xi), l)
        self.assertEqual(len(yi_a), l)
        self.assertEqual(len(yi_b), l)
        # check interpolated values in yi_a and yi_b
        # x = [3., 3.25, 3.5, 3.75, 4., 4.25, 4.5, 4.75, 5.]
        self.assertListEqual(yi_a.tolist(), [2., 1.75, 1.5, 1.25, 1., 0.75, 0.5, 0.25, 0.])
        self.assertListEqual(yi_b.tolist(), [0., 0.25, 0.5, 0.75, 1., 1.25, 1.5, 1.75, 2.])

    def test_overlapping_normalized(self):
        """ test lerping together overlapping ranges and normalized y values """
        data_a = np.array([[1., 2., 3., 4., 5.], [0., 1., 2., 1., 0]])
        data_b = np.array([[3., 4., 5., 6., 7.], [0., 1., 2., 1., 0]])
        xi, yi_a, yi_b = _lerp_together(data_a, data_b, 0.25)
        # all arrays should have the expected length
        l = 9
        self.assertEqual(len(xi), l)
        self.assertEqual(len(yi_a), l)
        self.assertEqual(len(yi_b), l)
        # check interpolated values in yi_a and yi_b
        # x = [3., 3.25, 3.5, 3.75, 4., 4.25, 4.5, 4.75, 5.]
        self.assertListEqual(yi_a.tolist(), [1., 0.875, 0.750, 0.625, 0.500, 0.375, 0.250, 0.125, 0.])
        self.assertListEqual(yi_b.tolist(), [0., 0.125, 0.250, 0.375, 0.500, 0.625, 0.750, 0.875, 1.])


class Test_DeconDistance(unittest.TestCase):
    """ tests for the _decon_distance function """

    def test_zero_dist(self):
        """ test that identical signals produce 0 distance with multiple distance functions """
        np.random.seed(420)
        x = np.arange(0., 101., 1.)
        data_a = np.array([x, np.random.random(x.shape)])
        data_b = data_a.copy()
        for dist_func in ["cosine", "correlation", "euclidean"]:
            self.assertEqual(_decon_distance(data_a, data_b, dist_func, 1.), 0.,
                             msg=f"distance func {dist_func} did not produce 0 distance with identical data")
            
    def test_nonzero_dist(self):
        """ test that different random signals produce >0 distance with multiple distance functions """
        np.random.seed(420)
        x = np.arange(0., 101., 1.)
        data_a = np.array([x, np.random.random(x.shape)])
        data_b = np.array([x, np.random.random(x.shape)])
        for dist_func in ["cosine", "correlation", "euclidean"]:
            self.assertGreater(_decon_distance(data_a, data_b, dist_func, 1.), 0.,
                               msg=f"distance func {dist_func} did not produce >0 distance")


class Test_DeconvoluteMs2Peaks(unittest.TestCase):
    """ tests for the _deconvolute_ms2_peaks function """

    def test_mock_data_match_XIC_match_ATD(self):
        """ test deconvoluting MS2 peaks with mock data and matching XIC and ATD """
        # make a fake XIC with one peak
        np.random.seed(420)
        xic_rts = np.arange(12, 17.05, 0.01)
        noise1 = np.random.normal(1, 0.2, size=xic_rts.shape)
        noise2 = np.random.normal(1, 0.1, size=xic_rts.shape)
        xic_iis = 1000 * noise1 
        xic_iis += _gauss(xic_rts, 15, 1e5, 0.25) * noise2 
        # make a fake ATD with one peak
        atd_ats = np.arange(30, 50.05, 0.05)
        noise1 = np.random.normal(1, 0.2, size=atd_ats.shape)
        noise2 = np.random.normal(1, 0.1, size=atd_ats.shape)
        atd_iis = 1000 * noise1 
        atd_iis += _gauss(atd_ats, 40, 1e5, 2.5) * noise2
        # make another fake XIC with one peak 
        np.random.seed(420)
        xic2_rts = np.arange(12, 17.05, 0.05)
        noise1 = np.random.normal(1, 0.4, size=xic2_rts.shape)
        noise2 = np.random.normal(1, 0.2, size=xic2_rts.shape)
        xic2_iis = 1000 * noise1 
        xic2_iis += _gauss(xic2_rts, 15.1, 1e5, 0.27) * noise2 
        # make another fake ATD with one peak
        atd2_ats = np.arange(30, 50.05, 0.075)
        noise1 = np.random.normal(1, 0.4, size=atd2_ats.shape)
        noise2 = np.random.normal(1, 0.2, size=atd2_ats.shape)
        atd2_iis = 1000 * noise1 
        atd2_iis += _gauss(atd2_ats, 40.5, 1e5, 2.6) * noise2
        # assemble precursor Xic and Atd from the second set of fake data
        pre_xic = (xic2_rts, xic2_iis)
        pre_atd = (atd2_ats, atd2_iis)
        # need to patch a mock MZA instance
        with patch('mzapy.MZA') as MockReader:
            # mock a MZA instance with 
            # collect_xic_arrays_by_mz method that returns a fake XIC
            # collect_atd_arrays_by_rt_mz method that returns a fake ATD
            rdr = MockReader.return_value
            rdr.collect_xic_arrays_by_mz.return_value = (xic_rts, xic_iis)
            rdr.collect_atd_arrays_by_rt_mz.return_value = (atd_ats, atd_iis)
            # test the function
            deconvoluted, raws = _deconvolute_ms2_peaks(rdr, [789.0123], pre_xic, 15.1, 0.27, pre_atd, _DIA_PARAMS)
            # should get one entry in the deconvoluted list
            self.assertEqual(len(deconvoluted), 1)
            # make sure the deconvoluted feature has the correct info
            self.assertTrue(deconvoluted[0][0])
            self.assertLess(deconvoluted[0][1], 0.5)
            self.assertLess(deconvoluted[0][2], 0.5)

    def test_mock_data_match_XIC_nomatch_ATD(self):
        """ test deconvoluting MS2 peaks with mock data and matching XIC and non matching ATD """
        # make a fake XIC with one peak
        np.random.seed(420)
        xic_rts = np.arange(12, 17.05, 0.01)
        noise1 = np.random.normal(1, 0.2, size=xic_rts.shape)
        noise2 = np.random.normal(1, 0.1, size=xic_rts.shape)
        xic_iis = 1000 * noise1 
        xic_iis += _gauss(xic_rts, 15, 1e5, 0.25) * noise2 
        # make a fake ATD with one peak, bad AT
        atd_ats = np.arange(30, 50.05, 0.05)
        noise1 = np.random.normal(1, 0.2, size=atd_ats.shape)
        noise2 = np.random.normal(1, 0.1, size=atd_ats.shape)
        atd_iis = 1000 * noise1 
        atd_iis += _gauss(atd_ats, 35, 1e5, 2.5) * noise2
        # make another fake XIC with one peak 
        np.random.seed(420)
        xic2_rts = np.arange(12, 17.05, 0.05)
        noise1 = np.random.normal(1, 0.4, size=xic2_rts.shape)
        noise2 = np.random.normal(1, 0.2, size=xic2_rts.shape)
        xic2_iis = 1000 * noise1 
        xic2_iis += _gauss(xic2_rts, 15.1, 1e5, 0.27) * noise2 
        # make another fake ATD with one peak
        atd2_ats = np.arange(30, 50.05, 0.075)
        noise1 = np.random.normal(1, 0.4, size=atd2_ats.shape)
        noise2 = np.random.normal(1, 0.2, size=atd2_ats.shape)
        atd2_iis = 1000 * noise1 
        atd2_iis += _gauss(atd2_ats, 40.5, 1e5, 2.6) * noise2
        # assemble precursor Xic and Atd from the second set of fake data
        pre_xic = (xic2_rts, xic2_iis)
        pre_atd = (atd2_ats, atd2_iis)
        # need to patch a mock MZA instance
        with patch('mzapy.MZA') as MockReader:
            # mock a MZA instance with 
            # collect_xic_arrays_by_mz method that returns a fake XIC
            # collect_atd_arrays_by_rt_mz method that returns a fake ATD
            rdr = MockReader.return_value
            rdr.collect_xic_arrays_by_mz.return_value = (xic_rts, xic_iis)
            rdr.collect_atd_arrays_by_rt_mz.return_value = (atd_ats, atd_iis)
            # test the function
            deconvoluted, raws = _deconvolute_ms2_peaks(rdr, [789.0123], pre_xic, 15.1, 0.27, pre_atd, _DIA_PARAMS)
            # should get a result with deconvoluted flag set to False
            self.assertEqual(len(deconvoluted), 1)
            # make sure the deconvoluted feature has the correct info
            self.assertFalse(deconvoluted[0][0])
            self.assertLess(deconvoluted[0][1], 0.5)
            # ATD distance should cause the False label
            self.assertGreater(deconvoluted[0][2], 0.5) 

    def test_mock_data_nomatch_XIC_nomatch_ATD(self):
        """ test deconvoluting MS2 peaks with mock data and non matching XIC and non matching ATD """
        # make a fake XIC with one peak, bad RT
        np.random.seed(420)
        xic_rts = np.arange(12, 17.05, 0.01)
        noise1 = np.random.normal(1, 0.2, size=xic_rts.shape)
        noise2 = np.random.normal(1, 0.1, size=xic_rts.shape)
        xic_iis = 1000 * noise1 
        xic_iis += _gauss(xic_rts, 13, 1e5, 0.25) * noise2 
        # make a fake ATD with one peak, bad AT
        atd_ats = np.arange(30, 50.05, 0.05)
        noise1 = np.random.normal(1, 0.2, size=atd_ats.shape)
        noise2 = np.random.normal(1, 0.1, size=atd_ats.shape)
        atd_iis = 1000 * noise1 
        atd_iis += _gauss(atd_ats, 35, 1e5, 2.5) * noise2
        # make another fake XIC with one peak 
        np.random.seed(420)
        xic2_rts = np.arange(12, 17.05, 0.05)
        noise1 = np.random.normal(1, 0.4, size=xic2_rts.shape)
        noise2 = np.random.normal(1, 0.2, size=xic2_rts.shape)
        xic2_iis = 1000 * noise1 
        xic2_iis += _gauss(xic2_rts, 15.1, 1e5, 0.27) * noise2 
        # make another fake ATD with one peak
        atd2_ats = np.arange(30, 50.05, 0.075)
        noise1 = np.random.normal(1, 0.4, size=atd2_ats.shape)
        noise2 = np.random.normal(1, 0.2, size=atd2_ats.shape)
        atd2_iis = 1000 * noise1 
        atd2_iis += _gauss(atd2_ats, 40.5, 1e5, 2.6) * noise2
        # assemble precursor Xic and Atd from the second set of fake data
        pre_xic = (xic2_rts, xic2_iis)
        pre_atd = (atd2_ats, atd2_iis)
        # need to patch a mock MZA instance
        with patch('mzapy.MZA') as MockReader:
            # mock a MZA instance with 
            # collect_xic_arrays_by_mz method that returns a fake XIC
            # collect_atd_arrays_by_rt_mz method that returns a fake ATD
            rdr = MockReader.return_value
            rdr.collect_xic_arrays_by_mz.return_value = (xic_rts, xic_iis)
            rdr.collect_atd_arrays_by_rt_mz.return_value = (atd_ats, atd_iis)
            # test the function
            deconvoluted, raws = _deconvolute_ms2_peaks(rdr, [789.0123], pre_xic, 15.1, 0.27, pre_atd, _DIA_PARAMS)
            # should get a result with deconvoluted flag set to False
            self.assertEqual(len(deconvoluted), 1)
            # make sure the deconvoluted feature has the correct info
            self.assertFalse(deconvoluted[0][0])
            # XIC should cause the False label
            self.assertGreater(deconvoluted[0][1], 0.5)
            # ATD is still None because it isnt checked after XIC 
            self.assertIsNone(deconvoluted[0][2]) 


class Test_AddSingleTargetResultsToDb(unittest.TestCase):
    """ tests for the _add_single_target_results_to_db function """

    def test_no_decon_frags(self):
        """ test adding a single target's results to DB with no deconvoluted fragments """
        # make a fake XIC with one peak
        np.random.seed(420)
        xic_rts = np.arange(12, 17.05, 0.01)
        noise1 = np.random.normal(1, 0.2, size=xic_rts.shape)
        noise2 = np.random.normal(1, 0.1, size=xic_rts.shape)
        xic_iis = 1000 * noise1 
        xic_iis += _gauss(xic_rts, 15, 1e5, 0.25) * noise2 
        # make a fake ATD with one peak
        atd_ats = np.arange(30, 50.05, 0.05)
        noise1 = np.random.normal(1, 0.2, size=atd_ats.shape)
        noise2 = np.random.normal(1, 0.1, size=atd_ats.shape)
        atd_iis = 1000 * noise1 
        atd_iis += _gauss(atd_ats, 40, 1e5, 2.5) * noise2
        # assemble precursor Xic and Atd from the fake data
        xic = (xic_rts, xic_iis)
        atd = (atd_ats, atd_iis)
        # fake MS2 peaks
        ms12_mzs = np.arange(50, 800, 0.01)
        noise1 = np.random.normal(1, 0.2, size=ms12_mzs.shape)
        ms12_iis = 1000 * noise1 
        noise2 = np.random.normal(1, 0.1, size=ms12_mzs.shape)
        pkmzs = np.arange(100, 800, 25, dtype=float)
        for pkmz in pkmzs:
            ms12_iis += _gauss(ms12_mzs, pkmz, 1e5, 0.1) * noise2 
        ms12 = (ms12_mzs, ms12_iis)
        with TemporaryDirectory() as tmp_dir:
            dbf = os.path.join(tmp_dir, "results.db")
            create_results_db(dbf)  # STRICT!
            con = sqlite3.connect(dbf)
            cur = con.cursor()
            # test the function
            _add_single_target_results_to_db(cur, None, -1, 
                                             420.6969, 
                                             12.34, 0.25, 1e5, 10.,
                                             40., 2.5, 1e6, 10.,
                                             (ms12, xic, atd), 
                                             pkmzs, [1e5 for _ in pkmzs], 
                                             [(False, None, None) for _ in pkmzs], 
                                             [(None, None) for _ in pkmzs], 
                                             True)
            # check that the feature was added to the database
            # this query should return 1 row
            self.assertEqual(len(cur.execute("SELECT * FROM DIAPrecursors").fetchall()), 1)

    def test_decon_frags(self):
        """ test adding a single target's results to DB with deconvoluted fragments """
        # make a fake XIC with one peak
        np.random.seed(420)
        xic_rts = np.arange(12, 17.05, 0.01)
        noise1 = np.random.normal(1, 0.2, size=xic_rts.shape)
        noise2 = np.random.normal(1, 0.1, size=xic_rts.shape)
        xic_iis = 1000 * noise1 
        xic_iis += _gauss(xic_rts, 15, 1e5, 0.25) * noise2 
        # make a fake ATD with one peak
        atd_ats = np.arange(30, 50.05, 0.05)
        noise1 = np.random.normal(1, 0.2, size=atd_ats.shape)
        noise2 = np.random.normal(1, 0.1, size=atd_ats.shape)
        atd_iis = 1000 * noise1 
        atd_iis += _gauss(atd_ats, 40, 1e5, 2.5) * noise2
        # assemble precursor Xic and Atd from the fake data
        xic = (xic_rts, xic_iis)
        atd = (atd_ats, atd_iis)
        # make fake MS1/MS2 spectra
        ms12_mzs = np.arange(50, 800, 0.01)
        noise1 = np.random.normal(1, 0.2, size=ms12_mzs.shape)
        ms12_iis = 1000 * noise1 
        noise2 = np.random.normal(1, 0.1, size=ms12_mzs.shape)
        pkmzs = np.arange(100, 800, 25)
        for pkmz in pkmzs:
            ms12_iis += _gauss(ms12_mzs, pkmz, 1e5, 0.1) * noise2 
        ms12 = (ms12_mzs, ms12_iis)
        with TemporaryDirectory() as tmp_dir:
            dbf = os.path.join(tmp_dir, "results.db")
            create_results_db(dbf)  # STRICT!
            con = sqlite3.connect(dbf)
            cur = con.cursor()
            # test the function
            _add_single_target_results_to_db(cur, None, -1, 
                                             420.6969, 
                                             12.34, 0.25, 1e5, 10.,
                                             40., 2.5, 1e6, 10.,
                                             (ms12, xic, atd), 
                                             [123.4567, 234.5678, 345.6789], [1e3, 1e4, 1e5], 
                                             [(True, 0.05, 0.06), (True, 0.07, 0.08), (True, 0.09, 0.10)], 
                                             [(xic, atd) for _ in range(3)], 
                                             True)
            # check that the feature was added to the database
            # this query should return 1 row
            self.assertEqual(len(cur.execute("SELECT * FROM DIAPrecursors").fetchall()), 1)
            # this query should return 3 rows
            self.assertEqual(len(cur.execute("SELECT * FROM DIAFragments").fetchall()), 3)


class Test_SingleTargetAnalysis(unittest.TestCase):
    """ tests for the _single_target_analysis function """

    # TODO (Dylan Ross): Add a method to test cases where dia_data_file is provided as a path, an 
    #                    integer file ID, or some invalid value.

    def test_mock_data(self):
        """ use mock data to test complete single target analysis """
        # make a fake XIC with one peak
        np.random.seed(420)
        xic_rts = np.arange(12, 17.05, 0.01)
        noise1 = np.random.normal(1, 0.2, size=xic_rts.shape)
        noise2 = np.random.normal(1, 0.1, size=xic_rts.shape)
        xic_iis = 1000 * noise1 
        xic_iis += _gauss(xic_rts, 15, 1e5, 0.25) * noise2 
        # make a fake ATD with one peak, bad AT
        atd_ats = np.arange(30, 50.05, 0.05)
        noise1 = np.random.normal(1, 0.2, size=atd_ats.shape)
        noise2 = np.random.normal(1, 0.1, size=atd_ats.shape)
        atd_iis = 1000 * noise1 
        atd_iis += _gauss(atd_ats, 35, 1e5, 2.5) * noise2
        # make a fake MS2 spectrum with peaks
        ms2_mzs = np.arange(50, 800, 0.01)
        noise1 = np.random.normal(1, 0.2, size=ms2_mzs.shape)
        ms2_iis = 1000 * noise1 
        noise2 = np.random.normal(1, 0.1, size=ms2_mzs.shape)
        pkmzs = np.arange(100, 800, 25, dtype=np.float64)
        for pkmz in pkmzs:
            ms2_iis += _gauss(ms2_mzs, pkmz, 1e5, 0.075) * noise2 
        # need to patch a mock MZA instance
        # and create a fake database
        with patch('lipidimea.msms.dia.MZA') as MockReader, TemporaryDirectory() as tmp_dir:
            # mock a MZA instance with 
            # collect_xic_arrays_by_mz method that returns a fake XIC
            # collect_atd_arrays_by_rt_mz method that returns a fake ATD
            # collect_ms2_arrays_by_rt_dt method that returns a fake MS2 spectrum
            rdr = MockReader.return_value
            rdr.collect_xic_arrays_by_mz.return_value = (xic_rts, xic_iis)
            rdr.collect_atd_arrays_by_rt_mz.return_value = (atd_ats, atd_iis)
            rdr.collect_ms2_arrays_by_rt_dt.return_value = (ms2_mzs, ms2_iis)
            # make the fake results database
            dbf = os.path.join(tmp_dir, "results.db")
            create_results_db(dbf)  # STRICT!
            con = sqlite3.connect(dbf)
            cur = con.cursor()
            # need to insert a couple of entries into DDAFragments for determining m/z bounds 
            # for extracting MS2 from DIA data
            dda_pre_id = 69420
            cur.executemany(
                "INSERT INTO DDAFragments VALUES (?,?,?,?)",
                [
                    (None, dda_pre_id, fmz, 1e3)
                    for fmz in pkmzs
                ]
            )
            # test the function
            n = _single_target_analysis(1, 0, rdr, cur, 1, dda_pre_id, 789.0123, "15.", 25, _DIA_PARAMS, None, None)
            # check that the feature was added to the database
            # this query should return 1 row
            #print(cur.execute("SELECT * FROM DIAPrecursors").fetchall())
            self.assertEqual(len(cur.execute("SELECT * FROM DIAPrecursors").fetchall()), 1)
            #print(cur.execute("SELECT * FROM DIAFragments").fetchall())
            # There should be more than 20 fragment peaks picked up
            self.assertGreater(len(cur.execute("SELECT * FROM DIAFragments").fetchall()), 20)
            # also the feature count returned from the function should be 1
            self.assertEqual(n, 1)


class TestExtractDiaFeatures(unittest.TestCase):
    """ tests for the extract_dia_features function """

    def test_mock_data(self):
        """ use mock data to test the main workflow function for extracting DIA features """
        # make a fake XIC with one peak
        np.random.seed(420)
        xic_rts = np.arange(12, 17.05, 0.01)
        noise1 = np.random.normal(1, 0.2, size=xic_rts.shape)
        noise2 = np.random.normal(1, 0.1, size=xic_rts.shape)
        xic_iis = 1000 * noise1 
        xic_iis += _gauss(xic_rts, 15, 1e5, 0.25) * noise2 
        # make a fake ATD with one peak, bad AT
        atd_ats = np.arange(30, 50.05, 0.05)
        noise1 = np.random.normal(1, 0.2, size=atd_ats.shape)
        noise2 = np.random.normal(1, 0.1, size=atd_ats.shape)
        atd_iis = 1000 * noise1 
        atd_iis += _gauss(atd_ats, 35, 1e5, 2.5) * noise2
        # make a fake MS2 spectrum with peaks
        ms2_mzs = np.arange(50, 800, 0.01)
        noise1 = np.random.normal(1, 0.2, size=ms2_mzs.shape)
        ms2_iis = 1000 * noise1 
        noise2 = np.random.normal(1, 0.1, size=ms2_mzs.shape)
        pkmzs = np.arange(100, 800, 25, dtype=np.float64)
        for pkmz in pkmzs:
            ms2_iis += _gauss(ms2_mzs, pkmz, 1e5, 0.1) * noise2 
        # need to patch a mock MZA instance
        # and create a fake database
        # NOTE (Dylan Ross): Notice here that I had to patch lipidimea.msms.dia.MZA rather than mzapy.MZA
        #                    as I did in the other tests. The reason for this as I currently understand it
        #                    is that the lipidimea.msms.dia module imports MZA and uses that to instantiate 
        #                    a reader object inside of the extract_dia_features function and it is that 
        #                    imported MZA that needs to get patched, not the source MZA from mzapy for it to
        #                    work correctly. In the other examples I am passing in an instance of the mocked
        #                    reader object into the functions I am testing so it seems that it suffices to
        #                    just use the patch method on mzapy.MZA. In fact, now that I think about it in 
        #                    those cases it may not be necessary at all to use patch() since I am building 
        #                    the mock object with all required methods/attributes and not even importing 
        #                    from mzapy.
        # TODO (Dylan Ross): Considering the above, I should change all the places where I use patch()
        #                    unnecessarily and just build out the mocked reader objects without the unneeded 
        #                    reference to mzapy.MZA
        with patch('lipidimea.msms.dia.MZA') as MockReader, TemporaryDirectory() as tmp_dir:
            # mock a MZA instance with 
            # collect_xic_arrays_by_mz method that returns a fake XIC
            # collect_atd_arrays_by_rt_mz method that returns a fake ATD
            # collect_ms2_arrays_by_rt_dt method that returns a fake MS2 spectrum
            rdr = MockReader.return_value
            rdr.collect_xic_arrays_by_mz.return_value = (xic_rts, xic_iis)
            rdr.collect_atd_arrays_by_rt_mz.return_value = (atd_ats, atd_iis)
            rdr.collect_ms2_arrays_by_rt_dt.return_value = (ms2_mzs, ms2_iis)
            # make the fake results database
            dbf = os.path.join(tmp_dir, "results.db")
            create_results_db(dbf)  # STRICT!
            con = sqlite3.connect(dbf)
            cur = con.cursor()
            # need to insert a couple of entries into DDAFragments for determining m/z bounds 
            # for extracting MS2 from DIA data
            dda_pre_id = 69420
            cur.executemany(
                "INSERT INTO DDAFragments VALUES (?,?,?,?)",
                [
                    (None, dda_pre_id, fmz, 1e3)
                    for fmz in pkmzs
                ]
            )
            # add the input data to DDAPrecursors table
            dda_qdata = (
                69420, 
                1, 
                789.0123, 
                15., 0.1, 1e5, 20., 
                3, 25
            )
            cur.execute(f"INSERT INTO DDAPrecursors VALUES ({("?," * 9).rstrip(",")});", dda_qdata)
            con.commit()
            # test the function
            n = extract_dia_features("dia.data.file", dbf, _DIA_PARAMS)
            # check that the feature was added to the database
            # this query should return 1 row
            self.assertEqual(len(cur.execute("SELECT * FROM DIAPrecursors").fetchall()), 1)
            # this query should return at least 20 rows
            self.assertGreater(len(cur.execute("SELECT * FROM DIAFragments").fetchall()), 20)
            # also the feature count returned from the function should be 1
            self.assertEqual(n, 1)


# NOTE (Dylan Ross): removed the unit test for extract_dia_features_multiproc as mocking does 
#                    not work well with multiprocessing. The actual business logic function is 
#                    fully tested and the logic of applying it in a multiprocessing context via 
#                    starmap is small and straightforward so should be able to trust it well 
#                    enough without the unit test


class TestAddCalibratedCcsToDiaFeatures(unittest.TestCase):
    """ tests for the add_calibrated_ccs_to_dia_features function """

    def test_mock_data(self):
        """ test adding calibrated CCS to DIA features with some mock data """
        with TemporaryDirectory() as tmp_dir:
            # make the fake results database
            dbf = os.path.join(tmp_dir, "results.db")
            create_results_db(dbf)  # STRICT!
            con = sqlite3.connect(dbf)
            cur = con.cursor()
            # add the input data to DDAFeatures table
            # dda_qdata = (69420, "dda.data.file", 789.0123, 15., 0.1, 1e5, 20., 3, 0, None)
            # cur.execute("INSERT INTO DDAPrecursors VALUES (?,?,?,?,?,?,?,?,?,?);", dda_qdata)
            # add the input data to DIAPrecursors table
            dfile_id = 69420
            for dia_qdata in [
                (
                    1, 
                    None, 
                    dfile_id, 
                    789.0123, 
                    11.0, 0.1, 1e5, 20., 
                    31, 2.5, 1e5, 10.,
                    None, None 
                ),
                (
                    2, 
                    None, 
                    dfile_id, 
                    789.0123, 
                    12.0, 0.1, 1e5, 20., 
                    32, 2.5, 1e5, 10.,
                    None, None 
                ),
                (
                    3, 
                    None, 
                    dfile_id, 
                    789.0123, 
                    13.0, 0.1, 1e5, 20., 
                    33, 2.5, 1e5, 10.,
                    None, None 
                ),
                (
                    4, 
                    None, 
                    dfile_id, 
                    789.0123, 
                    14.0, 0.1, 1e5, 20., 
                    34, 2.5, 1e5, 10.,
                    None, None 
                ),
                (
                    5, 
                    None, 
                    dfile_id, 
                    789.0123, 
                    15.0, 0.1, 1e5, 20., 
                    35, 2.5, 1e5, 10.,
                    None, None 
                ),
            ]: 
                cur.execute(f"INSERT INTO DIAPrecursors VALUES ({("?," * 14).rstrip(",")});",
                            dia_qdata)
            con.commit()
            # test the function
            add_calibrated_ccs_to_dia_features(dbf, dfile_id, 0., 1.)
            # make sure the CCS values got added
            for ccs in cur.execute("SELECT ccs FROM DIAPrecursors").fetchall():
                self.assertIsNotNone(ccs)


# group all of the tests from this module into a TestSuite
_loader = unittest.TestLoader()
AllTestsDia = unittest.TestSuite()
AllTestsDia.addTests([
    _loader.loadTestsFromTestCase(Test_SelectXicPeak),
    _loader.loadTestsFromTestCase(Test_LerpTogether),
    _loader.loadTestsFromTestCase(Test_DeconDistance),
    _loader.loadTestsFromTestCase(Test_DeconvoluteMs2Peaks),
    _loader.loadTestsFromTestCase(Test_AddSingleTargetResultsToDb),
    _loader.loadTestsFromTestCase(Test_SingleTargetAnalysis),
    _loader.loadTestsFromTestCase(TestExtractDiaFeatures),
    _loader.loadTestsFromTestCase(TestAddCalibratedCcsToDiaFeatures),
])


if __name__ == '__main__':
    # run all defined TestCases for only this module if invoked directly
    unittest.TextTestRunner(verbosity=2).run(AllTestsDia)
