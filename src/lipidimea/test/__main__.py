"""
lipidimea/test/__main__.py
Dylan Ross (dylan.ross@pnnl.gov)

    runs unit tests, imports defined test cases from all of the
    individual test subpackages/modules below
"""


import unittest

from lipidimea.test.__all_tests import AllTests


# run all defined TestCases from across the package
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(AllTests)
