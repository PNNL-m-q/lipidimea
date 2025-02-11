"""
lipidimea/test/__all_tests.py
Dylan Ross (dylan.ross@pnnl.gov)

    special module for grouping all TestSuites from submodules/subpackages below
"""


import unittest

from lipidimea.test.annotation import AllTestsAnnotation
from lipidimea.test.params import AllTestsParams
from lipidimea.test.util import AllTestsUtil
from lipidimea.test.msms.__all_tests import AllTests as AllTestsMsms


# collect tests
AllTests = unittest.TestSuite()
AllTests.addTests([
    AllTestsAnnotation,
    AllTestsParams,
    AllTestsUtil,
    AllTestsMsms
])
