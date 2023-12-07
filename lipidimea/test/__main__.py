"""
LipidIMEA/test/__main__.py

Dylan Ross (dylan.ross@pnnl.gov)

    runs unit tests
"""


import unittest

# tests for LipidIMEA/util.py
from LipidIMEA.test.util import (
    TestCreateResultsDb, TestLoadDefaultParams, TestLoadParams, TestSaveParams
)


if __name__ == '__main__':
    # run all imported TestCases
    unittest.main(verbosity=2)
