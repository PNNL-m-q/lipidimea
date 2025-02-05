"""
lipidlib/test/__main__.py

Dylan Ross (dylan.ross@pnnl.gov)

    runs unit tests, imports defined test cases from all of the
    individual test modules
"""


import unittest


from lipidlib.test.lipids import (
    TestGetCUCombos, TestLipid, TestLipidWithChains
)
from lipidlib.test._fragmentation_rules import (
    Test_FragRule, Test_FragRuleStatic, Test_FragRuleDynamic, TestLoadRules
)
from lipidlib.test.parser import (
    Test_SuffixesCombinable, Test_CombineOVariants, Test_CombinedOxySuffixFromOxySuffixChains, 
    Test_GetLmidPrefix, TestParseLipidName
)


if __name__ == '__main__':
    # run all imported TestCases
    unittest.main(verbosity=2)
