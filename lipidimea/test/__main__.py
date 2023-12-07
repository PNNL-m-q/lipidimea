"""
LipidIMEA/test/__main__.py

Dylan Ross (dylan.ross@pnnl.gov)

    runs unit tests, imports defined test cases from all of the
    individual test modules
"""


import unittest


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
from LipidIMEA.test.msms._util import (
    TestMS2ToStr, TestStrToMS2, TestApplyArgsAndKwargs
)
from LipidIMEA.test.msms.dda import (
    Test_MSMSReaderDDA, Test_MSMSReaderDDACached, Test_ExtractAndFitChroms, 
    Test_ConsolidateChromFeats, Test_ExtractAndFitMs2Spectra, Test_AddFeaturesToDb,
    TestExtractDdaFeatures, TestExtractDdaFeaturesMultiproc, TestConsolidateDdaFeatures
)
from LipidIMEA.test.msms.dia import (
    Test_SelectXicPeak, Test_LerpTogether, Test_DeconDistance, Test_DeconvoluteMs2Peaks,
    Test_AddSingleTargetResultsToDb, Test_Ms2PeaksToStr, Test_SingleTargetAnalysis, 
    TestExtractDiaFeatures, TestExtractDiaFeaturesMultiproc, TestAddCalibratedCcsToDiaFeatures
)
from LipidIMEA.test.util import (
    TestCreateResultsDb, TestLoadDefaultParams, TestLoadParams, TestSaveParams, TestDebugHandler
)


if __name__ == '__main__':
    # run all imported TestCases
    unittest.main(verbosity=2)
