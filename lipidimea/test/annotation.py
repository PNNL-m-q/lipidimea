"""
lipidimea/test/annotation.py

Dylan Ross (dylan.ross@pnnl.gov)

    tests for the lipidimea/annotation.py module
"""


import os

import unittest


from lipidimea.annotation import (
    DEFAULT_POS_SCDB_CONFIG, DEFAULT_NEG_SCDB_CONFIG,
    SumCompLipidDB, remove_lipid_annotations, annotate_lipids_sum_composition, 
    filter_annotations_by_rt_range, update_lipid_ids_with_frag_rules
)


class TestDefaultSumCompLipidDBConfigs(unittest.TestCase):
    """ tests for the globals storing paths to default SumCompLipidDB config files """

    def test_DSCLDC_built_in_configs_exist(self):
        """ ensure the built in default SumCompLipidDB config files exist """
        self.assertTrue(os.path.isfile(DEFAULT_POS_SCDB_CONFIG))
        self.assertTrue(os.path.isfile(DEFAULT_NEG_SCDB_CONFIG))


class TestSumCompLipidDB(unittest.TestCase):
    """ tests for the SumCompLipidDB class """

    def test_NO_TESTS_IMPLEMENTED_YET(self):
        """ placeholder, remove this function and implement tests """
        raise NotImplementedError("no tests implemented yet")
    

class TestRemoveLipidAnnotations(unittest.TestCase):
    """ tests for the remove_lipid_annotations function """

    def test_NO_TESTS_IMPLEMENTED_YET(self):
        """ placeholder, remove this function and implement tests """
        raise NotImplementedError("no tests implemented yet")


class TestAnnotateLipidsSumComposition(unittest.TestCase):
    """ tests for the annotate_lipids_sum_composition function """

    def test_NO_TESTS_IMPLEMENTED_YET(self):
        """ placeholder, remove this function and implement tests """
        raise NotImplementedError("no tests implemented yet")
    

class TestFilterAnnotationsByRTRange(unittest.TestCase):
    """ tests for the filter_annotations_by_rt_range function """

    def test_NO_TESTS_IMPLEMENTED_YET(self):
        """ placeholder, remove this function and implement tests """
        raise NotImplementedError("no tests implemented yet")


class TestUpdateLipidIDsWithFragRules(unittest.TestCase):
    """ tests for the update_lipid_ids_with_frag_rules function """

    def test_NO_TESTS_IMPLEMENTED_YET(self):
        """ placeholder, remove this function and implement tests """
        raise NotImplementedError("no tests implemented yet")


if __name__ == "__main__":
    # run the tests for this module if invoked directly
    unittest.main(verbosity=2)
