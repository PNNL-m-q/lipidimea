"""
lipidimea/test/lipids/__init__.py

Dylan Ross (dylan.ross@pnnl.gov)

    subpackage with tests for lipidimea/lipids subpackage,
    also this module has tests for anything defined in the 
    lipidimea/lipids/__init__.py module
"""


from unittest import TestCase

from lipidimea.lipids import (
    Lipid, LipidWithChains
)


class TestLipid(TestCase):
    """ tests for the Lipid class """

    def test_NO_TESTS_IMPLEMENTED_YET(self):
        """ placeholder, remove this function and implement tests """
        raise NotImplementedError("no tests implemented yet")


class TestLipidWithChains(TestCase):
    """ tests for the LipidWithChains class """

    def test_NO_TESTS_IMPLEMENTED_YET(self):
        """ placeholder, remove this function and implement tests """
        raise NotImplementedError("no tests implemented yet")