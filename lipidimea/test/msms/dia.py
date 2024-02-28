"""
lipidimea/test/msms/dia.py

Dylan Ross (dylan.ross@pnnl.gov)

    tests for the lipidimea/msms/dia.py module
"""


import unittest

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

    def test_NO_TESTS_IMPLEMENTED_YET(self):
        """ placeholder, remove this function and implement tests """
        raise NotImplementedError("no tests implemented yet")


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


