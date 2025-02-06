"""
lipidimea/test/msms/params.py
Dylan Ross (dylan.ross@pnnl.gov)

    tests for the lipidimea/params.py module
"""


import unittest
import os
from tempfile import TemporaryDirectory

from lipidimea.params import (
    DdaParams
)
    

class TestDdaParams(unittest.TestCase):
    """ tests for the tcdr.slim.params module """

    def test_default_config_findable(self):
        """ ensure the built in default config file can be found """
        self.assertTrue(os.path.isfile(_DEFAULT_CONFIG), 
                        f"could not find default config: {_DEFAULT_CONFIG}")

    def test_load_default_params(self):
        """ test that the SlimParams.load_default() staticmethod works """
        # expect no errors
        params = SlimParams.load_default()
        # TODO: More validation of loaded parameters.

    def test_load_bad_configs(self):
        """ test loading bad parameter config files """
        # --- ensure the config files exist first
        for config_file in [_BAD_CONFIG_1, _BAD_CONFIG_2]:
            self.assertTrue(os.path.isfile(config_file),
                            f"could not find test config file: {config_file}")
        # --- Bad config file 1
        with self.assertRaises(ValueError, 
                               msg="bad config (1) should have caused a ValueError"):
            params = SlimParams.from_config(_BAD_CONFIG_1)
        # --- Bad config file 2
        with self.assertRaises(ValueError, 
                               msg="bad config (2) should have caused a ValueError"):
            params = SlimParams.from_config(_BAD_CONFIG_2)

    def test_load_good_configs(self):
        """ test loading good parameter config files """
        # --- ensure the config files exist first
        for config_file in [_GOOD_CONFIG, _GOOD_CONFIG_EMPTY]:
            self.assertTrue(os.path.isfile(config_file),
                            f"could not find test config file: {config_file}")
        # --- Good config file
        # expect no errors loading it
        params = SlimParams.from_config(_GOOD_CONFIG)
        # check some values (by comparing to default)
        default = SlimParams.load_default()
        self.assertNotEqual(params.orbi.select_dda_scans.tol.mz, 
                            default.orbi.select_dda_scans.tol.mz,
                            "orbi.select_dda_scans.tol.mz should be updated")
        self.assertEqual(params.common.imms_feature_extraction.merge_features_tol.ccs, 
                         default.common.imms_feature_extraction.merge_features_tol.ccs,
                         "common.imms_feature_extraction.merge_features_tol.ccs should be unchanged")
        self.assertNotEqual(params.common.imms_feature_extraction.merge_features_tol.mz, 
                            default.common.imms_feature_extraction.merge_features_tol.mz,
                            "common.imms_feature_extraction.merge_features_tol.mz should be updated")
        # --- Good config file (empty) 
        # expect no errors loading it
        params = SlimParams.from_config(_GOOD_CONFIG_EMPTY)
        # check all values are unchanged
        self.assertEqual(params, 
                         SlimParams.load_default(),
                         "empty config file should reproduce the default parameters")
        
    def test_round_trip_with_default_params(self):
        """ load the default parameters, write to file, reload and make sure they did not change """
        # test with include_unchanged flag set to False
        with tempfile.NamedTemporaryFile(delete_on_close=False) as ntf:
            default = SlimParams.load_default()
            default.write_config(ntf.name)
            self.assertEqual(default, 
                             SlimParams.from_config(ntf.name),
                             "(1) parameters should not have changed between writing and reading config")
        # test with include_unchanged flag set to True
        with tempfile.NamedTemporaryFile(delete_on_close=False) as ntf:
            default = SlimParams.load_default()
            default.write_config(ntf.name, include_unchanged=True)
            self.assertEqual(default, 
                             SlimParams.from_config(ntf.name),
                             "(2) parameters should not have changed between writing and reading config")
    
    def test_round_trip_with_updated_params(self):
        """ load the default parameters, write to file, reload and make sure they did not change """
        # test with include_unchanged flag set to False
        with tempfile.NamedTemporaryFile(delete_on_close=False) as ntf:
            updated = SlimParams.load_default()
            updated.common.imms_feature_extraction.merge_features = False
            updated.orbi.select_dda_scans.tol.mz = 0.25
            updated.write_config(ntf.name)
            self.assertEqual(updated, 
                             SlimParams.from_config(ntf.name),
                             "(1) parameters should not have changed between writing and reading config")
        # test with include_unchanged flag set to True
        with tempfile.NamedTemporaryFile(delete_on_close=False) as ntf:
            updated = SlimParams.load_default()
            updated.common.imms_feature_extraction.merge_features = False
            updated.orbi.select_dda_scans.tol.mz = 0.25
            updated.write_config(ntf.name, include_unchanged=True)
            self.assertEqual(updated, 
                             SlimParams.from_config(ntf.name),
                             "(2) parameters should not have changed between writing and reading config")


# group all of the tests from this module into a TestSuite
_loader = unittest.TestLoader()
AllTestsParams = unittest.TestSuite()
AllTestsParams.addTests([
    _loader.loadTestsFromTestCase(TestDdaParams)
])


if __name__ == '__main__':
    # run all defined TestCases for only this module if invoked directly
    unittest.TextTestRunner(verbosity=2).run(AllTestsParams)



