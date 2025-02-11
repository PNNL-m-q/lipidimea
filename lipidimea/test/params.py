"""
lipidimea/test/params.py
Dylan Ross (dylan.ross@pnnl.gov)

    tests for the lipidimea/params.py module
"""


import unittest
import os
import tempfile

from lipidimea.test.__include import TEST_INCLUDE_DIR
from lipidimea.params import (
    _DEFAULT_DDA_CONFIG,
    DdaParams, 
    _DEFAULT_DIA_CONFIG,
    DiaParams,
    _DEFAULT_ANN_CONFIG,
    AnnotationParams
)


# define paths to test config files
_GOOD_CONFIG_EMPTY = os.path.join(TEST_INCLUDE_DIR, "good_config_empty.yaml")
_BAD_DDA_CONFIG_1 = os.path.join(TEST_INCLUDE_DIR, "bad_dda_config_1.yaml")
_BAD_DDA_CONFIG_2 = os.path.join(TEST_INCLUDE_DIR, "bad_dda_config_2.yaml")
_GOOD_DDA_CONFIG = os.path.join(TEST_INCLUDE_DIR, "good_dda_config.yaml")
_BAD_DIA_CONFIG_1 = os.path.join(TEST_INCLUDE_DIR, "bad_dia_config_1.yaml")
_BAD_DIA_CONFIG_2 = os.path.join(TEST_INCLUDE_DIR, "bad_dia_config_2.yaml")
_GOOD_DIA_CONFIG = os.path.join(TEST_INCLUDE_DIR, "good_dia_config.yaml")
_BAD_ANN_CONFIG = os.path.join(TEST_INCLUDE_DIR, "bad_ann_config.yaml")
_GOOD_ANN_CONFIG = os.path.join(TEST_INCLUDE_DIR, "good_ann_config.yaml")


class TestDdaParams(unittest.TestCase):
    """ tests for the DdaParams class """

    def test_default_config_findable(self):
        """ ensure the built in default config file can be found """
        self.assertTrue(os.path.isfile(_DEFAULT_DDA_CONFIG), 
                        f"could not find default DDA config: {_DEFAULT_DDA_CONFIG}")

    def test_load_default_params(self):
        """ test that the loading default parameters works """
        # expect no errors
        params = DdaParams.load_default()
        # TODO: More validation of loaded parameters.

    def test_load_bad_configs(self):
        """ test loading bad parameter config files """
        # --- ensure the config files exist first
        for config_file in [_BAD_DDA_CONFIG_1, _BAD_DDA_CONFIG_2]:
            self.assertTrue(os.path.isfile(config_file),
                            f"could not find test DDA config file: {config_file}")
        # --- Bad config file 1
        with self.assertRaises(ValueError, 
                               msg="bad config (1) should have caused a ValueError"):
            params = DdaParams.from_config(_BAD_DDA_CONFIG_1)
        # --- Bad config file 2
        with self.assertRaises(ValueError, 
                               msg="bad config (2) should have caused a ValueError"):
            params = DdaParams.from_config(_BAD_DDA_CONFIG_2)

    def test_load_good_configs(self):
        """ test loading good parameter config files """
        # --- ensure the config files exist first
        for config_file in [_GOOD_DDA_CONFIG, _GOOD_CONFIG_EMPTY]:
            self.assertTrue(os.path.isfile(config_file),
                            f"could not find test config file: {config_file}")
        # --- Good config file
        # expect no errors loading it
        params = DdaParams.from_config(_GOOD_DDA_CONFIG) 
        # check some values (by comparing to default)
        default = DdaParams.load_default() 
        self.assertNotEqual(params.extract_and_fit_chroms.fwhm.max, 
                            default.extract_and_fit_chroms.fwhm.max,
                            "extract_and_fit_chroms.fwhm.max should be updated")
        self.assertEqual(params.extract_and_fit_ms2_spectra.peak_min_dist, 
                         default.extract_and_fit_ms2_spectra.peak_min_dist,
                         "extract_and_fit_ms2_spectra.peak_min_dist should be unchanged")
        self.assertNotEqual(params.extract_and_fit_ms2_spectra.mz_bin_min, 
                            default.extract_and_fit_ms2_spectra.mz_bin_min,
                            "extract_and_fit_ms2_spectra.mz_bin_min should be updated")
        # --- Good config file (empty) 
        # expect no errors loading it
        params = DdaParams.from_config(_GOOD_CONFIG_EMPTY)  
        # check all values are unchanged
        self.assertEqual(params, 
                         DdaParams.load_default(),
                         "empty config file should reproduce the default parameters")
        
    def test_round_trip_with_default_params(self):
        """ load the default parameters, write to file, reload and make sure they did not change """
        # test with include_unchanged flag set to False
        with tempfile.NamedTemporaryFile(delete_on_close=False) as ntf:
            default = DdaParams.load_default() 
            default.write_config(ntf.name)
            self.assertEqual(default, 
                             DdaParams.from_config(ntf.name),
                             "(1) parameters should not have changed between writing and reading config")
        # test with include_unchanged flag set to True
        with tempfile.NamedTemporaryFile(delete_on_close=False) as ntf:
            default = DdaParams.load_default()  
            default.write_config(ntf.name, include_unchanged=True)
            self.assertEqual(default, 
                             DdaParams.from_config(ntf.name),
                             "(2) parameters should not have changed between writing and reading config")
    
    def test_round_trip_with_updated_params(self):
        """ load the default parameters, write to file, reload and make sure they did not change """
        # test with include_unchanged flag set to False
        with tempfile.NamedTemporaryFile(delete_on_close=False) as ntf:
            updated = DdaParams.load_default() 
            updated.extract_and_fit_chroms.fwhm.max = 420.
            updated.extract_and_fit_ms2_spectra.peak_min_dist = 69.
            updated.write_config(ntf.name)
            self.assertEqual(updated, 
                             DdaParams.from_config(ntf.name),
                             "(1) parameters should not have changed between writing and reading config")
        # test with include_unchanged flag set to True
        with tempfile.NamedTemporaryFile(delete_on_close=False) as ntf:
            updated = DdaParams.load_default() 
            updated.extract_and_fit_chroms.fwhm.max = 420.
            updated.extract_and_fit_ms2_spectra.peak_min_dist = 69.
            updated.write_config(ntf.name, include_unchanged=True)
            self.assertEqual(updated, 
                             DdaParams.from_config(ntf.name),
                             "(2) parameters should not have changed between writing and reading config")
            

class TestDiaParams(unittest.TestCase):
    """ tests for the DiaParams class """

    def test_default_config_findable(self):
        """ ensure the built in default config file can be found """
        self.assertTrue(os.path.isfile(_DEFAULT_DIA_CONFIG), 
                        f"could not find default DIA config: {_DEFAULT_DIA_CONFIG}")

    def test_load_default_params(self):
        """ test that the loading default parameters works """
        # expect no errors
        params = DiaParams.load_default()
        # TODO: More validation of loaded parameters.

    def test_load_bad_configs(self):
        """ test loading bad parameter config files """
        # --- ensure the config files exist first
        for config_file in [_BAD_DIA_CONFIG_1, _BAD_DIA_CONFIG_2]:
            self.assertTrue(os.path.isfile(config_file),
                            f"could not find test DDA config file: {config_file}")
        # --- Bad config file 1
        with self.assertRaises(ValueError, 
                               msg="bad config (1) should have caused a ValueError"):
            params = DiaParams.from_config(_BAD_DIA_CONFIG_1)
        # --- Bad config file 2
        with self.assertRaises(ValueError, 
                               msg="bad config (2) should have caused a ValueError"):
            params = DiaParams.from_config(_BAD_DIA_CONFIG_2)

    def test_load_good_configs(self):
        """ test loading good parameter config files """
        # --- ensure the config files exist first
        for config_file in [_GOOD_DIA_CONFIG, _GOOD_CONFIG_EMPTY]:
            self.assertTrue(os.path.isfile(config_file),
                            f"could not find test config file: {config_file}")
        # --- Good config file
        # expect no errors loading it
        params = DiaParams.from_config(_GOOD_DIA_CONFIG) 
        # check some values (by comparing to default)
        default = DiaParams.load_default() 
        self.assertNotEqual(params.extract_and_fit_chroms.fwhm.max, 
                            default.extract_and_fit_chroms.fwhm.max,
                            "extract_and_fit_chroms.fwhm.max should be updated")
        self.assertEqual(params.extract_and_fit_ms2_spectra.peak_min_dist, 
                         default.extract_and_fit_ms2_spectra.peak_min_dist,
                         "extract_and_fit_ms2_spectra.peak_min_dist should be unchanged")
        self.assertNotEqual(params.extract_and_fit_ms2_spectra.mz_bin_min, 
                            default.extract_and_fit_ms2_spectra.mz_bin_min,
                            "extract_and_fit_ms2_spectra.mz_bin_min should be updated")
        # --- Good config file (empty) 
        # expect no errors loading it
        params = DiaParams.from_config(_GOOD_CONFIG_EMPTY)  
        # check all values are unchanged
        self.assertEqual(params, 
                         DiaParams.load_default(),
                         "empty config file should reproduce the default parameters")
        
    def test_round_trip_with_default_params(self):
        """ load the default parameters, write to file, reload and make sure they did not change """
        # test with include_unchanged flag set to False
        with tempfile.NamedTemporaryFile(delete_on_close=False) as ntf:
            default = DiaParams.load_default() 
            default.write_config(ntf.name)
            self.assertEqual(default, 
                             DiaParams.from_config(ntf.name),
                             "(1) parameters should not have changed between writing and reading config")
        # test with include_unchanged flag set to True
        with tempfile.NamedTemporaryFile(delete_on_close=False) as ntf:
            default = DiaParams.load_default()  
            default.write_config(ntf.name, include_unchanged=True)
            self.assertEqual(default, 
                             DiaParams.from_config(ntf.name),
                             "(2) parameters should not have changed between writing and reading config")
    
    def test_round_trip_with_updated_params(self):
        """ load the default parameters, write to file, reload and make sure they did not change """
        # test with include_unchanged flag set to False
        with tempfile.NamedTemporaryFile(delete_on_close=False) as ntf:
            updated = DiaParams.load_default() 
            updated.extract_and_fit_chroms.fwhm.max = 420.
            updated.extract_and_fit_ms2_spectra.peak_min_dist = 69.
            updated.write_config(ntf.name)
            self.assertEqual(updated, 
                             DiaParams.from_config(ntf.name),
                             "(1) parameters should not have changed between writing and reading config")
        # test with include_unchanged flag set to True
        with tempfile.NamedTemporaryFile(delete_on_close=False) as ntf:
            updated = DiaParams.load_default() 
            updated.extract_and_fit_chroms.fwhm.max = 420.
            updated.extract_and_fit_ms2_spectra.peak_min_dist = 69.
            updated.write_config(ntf.name, include_unchanged=True)
            self.assertEqual(updated, 
                             DiaParams.from_config(ntf.name),
                             "(2) parameters should not have changed between writing and reading config")


class TestAnnotationParams(unittest.TestCase):
    """ tests for the AnnotationParams class """

    def test_default_config_findable(self):
        """ ensure the built in default config file can be found """
        self.assertTrue(os.path.isfile(_DEFAULT_ANN_CONFIG), 
                        f"could not find default DDA config: {_DEFAULT_ANN_CONFIG}")

    def test_load_default_params(self):
        """ test that the loading default parameters works """
        # expect no errors
        params = AnnotationParams.load_default()
        # TODO: More validation of loaded parameters.

    def test_load_bad_configs(self):
        """ test loading bad parameter config files """
        # --- ensure the config file exists first
        self.assertTrue(os.path.isfile(_BAD_ANN_CONFIG),
                        f"could not find test DDA config file: {_BAD_ANN_CONFIG}")
        # --- Bad config file
        with self.assertRaises(ValueError, 
                               msg="bad config (1) should have caused a ValueError"):
            params = AnnotationParams.from_config(_BAD_ANN_CONFIG)
       
    def test_load_good_configs(self):
        """ test loading good parameter config files """
        # --- ensure the config files exist first
        for config_file in [_GOOD_ANN_CONFIG, _GOOD_CONFIG_EMPTY]:
            self.assertTrue(os.path.isfile(config_file),
                            f"could not find test config file: {config_file}")
        # --- Good config file
        # expect no errors loading it
        params = AnnotationParams.from_config(_GOOD_ANN_CONFIG) 
        # check some values (by comparing to default)
        default = AnnotationParams.load_default() 
        self.assertNotEqual(params.sum_comp.fa_c.min, 
                            default.sum_comp.fa_c.min,
                            "sum_comp.fa_c.min should be updated")
        self.assertEqual(params.frag_rules.fa_c.min, 
                         default.frag_rules.fa_c.min,
                         "frag_rules.fa_c.min should be unchanged")
        self.assertNotEqual(params.frag_rules.fa_c.max, 
                            default.frag_rules.fa_c.max,
                            "frag_rules.fa_c.max should be updated")
        # --- Good config file (empty) 
        # expect no errors loading it
        params = AnnotationParams.from_config(_GOOD_CONFIG_EMPTY)  
        # check all values are unchanged
        self.assertEqual(params, 
                         AnnotationParams.load_default(),
                         "empty config file should reproduce the default parameters")
        
    def test_round_trip_with_default_params(self):
        """ load the default parameters, write to file, reload and make sure they did not change """
        # test with include_unchanged flag set to False
        with tempfile.NamedTemporaryFile(delete_on_close=False) as ntf:
            default = AnnotationParams.load_default() 
            default.write_config(ntf.name)
            self.assertEqual(default, 
                             AnnotationParams.from_config(ntf.name),
                             "(1) parameters should not have changed between writing and reading config")
        # test with include_unchanged flag set to True
        with tempfile.NamedTemporaryFile(delete_on_close=False) as ntf:
            default = AnnotationParams.load_default()  
            default.write_config(ntf.name, include_unchanged=True)
            self.assertEqual(default, 
                             AnnotationParams.from_config(ntf.name),
                             "(2) parameters should not have changed between writing and reading config")
    
    def test_round_trip_with_updated_params(self):
        """ load the default parameters, write to file, reload and make sure they did not change """
        # test with include_unchanged flag set to False
        with tempfile.NamedTemporaryFile(delete_on_close=False) as ntf:
            updated = AnnotationParams.load_default() 
            updated.frag_rules.fa_c.min = 10
            updated.sum_comp.fa_odd_c = False
            updated.write_config(ntf.name)
            self.assertEqual(updated, 
                             AnnotationParams.from_config(ntf.name),
                             "(1) parameters should not have changed between writing and reading config")
        # test with include_unchanged flag set to True
        with tempfile.NamedTemporaryFile(delete_on_close=False) as ntf:
            updated = AnnotationParams.load_default() 
            updated.frag_rules.fa_c.min = 10
            updated.sum_comp.fa_odd_c = False
            updated.write_config(ntf.name, include_unchanged=True)
            self.assertEqual(updated, 
                             AnnotationParams.from_config(ntf.name),
                             "(2) parameters should not have changed between writing and reading config")


# group all of the tests from this module into a TestSuite
_loader = unittest.TestLoader()
AllTestsParams = unittest.TestSuite()
AllTestsParams.addTests([
    _loader.loadTestsFromTestCase(TestDdaParams),
    _loader.loadTestsFromTestCase(TestDiaParams),
    _loader.loadTestsFromTestCase(TestAnnotationParams)
])


if __name__ == '__main__':
    # run all defined TestCases for only this module if invoked directly
    unittest.TextTestRunner(verbosity=2).run(AllTestsParams)
