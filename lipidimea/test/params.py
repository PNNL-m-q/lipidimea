"""
lipidimea/test/msms/params.py

Dylan Ross (dylan.ross@pnnl.gov)

    tests for the lipidimea/params.py module
"""


import unittest
import os
from tempfile import TemporaryDirectory

from lipidimea.params import (
    DdaExtractAndFitChromsParams, DdaConsolidateChromFeatsParams, DdaExtractAndFitMs2SpectraParams,
    DdaConsolidateFeaturesParams, DdaParams,
    load_default_params, load_params, save_params
)
    

# class TestSomething(unittest.TestCase):
#     """ tests for the ? """

#     def test_something(self):
#         """ test ? """
#         params = DdaParams(
#             ExtractAndFitChromsParams(
#                 20, 0.33, 1e4, 0.1, 0.3, 2, 10
#             ), 
#             ConsolidateChromFeatsParams(
#                 20, 0.1
#             ), 
#             ExtractAndFitMS2SpectraParams(
#                 20, 50, 0.05, 0.33, 1e4, 0.1, 0.3, 0.1
#             )
#         )
#         print(params)

    
#     #def test_NO_TESTS_IMPLEMENTED_YET(self):
#     #    """ placeholder, remove this function and implement tests """
#     #    self.assertTrue(False, "no tests implemented yet")
    

class TestLoadDefaultParams(unittest.TestCase):
    """ tests for load_default_params function """

    def test_LDP_no_errs(self):
        """ run load_default_params and there should be no errors """
        params = load_default_params()

    def test_LDP_default_params_top_level_sections(self):
        """ load default parameters and make sure top level sections are present and not empty """
        params = load_default_params()
        for top_lvl_section in ['dda', 'dia', 'annotation', 'misc']:
            self.assertIn(top_lvl_section, params.keys(), 
                          msg=f"top level section '{top_lvl_section}' should have been in default params")
            self.assertNotEqual(params[top_lvl_section], {},
                                msg=f"top level section '{top_lvl_section}' should not have been empty")
            

class TestLoadParams(unittest.TestCase):
    """ tests for load_params function """

    def test_LP_load_params_no_errs(self):
        """ run load_params and there should be no errors """
        with TemporaryDirectory() as tmp_dir:
            yf = os.path.join(tmp_dir, "params.yml")
            # create params.yml file and write to it
            # give it the "input_output" and "params" sections it expects
            s = (
                "input_output:\n"
                "    subsection: none\n"
                "params:\n"
                "    subsection: none\n"
            )
            with open(yf, "w") as f:
                f.write(s)
            input_output, params = load_params(yf)


class TestSaveParams(unittest.TestCase):
    """ tests for save_params function """

    def test_SP_param_file_creation(self):
        """ makes sure a new params file is created """
        with TemporaryDirectory() as tmp_dir:
            pf = os.path.join(tmp_dir, "params.yml")
            self.assertFalse(os.path.isfile(pf), 
                             msg="params file should not exist before")
            save_params({"junk": "data"}, {"more": "junk"}, pf)
            self.assertTrue(os.path.isfile(pf), 
                            msg="params file should exist after")
    
    def test_SP_param_file_overwrite(self):
        """ make sure saving params to exsiting file overwrites it """
        with TemporaryDirectory() as tmp_dir:
            pf = os.path.join(tmp_dir, "params.yml")
            # create db file and write to it
            with open(pf, "w") as f:
                f.write("test")
            s = os.stat(pf)  # check file size
            save_params({"junk": "data"}, {"more": "junk"}, pf)
            # make sure file size changed
            with open(pf, "r") as f:
                self.assertNotEqual(s, os.stat(pf), 
                                    msg="existing params file contents should have been overwritten")


if __name__ == "__main__":
    # run the tests for this module if invoked directly
    unittest.main(verbosity=2)




