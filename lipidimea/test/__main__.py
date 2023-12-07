"""
LipidIMEA/test/__main__.py

Dylan Ross (dylan.ross@pnnl.gov)

    runs unit tests, imports defined test cases from all of the
    individual test modules
"""


import unittest

from LipidIMEA.test.util import (
    TestCreateResultsDb, TestLoadDefaultParams, TestLoadParams, TestSaveParams, TestDebugHandler
)
from LipidIMEA.test.lipids import (
    TestLipid, TestLipidWithChains
)
from LipidIMEA.test.lipids._fragmentation_rules import (
    Test_FragRule, Test_FragRuleStatic, Test_FragRuleDynamic, TestLoadRules
)
from LipidIMEA.test.lipids._util import (
    TestGetCUCombos
)
from LipidIMEA.test.lipids.annotation import (
    TestSumCompLipidDB, TestRemoveLipidAnnotations, TestAnnotateLipidsSumComposition, 
    TestFilterAnnotationsByRTRange, TestUpdateLipidIDsWithFragRules
)
from LipidIMEA.test.lipids.parser import (
    Test_GetLmidPrefix, Test_OxySuffixFromOxySuffixChains, TestParseLipidName
)


if __name__ == '__main__':
    # run all imported TestCases
    unittest.main(verbosity=2)
