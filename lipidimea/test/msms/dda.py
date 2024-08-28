"""
lipidimea/test/msms/dda.py

Dylan Ross (dylan.ross@pnnl.gov)

    tests for the lipidimea/msms/dda.py module
"""


import unittest
from unittest.mock import patch, PropertyMock
from tempfile import TemporaryDirectory
import os
import sqlite3

import numpy as np
from mzapy.peaks import _gauss

from lipidimea.msms.dda import (
    _MSMSReaderDDA, _MSMSReaderDDA_Cached, _extract_and_fit_chroms, _consolidate_chrom_feats,
    _extract_and_fit_ms2_spectra, _add_precursors_and_fragments_to_db, extract_dda_features, 
    consolidate_dda_features
)
from lipidimea.msms._util import ms2_to_str, str_to_ms2
from lipidimea.util import create_results_db
from lipidimea.params import (
    DdaExtractAndFitChromsParams, DdaConsolidateChromFeatsParams, DdaExtractAndFitMs2SpectraParams,
    DdaConsolidateFeaturesParams, DdaParams
)


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


# set some parameters for testing the different DDA data processing steps
_EAFC_PARAMS = DdaExtractAndFitChromsParams(
    20, 0.33, 1e4, 0.1, 0.5, 2, 5
)

_CCF_PARAMS = DdaConsolidateChromFeatsParams(
    20, 0.1
)

_EAFMS2_PARAMS = DdaExtractAndFitMs2SpectraParams(
    40, 50, 0.05, 0.3, 1e4, 0.025, 0.25, 0.1
)

_CDF_PARAMS = DdaConsolidateFeaturesParams(
    20, 0.1, False
)

_DDA_PARAMS = DdaParams(
    300.,
    1000.,
    _EAFC_PARAMS, 
    _CCF_PARAMS, 
    _EAFMS2_PARAMS, 
    _CDF_PARAMS
)


class Test_MSMSReaderDDA(unittest.TestCase):
    """ tests for the _MSMSReaderDDA class """

    def test_NO_TESTS_IMPLEMENTED_YET(self):
        """ placeholder, remove this function and implement tests """
        self.assertTrue(False, "no tests implemented yet")


class Test_MSMSReaderDDACached(unittest.TestCase):
    """ tests for the _MSMSReaderDDA_Cached class """

    def test_NO_TESTS_IMPLEMENTED_YET(self):
        """ placeholder, remove this function and implement tests """
        self.assertTrue(False, "no tests implemented yet")


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
            features = _extract_and_fit_chroms(rdr, {789.0123}, _EAFC_PARAMS,
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
        xic_iis += _gauss(xic_rts, 14.25, 5e4, 0.4) * noise2
        # expected feature parameters
        expected_features = [
            (789.0123, 15., 1e5, 0.25, 15.6),
            (789.0123, 14.25, 5e4, 0.4, 5),
        ]
        # mock a _MSMSReaderDDA instance with get_chrom method that returns the fake XIC 
        with patch('lipidimea.msms.dda._MSMSReaderDDA') as MockReader:
            rdr = MockReader.return_value
            rdr.get_chrom.return_value = (xic_rts, xic_iis)
            # use a helper callback function to store instead of printing debugging messages
            global _DEBUG_MSGS
            _DEBUG_MSGS = []
            # test the function
            features = _extract_and_fit_chroms(rdr, {789.0123}, _EAFC_PARAMS,
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
            (700.0001, 10.01, 1e4, 0.25, 10.),
            (700.0002, 10.02, 1e4, 0.25, 10.),
            (700.0003, 10.03, 1e5, 0.25, 10.),  # this should be the only retained feature
            (700.0004, 10.04, 1e4, 0.25, 10.),
            (700.0005, 10.05, 1e4, 0.25, 10.),
            # this feature stays because the RT is different from the group above
            (700.0003, 11., 1e5, 0.25, 10.),
            # this feature has a different enough m/z to to not be combined
            (700.1003, 10.03, 1e5, 0.25, 10.),
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
        cons_features = _consolidate_chrom_feats(features, _CCF_PARAMS, 
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
            (789.0123, 10.03, 1e5, 0.25, 10.),
        ]
        # mock a _MSMSReaderDDA instance with get_msms_spectrum method that returns the fake spectrum
        with patch('lipidimea.msms.dda._MSMSReaderDDA') as MockReader:
            rdr = MockReader.return_value
            rdr.get_msms_spectrum.return_value = (ms2_mzs, ms2_iis, 3, [789.0123, 789.0123, 789.0123])
            # use a helper callback function to store instead of printing debugging messages
            global _DEBUG_MSGS
            _DEBUG_MSGS = []
            # test the function
            precursors, spectra = _extract_and_fit_ms2_spectra(rdr, 69, cons_feats, _EAFMS2_PARAMS, 
                                                               debug_flag="textcb", debug_cb=_debug_cb)
            # there should be no features found in this spectrum, it is just flat noise
            # but there will still be qdata with the chromatographic feature
            self.assertListEqual(precursors, [(None, 69, 789.0123, 10.03, 0.25, 100000.0, 10, 3, 0)],
                                 msg="incorrect precursors returned")
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
        pkmzs = np.arange(100, 800, 25, dtype=np.float64)
        for pkmz in pkmzs:
            ms2_iis += _gauss(ms2_mzs, pkmz, 1e5, 0.1) * noise2 
        # expected query data generated from extracting and fitting MS2 spectrum
        expected_precursors = (
            (None, 69, 789.0123, 10.03, 0.25, 1e5, 10, 3, 28)
        )
        # consolidated features
        cons_feats = [
            (789.0123, 10.03, 1e5, 0.25, 10.),
        ]
        # mock a _MSMSReaderDDA instance with get_msms_spectrum method that returns the fake spectrum
        with patch('lipidimea.msms.dda._MSMSReaderDDA') as MockReader:
            rdr = MockReader.return_value
            rdr.get_msms_spectrum.return_value = (ms2_mzs, ms2_iis, 3, [789.0123, 789.0123, 789.0123])
            # use a helper callback function to store instead of printing debugging messages
            global _DEBUG_MSGS
            _DEBUG_MSGS = []
            # test the function
            precursors, spectra = _extract_and_fit_ms2_spectra(rdr, 69, cons_feats, _EAFMS2_PARAMS,
                                                               debug_flag="textcb", debug_cb=_debug_cb)
            # check the returned qdata values
            qid, qf, qmz, qrt, qwt, qht, qsnr, qnscans, qmzpeaks = precursors[0]
            eid, ef, emz, ert, ewt, eht, esnr, enscans, emzpeaks = expected_precursors
            self.assertEqual(qid, eid)
            self.assertEqual(qf, ef)
            self.assertAlmostEqual(qmz, emz, places=4)
            self.assertAlmostEqual(qrt, ert, places=2)
            self.assertAlmostEqual(qwt, ewt, places=2)
            self.assertLess(abs(qht - eht) / eht, 0.1)
            self.assertAlmostEqual(qsnr, esnr, places=0)
            self.assertEqual(qnscans, enscans)
            self.assertEqual(qmzpeaks, emzpeaks)
            # TODO: check on the returned spectra
            #for qpmz, qpi, epmz, epi in zip(*qpeak_arrays, *epeak_arrays):
            #    self.assertAlmostEqual(qpmz, epmz, places=1)
            #    self.assertLess(abs(qpi - epi) / epi, 0.3)
            # make sure that the correct number of debugging messages were generated
            self.assertEqual(len(_DEBUG_MSGS), 3)
            # check for debug message with number of MS2 peaks found
            self.assertIn("# MS2 peaks: 28", _DEBUG_MSGS[1])


class Test_AddPrecursorsAndFragmentsToDb(unittest.TestCase):
    """ 
        tests for the _add_precursors_to_db function, 
        cover all cases that can be generated by 
        _extract_and_fit_ms2_spectra 
    """

    def test_APAFTD_qdata_full(self):
        """ test adding complete qdata to DB """
        # query data
        precursors = [
            (None, 69, 789.0123, 12.34, 0.12, 1.23e4, 10., 3, 3),
        ]
        spectra = [
            np.array([[123.456, 234.567, 345.678], [1e3, 2e3, 3e3]]),
        ]
        # use a helper callback function to store instead of printing debugging messages
        _DEBUG_MSGS = []
        with TemporaryDirectory() as tmp_dir:
            dbf = os.path.join(tmp_dir, "results.db")
            create_results_db(dbf)  # STRICT!
            con = sqlite3.connect(dbf)
            cur = con.cursor()
            # test the function
            _add_precursors_and_fragments_to_db(cur, precursors, spectra, 
                                                debug_flag="textcb", debug_cb=_debug_cb)
            # make sure values in = values out 
            # exept for the first value which is an ID 
            # that is generated when the data gets inserted
            _, *values_in = precursors[0]
            _, *values_out = cur.execute("SELECT * FROM DDAPrecursors;").fetchall()[0]
            self.assertListEqual(values_in, values_out)

    def test_APAFTD_qdata_zero_mzpeaks_null_spectrum(self):
        """ test adding qdata with null spectrum to the DB """
        # query data
        precursors = [
            (None, 69, 789.0123, 12.34, 0.12, 1.23e4, 10., 3, 0),
        ]
        spectra = [
            None,
        ]
        # use a helper callback function to store instead of printing debugging messages
        global _DEBUG_MSGS
        _DEBUG_MSGS = []
        with TemporaryDirectory() as tmp_dir:
            dbf = os.path.join(tmp_dir, "results.db")
            create_results_db(dbf)  # STRICT!
            con = sqlite3.connect(dbf)
            cur = con.cursor()
            # test the function
            _add_precursors_and_fragments_to_db(cur, precursors, spectra,
                                                debug_flag="textcb", debug_cb=_debug_cb)
            # make sure values in = values out 
            # exept for the first value which is an ID 
            # that is generated when the data gets inserted
            _, *values_in = precursors[0]
            _, *values_out = cur.execute("SELECT * FROM DDAPrecursors;").fetchall()[0]
            self.assertListEqual(values_in, values_out)
    
    def test_APAFTD_null_mzpeaks_null_spectrum(self):
        """ test adding qdata with null mz peaks count and no spectrum """
        # query data
        precursors = [
            (None, 69, 789.0123, 12.34, 0.12, 1.23e4, 10., 3, None),
        ]
        spectra = [
            None,
        ]
        # use a helper callback function to store instead of printing debugging messages
        global _DEBUG_MSGS
        _DEBUG_MSGS = []
        with TemporaryDirectory() as tmp_dir:
            dbf = os.path.join(tmp_dir, "results.db")
            create_results_db(dbf)  # STRICT!
            con = sqlite3.connect(dbf)
            cur = con.cursor()
            # test the function
            _add_precursors_and_fragments_to_db(cur, precursors, spectra,
                                                debug_flag="textcb", debug_cb=_debug_cb)
            # make sure values in = values out 
            # exept for the first value which is an ID 
            # that is generated when the data gets inserted
            _, *values_in = precursors[0]
            _, *values_out = cur.execute("SELECT * FROM DDAPrecursors;").fetchall()[0]
            self.assertListEqual(values_in, values_out)


class TestExtractDdaFeatures(unittest.TestCase):
    """ tests for the extract_dda_features function """

    # TODO (Dylan Ross): Add a method to test cases where dda_data_file is provided as a path, an 
    #                    integer file ID, or some invalid value.

    def test_EDF_with_peaks(self):
        """ test extracting DDA features from mock data with peaks """
        # make a fake XIC with two peaks
        np.random.seed(420)
        xic_rts = np.arange(0, 20.05, 0.01)
        noise1 = np.random.normal(1, 0.2, size=xic_rts.shape)
        noise2 = np.random.normal(1, 0.1, size=xic_rts.shape)
        xic_iis = 1000 * noise1 
        xic_iis += _gauss(xic_rts, 15, 1e5, 0.25) * noise2 
        xic_iis += _gauss(xic_rts, 14.25, 5e4, 0.4) * noise2
        # make a fake spectrum with peaks
        ms2_mzs = np.arange(50, 800, 0.01)
        noise1 = np.random.normal(1, 0.2, size=ms2_mzs.shape)
        ms2_iis = 1000 * noise1 
        noise2 = np.random.normal(1, 0.1, size=ms2_mzs.shape)
        pkmzs = np.arange(100, 800, 25)
        for pkmz in pkmzs:
            ms2_iis += _gauss(ms2_mzs, pkmz, 1e5, 0.1) * noise2 
        # need to temporarily create a results database and patch a mock _MSMSReaderDDA 
        with TemporaryDirectory() as tmp_dir, patch('lipidimea.msms.dda._MSMSReaderDDA') as MockReader:
            dbf = os.path.join(tmp_dir, "results.db")
            create_results_db(dbf)  # STRICT!
            con = sqlite3.connect(dbf)
            cur = con.cursor()
            # mock a _MSMSReaderDDA instance with 
            # get_pre_mzs method that returns {789.0123}
            # get_chrom method that returns a fake XIC 
            # get_msms_spectrum method that returns a fake spectrum
            # f property that returns "data.file"
            rdr = MockReader.return_value
            type(rdr).f = PropertyMock(return_value="data.file")
            rdr.get_pre_mzs.return_value = {789.0123}
            rdr.get_chrom.return_value = (xic_rts, xic_iis)
            rdr.get_msms_spectrum.return_value = (ms2_mzs, ms2_iis, 1, [789.0123])
            # use a helper callback function to store instead of printing debugging messages
            global _DEBUG_MSGS
            _DEBUG_MSGS = []
            # test the function
            n = extract_dda_features("data.file", dbf, _DDA_PARAMS, 
                                     cache_ms1=False, debug_flag="textcb", debug_cb=_debug_cb)
            # make sure that the correct number of debugging messages were generated
            self.assertEqual(len(_DEBUG_MSGS), 13)
            # fetch the features from the database, there should be 2
            self.assertEqual(len(cur.execute("SELECT * FROM DDAPrecursors;").fetchall()), 2,
                             msg="there should be 2 DDA features in the database")
            # make sure the correct number of DDA features is returned from the function
            self.assertEqual(n, 2,
                             msg="should have gotten 2 for number of features extracted")


# NOTE (Dylan Ross): removed the unit test for extract_dda_features_multiproc as mocking does 
#                    not work well with multiprocessing. The actual business logic function is 
#                    fully tested and the logic of applying it in a multiprocessing context via 
#                    starmap is small and straightforward so should be able to trust it well 
#                    enough without the unit test


class TestConsolidateDdaFeatures(unittest.TestCase):
    """ tests for the consolidate_dda_features function """

    def test_CDF_multiple_cases(self):
        """ covers multiple cases of DDA features that should or should not be combined """
        # query data to fill the database with
        precursors = [
            # only the 3rd from this group is kept because it has the highest intensity
            (None, 69, 789.0123, 12.34, 0.12, 1.23e4, 10., 0, None),
            (None, 69, 789.0123, 12.34, 0.12, 2.34e4, 10., 0, None),
            (None, 69, 789.0123, 12.34, 0.12, 3.45e4, 10., 0, None),
            # different m/z so different group
            # second is kept because it has a spectrum
            # even though the others have higher intensity
            (None, 69, 799.0123, 12.34, 0.12, 2.34e4, 10., 0, None),
            (None, 69, 799.0123, 12.34, 0.12, 1.23e4, 10., 3, 3),
            (None, 69, 799.0123, 12.34, 0.12, 2.34e4, 10., 0, None),
            # different m/z so different group
            # first and second are kept because they have spectra
            # even though the third has higher intensity
            (None, 69, 709.0123, 12.34, 0.12, 1.99e4, 10., 1, 0),  # has a spectrum but no peaks
            (None, 69, 709.0123, 12.34, 0.12, 1.23e4, 10., 3, 3),
            (None, 69, 709.0123, 12.34, 0.12, 2.34e4, 10., 0, None),
        ]
        spectra = [
            None,
            None,
            None,
            None,
            np.array([[123.456, 234.567, 345.678], [1e3, 2e3, 3e3]]),
            None,
            None,
            np.array([[123.456, 234.567, 345.678], [1e3, 2e3, 3e3]]),
            None,
        ]
        expected = [
            (None, 69, 789.0123, 12.34, 0.12, 3.45e4, 10., 0, None),
            (None, 69, 799.0123, 12.34, 0.12, 1.23e4, 10., 3, 3),
            (None, 69, 709.0123, 12.34, 0.12, 1.99e4, 10., 1, 0),
            (None, 69, 709.0123, 12.34, 0.12, 1.23e4, 10., 3, 3),
        ]
        # use a helper callback function to store instead of printing debugging messages
        _DEBUG_MSGS = []
        with TemporaryDirectory() as tmp_dir:
            dbf = os.path.join(tmp_dir, "results.db")
            create_results_db(dbf)  # STRICT!
            con = sqlite3.connect(dbf)
            cur = con.cursor()
            # fill the db with the features
            # set debug_flag and debug_cb to None
            # so we do not capture debug messages from this step
            _add_precursors_and_fragments_to_db(cur, precursors, spectra, None, None)  
            # write changes to the db
            con.commit()
            # test the function
            n_pre, n_post = consolidate_dda_features(dbf, _DDA_PARAMS.consolidate_dda_features_params, 
                                                     debug_flag="text_cb", debug_cb=_debug_cb)
            # make sure number of features pre/post is correct
            self.assertEqual(n_pre, 9,
                             msg="number of feature before consolidation should be 9")
            self.assertEqual(n_post, 4,
                             msg="number of feature after consolidation should be 4")
            # make sure values in = values out 
            # exept for the first value which is an ID 
            # that is generated when the data gets inserted
            for exp, obs in zip(expected, cur.execute("SELECT * FROM DDAPrecursors;").fetchall()):
                _, *a = exp
                _, *b = obs
                self.assertListEqual(a, b)


if __name__ == "__main__":
    # run the tests for this module if invoked directly
    unittest.main(verbosity=2)
