"""
lipidimea/test/util.py

Dylan Ross (dylan.ross@pnnl.gov)

    tests for lipidimea/util.py module
"""


import unittest
from tempfile import TemporaryDirectory
import os
import io
import contextlib
import sqlite3

from lipidimea.util import (
    _RESULTS_DB_SCHEMA,
    create_results_db,
    debug_handler
)


class Test_ResultsDbSchemaPath(unittest.TestCase):
    """ test for the global storing the path to the results DB schema file """

    def test_RDSP_built_schema_file_exist(self):
        """ ensure the results database schema file exists """
        self.assertTrue(os.path.isfile(_RESULTS_DB_SCHEMA))


class TestCreateResultsDb(unittest.TestCase):
    """ tests for create_results_db function """

    def test_CRD_db_file_creation(self):
        """ makes sure the db file is created """
        with TemporaryDirectory() as tmp_dir:
            dbf = os.path.join(tmp_dir, "results.db")
            self.assertFalse(os.path.isfile(dbf), 
                             msg="db file should not exist before")
            create_results_db(dbf)
            self.assertTrue(os.path.isfile(dbf), 
                            msg="db file should exist after")
    
    def test_CRD_db_file_already_exists(self):
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
    
    def test_CRD_db_file_already_exists_overwrite(self):
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
                
    def test_CRD_strict_option(self):
        """ make sure the strict option works as intended """
        # first create a database with the default behavior (strict enabled)
        with TemporaryDirectory() as tmp_dir:
            dbf = os.path.join(tmp_dir, "results.db")
            create_results_db(dbf)
            # try an insert query with the wrong datatypes
            # with STRICT enabled this should cause an error
            with self.assertRaises(sqlite3.IntegrityError,
                                   msg="trying to insert with wrong types and STRICT enabled should cause an error"):
                con = sqlite3.connect(dbf)
                con.execute("INSERT INTO _DIAFeatsToDeconFrags VALUES (?,?);", ("bad", "types"))
        # create a database with strict disabled
        with TemporaryDirectory() as tmp_dir:
            dbf = os.path.join(tmp_dir, "results.db")
            create_results_db(dbf, strict=False)
            # try an insert query with the wrong datatypes
            # with STRICT disabled this should not cause an error
            con = sqlite3.connect(dbf)
            con.execute("INSERT INTO _DIAFeatsToDeconFrags VALUES (?,?);", ("bad", "types"))
                

class TestDebugHandler(unittest.TestCase):
    """ tests for the debug_handler function """

    def test_DH_textcb_with_no_cb(self):
        """ calling the debug handler with 'textcb' or 'textcb_pid' without providing a callback should cause a ValueError """
        with self.assertRaises(ValueError,
                               msg="should have gotten a ValueError for not providing a callback"):
            debug_handler("textcb", None, "this should cause a ValueError")
        with self.assertRaises(ValueError,
                               msg="should have gotten a ValueError for not providing a callback"):
            debug_handler("textcb_pid", None, "this should cause a ValueError")

    def test_DH_text_expected_output(self):
        """ call the debug handler with 'text' and make sure the captured output is correct """
        sio = io.StringIO()
        with contextlib.redirect_stdout(sio):
            # do something
            debug_handler("text", None, "expected message")
        output = sio.getvalue()
        self.assertEqual(output, "DEBUG: expected message\n",
                         msg="captured text incorrect")

    def test_DH_text_pid_expected_output(self):
        """ call the debug handler with 'text_pid' and make sure the captured output is correct """
        sio = io.StringIO()
        with contextlib.redirect_stdout(sio):
            # do something
            debug_handler("text_pid", None, "expected message", pid=420)
        output = sio.getvalue()
        self.assertEqual(output, "<pid: 420> DEBUG: expected message\n",
                         msg="captured text incorrect")

    def _helper_cb(self, msg):
        """ helper method simulating a debug callback, stores messages in a list in self.__msgs """
        self.__msgs.append(msg)

    def test_DH_textcb_expected_output(self):
        """ simulate using a debug callback and make sure the generated messages are correct """
        expected = [
            "DEBUG: message 1",
            "DEBUG: message 2",
            "DEBUG: message 3"
        ]
        self.__msgs = []
        debug_handler("textcb", self._helper_cb, "message 1")
        debug_handler("textcb", self._helper_cb, "message 2", pid=420)  # PID should be ignored with "textcb" flag
        debug_handler("textcb", self._helper_cb, "message 3")
        self.assertListEqual(self.__msgs, expected,
                             msg="incorrect outputs produced")

    def test_DH_textcb_pid_expected_output(self):
        """ simulate using a debug callback with PID and make sure the generated messages are correct """
        expected = [
            "<pid: 420> DEBUG: message 1",
            "<pid: 420> DEBUG: message 2",
            "<pid: 420> DEBUG: message 3"
        ]
        self.__msgs = []
        debug_handler("textcb_pid", self._helper_cb, "message 1", pid=420)
        debug_handler("textcb_pid", self._helper_cb, "message 2", pid=420)
        debug_handler("textcb_pid", self._helper_cb, "message 3", pid=420)
        self.assertListEqual(self.__msgs, expected,
                             msg="incorrect outputs produced")


if __name__ == "__main__":
    # run the tests for this module if invoked directly
    unittest.main(verbosity=2)

