"""
lipidimea/test/msms/dda.py

Dylan Ross (dylan.ross@pnnl.gov)

    tests for the lipidimea/msms/dda.py module
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
from lipidimea.msms._util import ms2_to_str, str_to_ms2


# Multiple tests cover functions that use the debug handler so instead of 
# printing the debugging messages, use a callback function to store them
# in this list. Individual test functions should clear out this list before
# calling whatever function is being tested, then the list can be checked 
# for the expected debugging messages if needed
_DEBUG_MSGS = []


def _debug_cb(msg: str
              ) -> None :
    """ helper callback function for redirecting debugging messages """
    _DEBUG_MSGS.append(msg)


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
            global _DEBUG_MSGS
            _DEBUG_MSGS = []
            # test the function
            features = _extract_and_fit_chroms(rdr, {789.0123}, 
                                               20, 0.3, 1e3, 0.1, 1.0, 3, 4, 
                                               debug_flag="textcb", debug_cb=_debug_cb)
            # there should be no features found in this XIC, it is just flat noise
            self.assertListEqual(features, [],
                                 msg="the fake XIC is flat noise and should not have any peaks")
            # make sure that the correct number of debugging messages were generated
            self.assertEqual(len(_DEBUG_MSGS), 3)
            # check for debug message showing no peaks found
            self.assertIn("no peaks found", _DEBUG_MSGS[1])

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
            global _DEBUG_MSGS
            _DEBUG_MSGS = []
            # test the function
            features = _extract_and_fit_chroms(rdr, {789.0123}, 
                                               20, 0.3, 1e3, 0.1, 1.0, 3, 4, 
                                               debug_flag="textcb", debug_cb=_debug_cb)
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
            self.assertEqual(len(_DEBUG_MSGS), 4)
            # check for debug messages showing two found peaks
            self.assertIn("RT", _DEBUG_MSGS[1])
            self.assertIn("RT", _DEBUG_MSGS[2])


class Test_ConsolidateChromFeats(unittest.TestCase):
    """ tests for the _consolidate_chrom_feats function """

    def test_CCF_correct_features(self):
        """ consolidate some features and ensure the correct ones are consolidated """
        # define the input features
        features = [
            # this group should condense down to 1 feature
            (700.0001, 10.01, 1e4, 0.25, 10),
            (700.0002, 10.02, 1e4, 0.25, 10),
            (700.0003, 10.03, 1e5, 0.25, 10),  # this should be the only retained feature
            (700.0004, 10.04, 1e4, 0.25, 10),
            (700.0005, 10.05, 1e4, 0.25, 10),
            # this feature stays because the RT is different from the group above
            (700.0003, 11., 1e5, 0.25, 10),
            # this feature has a different enough m/z to to not be combined
            (700.1003, 10.03, 1e5, 0.25, 10),
        ]
        # expected consolidated features
        expected_features = [
            (700.0003, 10.03, 1e5, 0.25, 10),
            (700.0003, 11., 1e5, 0.25, 10),
            (700.1003, 10.03, 1e5, 0.25, 10),
        ]
        # use a helper callback function to store instead of printing debugging messages
        _DEBUG_MSGS = []
        # test the function
        cons_features = _consolidate_chrom_feats(features, 20, 0.1, 
                                                 debug_flag="textcb", debug_cb=_debug_cb)
        # ensure the correct features were consolidated
        self.assertEqual(len(cons_features), len(expected_features),
                         msg="number of consolidated features does not match expectation")
        for feat, exp_feat in zip(cons_features, expected_features):
            fmz, frt, fht, fwt, fsnr = feat
            efmz, efrt, efht, efwt, efsnr = exp_feat
            self.assertAlmostEqual(fmz, efmz, places=4)
            self.assertAlmostEqual(frt, efrt, places=2)
            self.assertLess(abs(fht - efht) / efht, 0.1)      


class Test_ExtractAndFitMs2Spectra(unittest.TestCase):
    """ tests for the _extract_and_fit_ms2_spectra function """

    def test_EAFMS2_spectrum_no_peaks(self):
        """ test extracting and fitting spectrum from noisy signal with no peaks in it """
        # make a fake XIC with no peaks
        np.random.seed(420)
        ms2_mzs = np.arange(50, 800, 0.01)
        noise1 = np.random.normal(1, 0.2, size=ms2_mzs.shape)
        ms2_iis = 1000 * noise1 
        # consolidated features
        cons_feats = [
            (789.0123, 10.03, 1e5, 0.25, 10),
        ]
        # mock a _MSMSReaderDDA instance with get_msms_spectrum method that returns the fake spectrum
        with patch('lipidimea.msms.dda._MSMSReaderDDA') as MockReader:
            rdr = MockReader.return_value
            rdr.f = "<filename>"
            rdr.get_msms_spectrum.return_value = (ms2_mzs, ms2_iis, 3, [789.0123, 789.0123, 789.0123])
            # use a helper callback function to store instead of printing debugging messages
            global _DEBUG_MSGS
            _DEBUG_MSGS = []
            # test the function
            qdata = _extract_and_fit_ms2_spectra(rdr, cons_feats, 40, 50, 0.05, 0.3, 1e4, 0.025, 0.25, 0.1, 
                                                 debug_flag="textcb", debug_cb=_debug_cb)
            # there should be no features found in this spectrum, it is just flat noise
            # but there will still be qdata with the chromatographic feature
            self.assertListEqual(qdata, [(None, '<filename>', 789.0123, 10.03, 0.25, 100000.0, 10, 3, 0, None)],
                                 msg="incorrect qdata returned")
            # make sure that the correct number of debugging messages were generated
            self.assertEqual(len(_DEBUG_MSGS), 3)
            # check for debug message showing no peaks found
            self.assertIn("# MS2 peaks: 0", _DEBUG_MSGS[1])

    def test_EAFM2S_spectrum_with_peaks(self):
        """ test extracting and fitting MS2 spectrum with peaks in it """
        # make a fake spectrum with peaks
        np.random.seed(420)
        ms2_mzs = np.arange(50, 800, 0.01)
        noise1 = np.random.normal(1, 0.2, size=ms2_mzs.shape)
        ms2_iis = 1000 * noise1 
        noise2 = np.random.normal(1, 0.1, size=ms2_mzs.shape)
        pkmzs = np.arange(100, 800, 25)
        for pkmz in pkmzs:
            ms2_iis += _gauss(ms2_mzs, pkmz, 1e5, 0.1) * noise2 
        # expected query data generated from extracting and fitting MS2 spectrum
        expected_qdata = (
            None, "<filename>", 789.0123, 10.03, 0.25, 1e5, 10, 3, 28, ms2_to_str(pkmzs, np.repeat(1e5, len(pkmzs)))
        )
        # consolidated features
        cons_feats = [
            (789.0123, 10.03, 1e5, 0.25, 10),
        ]
        # mock a _MSMSReaderDDA instance with get_msms_spectrum method that returns the fake spectrum
        with patch('lipidimea.msms.dda._MSMSReaderDDA') as MockReader:
            rdr = MockReader.return_value
            rdr.f = "<filename>"
            rdr.get_msms_spectrum.return_value = (ms2_mzs, ms2_iis, 3, [789.0123, 789.0123, 789.0123])
            # use a helper callback function to store instead of printing debugging messages
            global _DEBUG_MSGS
            _DEBUG_MSGS = []
            # test the function
            qdata = _extract_and_fit_ms2_spectra(rdr, cons_feats, 40, 50, 0.05, 0.3, 1e3, 0.025, 0.25, 0.1, 
                                                 debug_flag="textcb", debug_cb=_debug_cb)
            # check the returned qdata values
            qid, qf, qmz, qrt, qwt, qht, qsnr, qnscans, qmzpeaks, qspecstr = qdata[0]
            eid, ef, emz, ert, ewt, eht, esnr, enscans, emzpeaks, especstr = expected_qdata
            self.assertEqual(qid, eid)
            self.assertEqual(qf, ef)
            self.assertAlmostEqual(qmz, emz, places=4)
            self.assertAlmostEqual(qrt, ert, places=2)
            self.assertAlmostEqual(qwt, ewt, places=2)
            self.assertLess(abs(qht - eht) / eht, 0.1)
            self.assertAlmostEqual(qsnr, esnr, places=0)
            self.assertEqual(qnscans, enscans)
            self.assertEqual(qmzpeaks, emzpeaks)
            qpeak_arrays = str_to_ms2(qspecstr)
            epeak_arrays = str_to_ms2(especstr)
            for qpmz, qpi, epmz, epi in zip(*qpeak_arrays, *epeak_arrays):
                self.assertAlmostEqual(qpmz, epmz, places=1)
                self.assertLess(abs(qpi - epi) / epi, 0.3)
            # make sure that the correct number of debugging messages were generated
            self.assertEqual(len(_DEBUG_MSGS), 3)
            # check for debug message with number of MS2 peaks found
            self.assertIn("# MS2 peaks: 28", _DEBUG_MSGS[1])


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
