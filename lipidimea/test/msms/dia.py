"""
lipidimea/test/msms/dia.py

Dylan Ross (dylan.ross@pnnl.gov)

    tests for the lipidimea/msms/dia.py module
"""


import unittest

import numpy as np

from lipidimea.msms.dia import (
    _select_xic_peak, _lerp_together, _decon_distance, _deconvolute_ms2_peaks,
    _add_single_target_results_to_db, _ms2_peaks_to_str, _single_target_analysis,
    extract_dia_features, extract_dia_features_multiproc, add_calibrated_ccs_to_dia_features
)


class Test_SelectXicPeak(unittest.TestCase):
    """ tests for the _select_xic_peak function """

    def test_SXP_empty_peaks(self):
        """ test selecting XIC peaks from empty list of peak params """
        pkrt, pkht, pkwt = _select_xic_peak(12.34, 0.5, [], [], [])
        self.assertIsNone(pkrt)
        self.assertIsNone(pkht)
        self.assertIsNone(pkwt)
    
    def test_SXP_one_peak_not_selected(self):
        """ test selecting XIC peaks from list of peak params with one entry but not selected """
        pkrt, pkht, pkwt = _select_xic_peak(12.34, 0.5, [23.45], [1e4], [0.25])
        self.assertIsNone(pkrt)
        self.assertIsNone(pkht)
        self.assertIsNone(pkwt)
    
    def test_SXP_one_peak(self):
        """ test selecting XIC peaks from list of peak params with one entry """
        pkrt, pkht, pkwt = _select_xic_peak(12.34, 0.5, [12.54], [1e4], [0.25])
        self.assertEqual(pkrt, 12.54)
        self.assertEqual(pkht, 1e4)
        self.assertEqual(pkwt, 0.25)
    
    def test_SXP_multiple_peaks_not_selected(self):
        """ test selecting XIC peaks from list of peak params with multiple entries but none selected """
        pkrt, pkht, pkwt = _select_xic_peak(12.34, 0.5, [23.45, 13.54, 13.94], [2e4, 1e4, 3e4], [0.3, 0.25, 0.2])
        self.assertIsNone(pkrt)
        self.assertIsNone(pkht)
        self.assertIsNone(pkwt)

    def test_SXP_multiple_peaks(self):
        """ test selecting XIC peaks from list of peak params with multiple entries """
        pkrt, pkht, pkwt = _select_xic_peak(12.34, 0.5, [23.45, 12.54, 12.94], [2e4, 1e4, 3e4], [0.3, 0.25, 0.2])
        self.assertEqual(pkrt, 12.54)
        self.assertEqual(pkht, 1e4)
        self.assertEqual(pkwt, 0.25)


class Test_LerpTogether(unittest.TestCase):
    """ tests for the _lerp_together function """

    def test_LT_non_overlapping(self):
        """ test lerping together non-overlapping ranges """
        data_a = np.array([[1., 2., 3., 4., 5.], [0., 1., 2., 1., 0]])
        data_b = np.array([[6., 7., 8., 9., 10.], [0., 1., 2., 1., 0]])
        xi, yi_a, yi_b = _lerp_together(data_a, data_b, 0.2)
        # returned arrays should all be empty
        self.assertEqual(xi.tolist(), [])
        self.assertEqual(yi_a.tolist(), [])
        self.assertEqual(yi_b.tolist(), [])

    def test_LT_overlapping(self):
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

    def test_LT_overlapping_normalized(self):
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

    def test_NO_TESTS_IMPLEMENTED_YET(self):
        """ placeholder, remove this function and implement tests """
        raise NotImplementedError("no tests implemented yet")


class Test_DeconvoluteMs2Peaks(unittest.TestCase):
    """ tests for the _deconvolute_ms2_peaks function """

    def test_NO_TESTS_IMPLEMENTED_YET(self):
        """ placeholder, remove this function and implement tests """
        raise NotImplementedError("no tests implemented yet")


class Test_AddSingleTargetResultsToDb(unittest.TestCase):
    """ tests for the _add_single_target_results_to_db function """

    def test_NO_TESTS_IMPLEMENTED_YET(self):
        """ placeholder, remove this function and implement tests """
        raise NotImplementedError("no tests implemented yet")


class Test_Ms2PeaksToStr(unittest.TestCase):
    """ tests for the _ms2_peaks_to_str function """

    def test_NO_TESTS_IMPLEMENTED_YET(self):
        """ placeholder, remove this function and implement tests """
        raise NotImplementedError("no tests implemented yet")


class Test_SingleTargetAnalysis(unittest.TestCase):
    """ tests for the _single_target_analysis function """

    def test_NO_TESTS_IMPLEMENTED_YET(self):
        """ placeholder, remove this function and implement tests """
        raise NotImplementedError("no tests implemented yet")


class TestExtractDiaFeatures(unittest.TestCase):
    """ tests for the extract_dia_features function """

    def test_NO_TESTS_IMPLEMENTED_YET(self):
        """ placeholder, remove this function and implement tests """
        raise NotImplementedError("no tests implemented yet")


class TestExtractDiaFeaturesMultiproc(unittest.TestCase):
    """ tests for the extract_dia_features_multiproc function """

    def test_NO_TESTS_IMPLEMENTED_YET(self):
        """ placeholder, remove this function and implement tests """
        raise NotImplementedError("no tests implemented yet")


class TestAddCalibratedCcsToDiaFeatures(unittest.TestCase):
    """ tests for the add_calibrated_ccs_to_dia_features function """

    def test_NO_TESTS_IMPLEMENTED_YET(self):
        """ placeholder, remove this function and implement tests """
        raise NotImplementedError("no tests implemented yet")


if __name__ == "__main__":
    # run the tests for this module if invoked directly
    unittest.main(verbosity=2)


