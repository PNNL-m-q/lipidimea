"""
LipidIMEA/test/lipids/_util.py

Dylan Ross (dylan.ross@pnnl.gov)

    tests for the LipidIMEA/lipids/_util.py module
"""


from unittest import TestCase

from LipidIMEA.lipids._util import (
    get_c_u_combos
)
from LipidIMEA.lipids import Lipid


class TestGetCUCombos(TestCase):
    """ tests for the get_c_u_combos function """

    def test_get_c_u_combos_no_errs(self):
        """ run get_c_u_combos with normal params there should be no errors """
        lpd = Lipid('LMGP0101', 40, 6)
        for c, u in get_c_u_combos(lpd, 8, 26, True):
            pass

    def test_correct_fa_combos(self):
        """ run get_c_u_combos with normal params and make sure all of the expected FAs are yielded """
        lpd = Lipid('LMGP0101', 40, 6)
        combos = [(c, u) for c, u in get_c_u_combos(lpd, 8, 26, True)]
        for c in range(14, 27):
            for u in range(7):
                self.assertIn((c, u), combos,
                              msg="expected C:U combo {}:{} was not produced".format(c, u))

    def test_no_odd_c(self):
        """ run get_c_u_combos with odd_c param set to False there should be no odd carbon counts """
        lpd = Lipid('LMGP0101', 40, 6)
        for c, u in get_c_u_combos(lpd, 8, 26, False):
            self.assertTrue(c % 2 == 0,
                            msg="there should be no odd carbon counts if odd_c is False")
