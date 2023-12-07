"""
LipidIMEA/test/util.py

Dylan Ross (dylan.ross@pnnl.gov)

    tests for LipidIMEA/util.py
"""


from unittest import TestCase
from tempfile import TemporaryDirectory
import os

from LipidIMEA.util import create_results_db, load_default_params


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