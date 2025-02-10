"""
lipidimea/test/__all_tests.py
Dylan Ross (dylan.ross@pnnl.gov)

    special module for grouping all TestSuites from submodules/subpackages below
"""


import unittest

from lipidimea.test.annotation import AllTestsAnnotation
from lipidimea.test.params import AllTestsParams


# collect tests
AllTests = unittest.TestSuite()
AllTests.addTests([
    AllTestsAnnotation,
    AllTestsParams,
])
