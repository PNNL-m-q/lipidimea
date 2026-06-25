"""
lipidimea/test/msms/__all_tests.py
Dylan Ross (dylan.ross@pnnl.gov)

    special module for grouping all TestSuites from submodules/subpackages below
"""


import unittest

from lipidimea.test.msms.dda import AllTestsDda
from lipidimea.test.msms.dia import AllTestsDia

# collect tests
AllTests = unittest.TestSuite()
AllTests.addTests([
    AllTestsDda,
    AllTestsDia
])
