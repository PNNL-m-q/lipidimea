"""
lipidimea/test/msms/dda.py

Dylan Ross (dylan.ross@pnnl.gov)

    tests for the lipidimea/msms/dda.py module
"""

"""
with patch('t.a.A') as MockClass:
            instance = MockClass.return_value
            instance.get_param1.return_value = 1
"""


import unittest
from unittest.mock import patch

import numpy as np
from mzapy.peaks import _gauss

from lipidimea.msms.dda import (
    _MSMSReaderDDA, _MSMSReaderDDA_Cached, _extract_and_fit_chroms, _consolidate_chrom_feats,
    _extract_and_fit_ms2_spectra, _add_features_to_db, extract_dda_features, 
    extract_dda_features_multiproc, consolidate_dda_features
)


class Test_MSMSReaderDDA(unittest.TestCase):
    """ tests for the _MSMSReaderDDA class """

    def test_NO_TESTS_IMPLEMENTED_YET(self):
        """ placeholder, remove this function and implement tests """
        raise NotImplementedError("no tests implemented yet")


class Test_MSMSReaderDDACached(unittest.TestCase):
    """ tests for the _MSMSReaderDDA_Cached class """

    def test_NO_TESTS_IMPLEMENTED_YET(self):
        """ placeholder, remove this function and implement tests """
        raise NotImplementedError("no tests implemented yet")

class Test_ExtractAndFitChroms(unittest.TestCase):
    """ tests for the _extract_and_fit_chroms function """

    def _helper_cb(self, msg):
        """ helper method simulating a debug callback, stores messages in a list in self.__msgs """
        self.__msgs.append(msg)

    def test_EAFC_chrom_no_peaks(self):
        """ test extracting and fitting chromatogram from noisy signal with no peaks in it """
        # make a fake XIC with no peaks
        np.random.seed(420)
        xic_rts = np.arange(0, 20.05, 0.01)
        noise1 = np.random.normal(1, 0.2, size=xic_rts.shape)
        xic_iis = 1000 * noise1 
        # mock a _MSMSReaderDDA instance with get_chrom method that returns the fake XIC 
        with patch('lipidimea.msms.dda._MSMSReaderDDA') as MockReader:
            rdr = MockReader.return_value
            rdr.get_chrom.return_value = (xic_rts, xic_iis)
            # use a helper callback function to store instead of printing debugging messages
            self.__msgs = []
            # test the function
            features = _extract_and_fit_chroms(rdr, {789.0123}, 
                                               20, 0.3, 1e3, 0.1, 1.0, 3, 4, 
                                               debug_flag="textcb", debug_cb=self._helper_cb)
            # there should be no features found in this XIC, it is just flat noise
            self.assertListEqual(features, [],
                                 msg="the fake XIC is flat noise and should not have any peaks")
            # make sure that the correct number of debugging messages were generated
            self.assertEqual(len(self.__msgs), 3)
            # check for debug message showing no peaks found
            self.assertIn("no peaks found", self.__msgs[1])

    def test_EAFC_chrom_with_peaks(self):
        """ test extracting and fitting chromatogram from signal with two peaks in it """
        # make a fake XIC with two peaks
        np.random.seed(420)
        xic_rts = np.arange(0, 20.05, 0.01)
        noise1 = np.random.normal(1, 0.2, size=xic_rts.shape)
        noise2 = np.random.normal(1, 0.1, size=xic_rts.shape)
        xic_iis = 1000 * noise1 
        xic_iis += _gauss(xic_rts, 15, 1e5, 0.25) * noise2 
        xic_iis += _gauss(xic_rts, 14.25, 5e4, 0.5) * noise2
        # expected feature parameters
        expected_features = [
            (789.0123, 15., 1e5, 0.25, 14),
            (789.0123, 14.25, 5e4, 0.5, 5),
        ]
        # mock a _MSMSReaderDDA instance with get_chrom method that returns the fake XIC 
        with patch('lipidimea.msms.dda._MSMSReaderDDA') as MockReader:
            rdr = MockReader.return_value
            rdr.get_chrom.return_value = (xic_rts, xic_iis)
            # use a helper callback function to store instead of printing debugging messages
            self.__msgs = []
            # test the function
            features = _extract_and_fit_chroms(rdr, {789.0123}, 
                                               20, 0.3, 1e3, 0.1, 1.0, 3, 4, 
                                               debug_flag="textcb", debug_cb=self._helper_cb)
            # check that the extracted features have close to the expected values
            for feat, exp_feat in zip(features, expected_features):
                fmz, frt, fht, fwt, fsnr = feat
                efmz, efrt, efht, efwt, efsnr = exp_feat
                self.assertAlmostEqual(fmz, efmz, places=4)
                self.assertAlmostEqual(frt, efrt, places=1)
                self.assertAlmostEqual(fwt, efwt, places=1)
                self.assertLess(abs(fht - efht) / efht, 0.1)
                self.assertAlmostEqual(fsnr, efsnr, places=0)       
            # make sure that the correct number of debugging messages were generated
            self.assertEqual(len(self.__msgs), 4)
            # check for debug messages showing two found peaks
            self.assertIn("RT", self.__msgs[1])
            self.assertIn("RT", self.__msgs[2])


class Test_ConsolidateChromFeats(unittest.TestCase):
    """ tests for the _consolidate_chrom_feats function """

    def test_NO_TESTS_IMPLEMENTED_YET(self):
        """ placeholder, remove this function and implement tests """
        raise NotImplementedError("no tests implemented yet")
    

class Test_ExtractAndFitMs2Spectra(unittest.TestCase):
    """ tests for the _extract_and_fit_ms2_spectra function """

    def test_NO_TESTS_IMPLEMENTED_YET(self):
        """ placeholder, remove this function and implement tests """
        raise NotImplementedError("no tests implemented yet")


class Test_AddFeaturesToDb(unittest.TestCase):
    """ tests for the _add_features_to_db function """

    def test_NO_TESTS_IMPLEMENTED_YET(self):
        """ placeholder, remove this function and implement tests """
        raise NotImplementedError("no tests implemented yet")
    

class TestExtractDdaFeatures(unittest.TestCase):
    """ tests for the extract_dda_features function """

    def test_NO_TESTS_IMPLEMENTED_YET(self):
        """ placeholder, remove this function and implement tests """
        raise NotImplementedError("no tests implemented yet")
    

class TestExtractDdaFeaturesMultiproc(unittest.TestCase):
    """ tests for the extract_dda_features_multiproc function """

    def test_NO_TESTS_IMPLEMENTED_YET(self):
        """ placeholder, remove this function and implement tests """
        raise NotImplementedError("no tests implemented yet")
    

class TestConsolidateDdaFeatures(unittest.TestCase):
    """ tests for the consolidate_dda_features function """

    def test_NO_TESTS_IMPLEMENTED_YET(self):
        """ placeholder, remove this function and implement tests """
        raise NotImplementedError("no tests implemented yet")
    

if __name__ == "__main__":
    # run the tests for this module if invoked directly
    unittest.main(verbosity=2)
