"""
LipidIMEA/test/util.py

Dylan Ross (dylan.ross@pnnl.gov)

    tests for LipidIMEA/util.py module
"""


from unittest import TestCase
from tempfile import TemporaryDirectory
import os

from LipidIMEA.util import (
    create_results_db, load_default_params, load_params, save_params
)


class TestCreateResultsDb(TestCase):
    """ tests for create_results_db function """

    def test_db_file_creation(self):
        """ makes sure the db file is created """
        with TemporaryDirectory() as tmp_dir:
            dbf = os.path.join(tmp_dir, "results.db")
            self.assertFalse(os.path.isfile(dbf), 
                             msg="db file should not exist before")
            create_results_db(dbf)
            self.assertTrue(os.path.isfile(dbf), 
                            msg="db file should exist after")
    
    def test_db_file_already_exists(self):
        """ make sure an exception is raised when trying to create the db file but it already exists and overwrite kwarg was not set to True """
        with TemporaryDirectory() as tmp_dir:
            dbf = os.path.join(tmp_dir, "results.db")
            # create db file and write to it
            with open(dbf, "w") as f:
                f.write("test")
            with self.assertRaises(RuntimeError,
                                   msg="should have raised a RuntimeError because the db file exists and overwrite kwarg is False"
                                   ):
                create_results_db(dbf)
            # make sure the file's content was not changed
            with open(dbf, "r") as f:
                self.assertEqual(f.read().strip(), "test", 
                                 msg="existing db file contents should not have been modified")
    
    def test_db_file_already_exists_overwrite(self):
        """ make sure when trying to create the db file but it already exists and overwrite kwarg was set to True that the file does get changed """
        with TemporaryDirectory() as tmp_dir:
            dbf = os.path.join(tmp_dir, "results.db")
            # create db file and write to it
            with open(dbf, "w") as f:
                f.write("test")
            s = os.stat(dbf)  # check file size
            create_results_db(dbf, overwrite=True)  # do not expect an exception because overwrite is True
            # make sure file size changed
            with open(dbf, "r") as f:
                self.assertNotEqual(s, os.stat(dbf), 
                                    msg="existing db file contents should have been overwritten")


class TestLoadDefaultParams(TestCase):
    """ tests for load_default_params function """

    def test_load_default_params_no_errs(self):
        """ run load_default_params and there should be no errors """
        params = load_default_params()

    def test_default_params_top_level_sections(self):
        """ load default parameters and make sure top level sections are present and not empty """
        params = load_default_params()
        for top_lvl_section in ['dda', 'dia', 'annotation', 'misc']:
            self.assertIn(top_lvl_section, params.keys(), 
                          msg="top level section '{}' should have been in default params".format(top_lvl_section))
            self.assertNotEqual(params[top_lvl_section], {},
                                msg="top level section '{}' should not have been empty".format(top_lvl_section))
            

class TestLoadParams(TestCase):
    """ tests for load_params function """

    def test_load_params_no_errs(self):
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


class TestSaveParams(TestCase):
    """ tests for save_params function """

    def test_param_file_creation(self):
        """ makes sure a new params file is created """
        with TemporaryDirectory() as tmp_dir:
            pf = os.path.join(tmp_dir, "params.yml")
            self.assertFalse(os.path.isfile(pf), 
                             msg="params file should not exist before")
            save_params({"junk": "data"}, {"more": "junk"}, pf)
            self.assertTrue(os.path.isfile(pf), 
                            msg="params file should exist after")
    
    def test_param_file_overwrite(self):
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
                

class TestDebugHandler(TestCase):
    """ tests for the debug_handler function """

    def test_NO_TESTS_IMPLEMENTED_YET(self):
        """ placeholder, remove this function and implement tests """
        raise NotImplementedError("no tests implemented yet")
