"""
lipidlib/test/lipids/__init__.py

Dylan Ross (dylan.ross@pnnl.gov)

    tests for lipidlib/lipids.py module
"""


import unittest

from lipidlib.lipids import (
    IdLevel, get_c_u_combos, Lipid, LipidWithChains
)


class TestIdLevel(unittest.TestCase):
    """ tests for the IdLevel Enum """

    def test_level_ordering(self):
        """ make sure ordering works as expected with IdLevels """
        self.assertEqual(IdLevel.FULL_STRUCTURE, IdLevel.FULL_STRUCTURE)
        self.assertLess(IdLevel.SPECIES, IdLevel.COMPLETE_STRUCTURE)
        self.assertGreater(IdLevel.MOLECULAR_SPECIES_DBP_SNP, IdLevel.MOLECULAR_SPECIES)


class TestGetCUCombos(unittest.TestCase):
    """ tests for the get_c_u_combos function """

    def test_get_c_u_combos_no_errs(self):
        """ run get_c_u_combos with normal params, there should be no errors """
        lpd = Lipid("LMGP0101", 40, 6)
        for c, u in get_c_u_combos(lpd, 12, 24, True):
            pass

    def test_correct_fa_combos(self):
        """ run get_c_u_combos with normal params, make sure all of the expected FAs are yielded """
        lpd = Lipid("LMGP0101", 40, 6)
        combos = [(c, u) for c, u in get_c_u_combos(lpd, 12, 24, True)]
        for c in range(16, 25):
            for u in range(7):
                self.assertIn((c, u), combos,
                              msg=f"expected C:U combo {c}:{u} was not produced")

    def test_no_odd_c(self):
        """ run get_c_u_combos with odd_c param set to False, there should be no odd carbon counts """
        lpd = Lipid('LMGP0101', 40, 6)
        for c, u in get_c_u_combos(lpd, 8, 26, False):
            self.assertTrue(c % 2 == 0,
                            msg="there should be no odd carbon counts if odd_c is False")
            
    def test_static_max_u(self):
        """ set max_u to an int for a static limit on unsaturations """
        lpd = Lipid("LMGP0101", 40, 6)
        max_u = 4
        combos = [(c, u) for c, u in get_c_u_combos(lpd, 12, 24, True, max_u=max_u)]
        for c in range(16, 25):
            for u in range(7):
                if u >= 2 and u <= max_u:
                    self.assertIn((c, u), combos,
                                  msg=f"expected C:U combo {c}:{u} was not produced")
                else:
                    self.assertNotIn((c, u), combos,
                                     msg=f"C:U combo {c}:{u} should not have been produced")

    def test_func_max_u(self):
        """ set max_u to a function for a dynamic limit on unsaturations """
        lpd = Lipid("LMGP0101", 40, 6)
        combos = [(c, u) for c, u in get_c_u_combos(lpd, 12, 24, True, max_u=lambda c: 4)]
        for c in range(16, 25):
            for u in range(7):
                if u >= 2 and u <= 4:
                    self.assertIn((c, u), combos,
                                  msg=f"expected C:U combo {c}:{u} was not produced")
                else:
                    self.assertNotIn((c, u), combos,
                                     msg=f"C:U combo {c}:{u} should not have been produced")


class TestLipid(unittest.TestCase):
    """ tests for the Lipid class """

    def test_init_lipid_no_errs(self):
        """ initialize a Lipid, there should be no errors """
        lpd = Lipid("LMGP0101", 34, 1)

    def test_init_lipid_bad_lmid_prefix(self):
        """ initialize a Lipid with an unrecognized LMID prefix, should raise an error """
        with self.assertRaises(ValueError,
                               msg="should have gotten a ValueError for unrecognized LMID prefix"):
            lpd = Lipid("not a valid LMID prefix", 34, 1)

    def test_init_lipid_bad_fa_composition(self):
        """ initialize a Lipid with bad FA compositions, should raise errors """
        # FA carbons must be > 0
        with self.assertRaises(ValueError,
                               msg="should have gotten a ValueError for FA carbons <= 0"):
            lpd = Lipid("LMGP0101", 0, 0)
        # FA unsat must be >= 0
        with self.assertRaises(ValueError,
                               msg="should have gotten a ValueError for FA unsaturations < 0"):
            lpd = Lipid("LMGP0101", 10, -1)
        # test some upper limits on FA unsaturations based on FA carbons
        for c, u in [(1, 1), (2, 1), (3, 2), (4, 2), (5, 3), (6, 3)]:
            with self.assertRaises(ValueError,
                                msg="should have gotten a ValueError for FA unsaturations {} with FA carbons {} (unsaturations > max)".format(u, c)):
                lpd = Lipid("LMGP0101", c, u)

    def test_correct_formulas(self):
        """ initialize Lipids from multiple classes, they should have the correct molecular formulas """
        test_lipids = [
            # (params=(lmid_prefix, sum_c, sum_u), expected formula)
            ("LMFA0101", 16, 0, {"C": 16, "H": 32, "O": 2}),  # FA 16:0
            ("LMFA0103", 20, 4, {"C": 20, "H": 32, "O": 2}),  # FA 20:4
            ("LMFA0707", 18, 2, {"C": 25, "H": 45, "N": 1, "O": 4}),  # CAR 18:2
            ("LMFA0804", 20, 4, {"C": 22, "H": 37, "N": 1, "O": 2}),  # NAE 20:4
            ("LMGL0101", 18, 0, {"C": 21, "H": 42, "O": 4}),  # MG 18:0
            ("LMGL0101", 18, 1, {"C": 21, "H": 40, "O": 4}),  # MG 18:1
            ("LMGL0201", 34, 0, {"C": 37, "H": 72, "O": 5}),  # DG 34:0
            ("LMGL0301", 48, 1, {"C": 51, "H": 96, "O": 6}),  # TG 48:1
            ("LMGL0302", 45, 0, {"C": 48, "H": 94, "O": 5}),  # TG O-45:0
            ("LMGL0501AA", 36, 2, {"C": 45, "H": 82, "O": 10}),  # MGDG 36:2
            ("LMGL0501AD", 32, 2, {"C": 47, "H": 84, "O": 15}),  # DGDG 32:2
            ("LMGP0101", 34, 1, {"C": 42, "H": 82, "N": 1, "O": 8, "P": 1}),  # PC 34:1
            ("LMGP0102", 30, 0, {"C": 38, "H": 78, "N": 1, "O": 7, "P": 1}),  # PC O-30:0
            ("LMGP0103", 34, 0, {"C": 42, "H": 84, "N": 1, "O": 7, "P": 1}),  # PC P-34:0
            ("LMGP0105", 16, 0, {"C": 24, "H": 50, "N": 1, "O": 7, "P": 1}),  # LPC 16:0
            ("LMGP0106", 16, 1, {"C": 24, "H": 50, "N": 1, "O": 6, "P": 1}),  # LPC O-16:1
            ("LMGP0107", 18, 0, {"C": 26, "H": 54, "N": 1, "O": 6, "P": 1}),  # LPC P-18:0
            ("LMGP0201", 34, 1, {"C": 39, "H": 76, "N": 1, "O": 8, "P": 1}),  # PE 34:1
            ("LMGP0202", 30, 0, {"C": 35, "H": 72, "N": 1, "O": 7, "P": 1}),  # PE O-30:0
            ("LMGP0203", 34, 0, {"C": 39, "H": 78, "N": 1, "O": 7, "P": 1}),  # PE P-34:0
            ("LMGP0205", 16, 0, {"C": 21, "H": 44, "N": 1, "O": 7, "P": 1}),  # LPE 16:0
            ("LMGP0206", 18, 1, {"C": 23, "H": 48, "N": 1, "O": 6, "P": 1}),  # LPE O-18:1
            ("LMGP0207", 18, 0, {"C": 23, "H": 48, "N": 1, "O": 6, "P": 1}),  # LPE P-18:0
            ("LMGP0301", 34, 1, {"C": 40, "H": 76, "N": 1, "O": 10, "P": 1}),  # PS 34:1
            ("LMGP0302", 30, 0, {"C": 36, "H": 72, "N": 1, "O": 9, "P": 1}),  # PS O-30:0
            ("LMGP0303", 34, 0, {"C": 40, "H": 78, "N": 1, "O": 9, "P": 1}),  # PS P-34:0
            ("LMGP0305", 16, 0, {"C": 22, "H": 44, "N": 1, "O": 9, "P": 1}),  # LPS 16:0
            ("LMGP0306", 18, 0, {"C": 24, "H": 50, "N": 1, "O": 8, "P": 1}),  # LPS O-18:0
            ("LMGP0307", 18, 0, {"C": 24, "H": 48, "N": 1, "O": 8, "P": 1}),  # LPS P-18:0
            ("LMGP0401", 34, 1, {"C": 40, "H": 77, "O": 10, "P": 1}),  # PG 34:1
            ("LMGP0402", 30, 0, {"C": 36, "H": 73, "O": 9, "P": 1}),  # PG O-30:0
            ("LMGP0403", 34, 0, {"C": 40, "H": 79, "O": 9, "P": 1}),  # PG P-34:0
            ("LMGP0405", 16, 0, {"C": 22, "H": 45, "O": 9, "P": 1}),  # LPG 16:0
            ("LMGP0406", 18, 0, {"C": 24, "H": 51, "O": 8, "P": 1}),  # LPG O-18:0
            ("LMGP0407", 18, 0, {"C": 24, "H": 49, "O": 8, "P": 1}),  # LPG P-18:0
            ("LMGP0601", 34, 1, {"C": 43, "H": 81, "O": 13, "P": 1}),  # PI 34:1
            ("LMGP0602", 30, 0, {"C": 39, "H": 77, "O": 12, "P": 1}),  # PI O-30:0
            ("LMGP0603", 34, 0, {"C": 43, "H": 83, "O": 12, "P": 1}),  # PI P-34:0
            ("LMGP0605", 16, 0, {"C": 25, "H": 49, "O": 12, "P": 1}),  # LPI 16:0
            ("LMGP0606", 18, 0, {"C": 27, "H": 55, "O": 11, "P": 1}),  # LPI O-18:0
            ("LMGP0607", 18, 0, {"C": 27, "H": 53, "O": 11, "P": 1}),  # LPI P-18:0
            ("LMGP0701", 34, 1, {"C": 43, "H": 82, "O": 16, "P": 2}),  # PIP 34:1
            # TODO: ("LMGP0705", ?, ?, {?}),  # LPIP ?:?
            ("LMGP0801", 37, 4, {"C": 46, "H": 83, "O": 19, "P": 3}),  # PIP2 37:4
            ("LMGP0901", 37, 4, {"C": 46, "H": 84, "O": 22, "P": 4}),  # PIP3 37:4
            ("LMGP1001", 34, 1, {"C": 37, "H": 71, "O": 8, "P": 1}),  # PA 34:1
            ("LMGP1002", 30, 0, {"C": 33, "H": 67, "O": 7, "P": 1}),  # PA O-30:0
            ("LMGP1003", 34, 0, {"C": 37, "H": 73, "O": 7, "P": 1}),  # PA P-34:0
            ("LMGP1005", 16, 0, {"C": 19, "H": 39, "O": 7, "P": 1}),  # LPA 16:0
            ("LMGP1006", 18, 0, {"C": 21, "H": 45, "O": 6, "P": 1}),  # LPA O-18:0
            ("LMGP1007", 18, 0, {"C": 21, "H": 43, "O": 6, "P": 1}),  # LPA P-18:0
            ("LMGP1201", 72, 8, {"C": 81, "H": 142, "O": 17, "P": 2}),  # CL 72:8
            ("LMSP0201", 34, 1, {"C": 34, "H": 67, "O": 3, "N": 1}),  # Cer 34:1;O2
            ("LMSP0301", 34, 1, {"C": 39, "H": 79, "O": 6, "N": 2, "P": 1}),  # SM 34:1;O2
            ("LMSP0501AA", 34, 1, {"C": 40, "H": 77, "O": 8, "N": 1}),  # HexCer 34:1;O2
            ("LMSP0501AB", 30, 1, {"C": 42, "H": 79, "O": 13, "N": 1}),  # Hex2Cer 30:1;O2
            ("LMST0102", 18, 0, {"C": 45, "H": 80, "O": 2}),  # CE 18:0
        ]
        for *params, expected_formula in test_lipids:
            lpd = Lipid(*params)
            self.assertDictEqual(lpd.formula, expected_formula,
                                 msg="lipid {} should have had formula: {} (had: {})".format(str(lpd), expected_formula, lpd.formula))

    def test_correct_shorthand_names(self):
        """ initialize Lipids from multiple classes, they should have the correct shorthand names """
        test_lipids = [
            # (params=(lmid_prefix, sum_c, sum_u), expected formula)
            ("LMFA0101", 16, 0, "FA 16:0"),
            ("LMFA0103", 20, 4, "FA 20:4"),
            ("LMFA0707", 18, 2, "CAR 18:2"),
            ("LMFA0804", 20, 4, "NAE 20:4"),
            ("LMGL0101", 18, 0, "MG 18:0"),
            ("LMGL0101", 18, 1, "MG 18:1"),
            ("LMGL0201", 34, 0, "DG 34:0"),
            ("LMGL0301", 48, 1, "TG 48:1"),
            ("LMGL0302", 45, 0, "TG O-45:0"),
            ("LMGL0501AA", 36, 2, "MGDG 36:2"),
            ("LMGL0501AD", 32, 2, "DGDG 32:2"),
            ("LMGP0101", 34, 1, "PC 34:1"),
            ("LMGP0102", 30, 0, "PC O-30:0"),
            ("LMGP0103", 34, 0, "PC P-34:0"),
            ("LMGP0105", 16, 0, "LPC 16:0"),
            ("LMGP0106", 16, 1, "LPC O-16:1"),
            ("LMGP0107", 18, 0, "LPC P-18:0"),
            ("LMGP0201", 34, 1, "PE 34:1"),
            ("LMGP0202", 30, 0, "PE O-30:0"),
            ("LMGP0203", 34, 0, "PE P-34:0"),
            ("LMGP0205", 16, 0, "LPE 16:0"),
            ("LMGP0206", 18, 1, "LPE O-18:1"),
            ("LMGP0207", 18, 0, "LPE P-18:0"),
            ("LMGP0301", 34, 1, "PS 34:1"),
            ("LMGP0302", 30, 0, "PS O-30:0"),
            ("LMGP0303", 34, 0, "PS P-34:0"),
            ("LMGP0305", 16, 0, "LPS 16:0"),
            ("LMGP0306", 18, 0, "LPS O-18:0"),
            ("LMGP0307", 18, 0, "LPS P-18:0"),
            ("LMGP0401", 34, 1, "PG 34:1"),
            ("LMGP0402", 30, 0, "PG O-30:0"),
            ("LMGP0403", 34, 0, "PG P-34:0"),
            ("LMGP0405", 16, 0, "LPG 16:0"),
            ("LMGP0406", 18, 0, "LPG O-18:0"),
            ("LMGP0407", 18, 0, "LPG P-18:0"),
            ("LMGP0601", 34, 1, "PI 34:1"),
            ("LMGP0602", 30, 0, "PI O-30:0"),
            ("LMGP0603", 34, 0, "PI P-34:0"),
            ("LMGP0605", 16, 0, "LPI 16:0"),
            ("LMGP0606", 18, 0, "LPI O-18:0"),
            ("LMGP0607", 18, 0, "LPI P-18:0"),
            ("LMGP0701", 34, 1, "PIP 34:1"),
            # TODO: ("LMGP0705", ?, ?, "LPIP ?:?"),
            ("LMGP0801", 37, 4, "PIP2 37:4"),
            ("LMGP0901", 37, 4, "PIP3 37:4"),
            ("LMGP1001", 34, 1, "PA 34:1"),
            ("LMGP1002", 30, 0, "PA O-30:0"),
            ("LMGP1003", 34, 0, "PA P-34:0"),
            ("LMGP1005", 16, 0, "LPA 16:0"),
            ("LMGP1006", 18, 0, "LPA O-18:0"),
            ("LMGP1007", 18, 0, "LPA P-18:0"),
            ("LMGP1201", 72, 8, "CL 72:8"),
            ("LMSP0201", 34, 1, "Cer 34:1;O2"),
            ("LMSP0301", 34, 1, "SM 34:1;O2"),
            ("LMSP0501AA", 34, 1, "HexCer 34:1;O2"),
            ("LMSP0501AB", 30, 1, "Hex2Cer 30:1;O2"),
            ("LMST0102", 18, 0, "CE 18:0"),
        ]
        for *params, expected_name in test_lipids:
            lpd = Lipid(*params)
            self.assertEqual(str(lpd), expected_name,
                             msg="lipid should have had name: {} (had: {})".format(expected_name, str(lpd)))


class TestLipidWithChains(unittest.TestCase):
    """ tests for the LipidWithChains class """

    def test_init_lipid_no_errs(self):
        """ initialize a LipidWithChains, there should be no errors """
        lpd = LipidWithChains("LMGP0101", [16, 18], [0, 1])

    def test_init_lipid_bad_lmid_prefix(self):
        """ initialize a LipidWithChains with an unrecognized LMID prefix, should raise an error """
        with self.assertRaises(ValueError,
                               msg="should have gotten a ValueError for unrecognized LMID prefix"):
            lpd = LipidWithChains("not a valid LMID prefix",  [16, 18], [0, 1])

    
    def test_init_lipid_bad_fa_composition(self):
        """ initialize a LipidWithChains with bad FA compositions, should raise errors """
        # FA carbon and unsaturation lists must be same length
        with self.assertRaises(ValueError,
                               msg="should have gotten a ValueError for different length FA carbons/unsaturations lists"):
            lpd = LipidWithChains("LMGP0101", [16, 18], [0])
        # length of FA carbons/unsaturations lists should match what is expected for lipid class
        with self.assertRaises(ValueError,
                               msg="should have gotten a ValueError for too few FA chains"):
            lpd = LipidWithChains("LMGP0101", [16], [0])
        with self.assertRaises(ValueError,
                               msg="should have gotten a ValueError for too many FA chains"):
            lpd = LipidWithChains("LMGP0101", [16, 18, 20], [0, 1, 4])
        # individual FA chains should have proper number of unsaturations
        bad_unsaturations = [
            ([16, 18], [-1, 0], "FA unsatutations < 0 (1)"),
            ([16, 18], [0, -1], "FA unsaturations < 0 (2)"),
            ([1, 18], [1, 0], "FA unsaturations > max (1)"),
            ([2, 18], [1, 0], "FA unsaturations > max (2)"),
            ([3, 18], [2, 0], "FA unsaturations > max (3)"),
            ([4, 18], [2, 0], "FA unsaturations > max (4)"),
            ([5, 18], [3, 0], "FA unsaturations > max (5)"),
            ([6, 18], [3, 0], "FA unsaturations > max (6)"),
            ([16, 1], [0, 1], "FA unsaturations > max (7)"),
            ([16, 2], [0, 1], "FA unsaturations > max (8)"),
            ([16, 3], [0, 2], "FA unsaturations > max (9)"),
            ([16, 4], [0, 2], "FA unsaturations > max (10)"),
            ([16, 5], [0, 3], "FA unsaturations > max (11)"),
            ([16, 6], [0, 3], "FA unsaturations > max (12)"),
        ]
        for fa_carbon_chains, fa_unsat_chains, reason in bad_unsaturations:
            with self.assertRaises(ValueError,
                                   msg="should have gotten a Value error for " + reason):
                lpd = LipidWithChains("LMGP0101", fa_carbon_chains, fa_unsat_chains)

    def test_correct_formulas(self):
        """ initialize LipidWithChains from multiple classes, they should have the correct molecular formulas """
        test_lipids = [
            # (params=(lmid_prefix, sum_c, sum_u), expected formula)
            ("LMFA0101", [16], [0], {"C": 16, "H": 32, "O": 2}),  # FA 16:0
            ("LMFA0103", [20], [4], {"C": 20, "H": 32, "O": 2}),  # FA 20:4
            ("LMFA0707", [18], [2], {"C": 25, "H": 45, "N": 1, "O": 4}),  # CAR 18:2
            ("LMFA0804", [20], [4], {"C": 22, "H": 37, "N": 1, "O": 2}),  # NAE 20:4
            ("LMGL0101", [18], [0], {"C": 21, "H": 42, "O": 4}),  # MG 18:0
            ("LMGL0101", [18], [1], {"C": 21, "H": 40, "O": 4}),  # MG 18:1
            ("LMGL0201", [16, 18], [0 ,0], {"C": 37, "H": 72, "O": 5}),  # DG 34:0
            ("LMGL0301", [18, 16, 14], [1, 0, 0], {"C": 51, "H": 96, "O": 6}),  # TG 48:1
            ("LMGL0302", [16, 15, 14], [0, 0, 0], {"C": 48, "H": 94, "O": 5}),  # TG O-45:0
            ("LMGL0501AA", [18, 18], [1, 1], {"C": 45, "H": 82, "O": 10}),  # MGDG 36:2 
            ("LMGL0501AD", [16, 16], [1, 1], {"C": 47, "H": 84, "O": 15}),  # DGDG 32:2
            ("LMGP0101", [18, 16], [1, 0], {"C": 42, "H": 82, "N": 1, "O": 8, "P": 1}),  # PC 34:1
            ("LMGP0102", [16, 14], [0, 0], {"C": 38, "H": 78, "N": 1, "O": 7, "P": 1}),  # PC O-30:0
            ("LMGP0103", [18, 16], [0, 0], {"C": 42, "H": 84, "N": 1, "O": 7, "P": 1}),  # PC P-34:0
            ("LMGP0105", [16], [0], {"C": 24, "H": 50, "N": 1, "O": 7, "P": 1}),  # LPC 16:0
            ("LMGP0106", [16], [1], {"C": 24, "H": 50, "N": 1, "O": 6, "P": 1}),  # LPC O-16:1
            ("LMGP0107", [18], [0], {"C": 26, "H": 54, "N": 1, "O": 6, "P": 1}),  # LPC P-18:0
            ("LMGP0201", [18, 16], [1, 0], {"C": 39, "H": 76, "N": 1, "O": 8, "P": 1}),  # PE 34:1
            ("LMGP0202", [16, 14], [0, 0], {"C": 35, "H": 72, "N": 1, "O": 7, "P": 1}),  # PE O-30:0
            ("LMGP0203", [16, 18], [0, 0], {"C": 39, "H": 78, "N": 1, "O": 7, "P": 1}),  # PE P-34:0
            ("LMGP0205", [16], [0], {"C": 21, "H": 44, "N": 1, "O": 7, "P": 1}),  # LPE 16:0
            ("LMGP0206", [18], [1], {"C": 23, "H": 48, "N": 1, "O": 6, "P": 1}),  # LPE O-18:1
            ("LMGP0207", [18], [0], {"C": 23, "H": 48, "N": 1, "O": 6, "P": 1}),  # LPE P-18:0
            ("LMGP0301", [18, 16], [1, 0], {"C": 40, "H": 76, "N": 1, "O": 10, "P": 1}),  # PS 34:1
            ("LMGP0302", [16, 14], [0, 0], {"C": 36, "H": 72, "N": 1, "O": 9, "P": 1}),  # PS O-30:0
            ("LMGP0303", [18, 16], [0, 0], {"C": 40, "H": 78, "N": 1, "O": 9, "P": 1}),  # PS P-34:0
            ("LMGP0305", [16], [0], {"C": 22, "H": 44, "N": 1, "O": 9, "P": 1}),  # LPS 16:0
            ("LMGP0306", [18], [0], {"C": 24, "H": 50, "N": 1, "O": 8, "P": 1}),  # LPS O-18:0
            ("LMGP0307", [18], [0], {"C": 24, "H": 48, "N": 1, "O": 8, "P": 1}),  # LPS P-18:0
            ("LMGP0401", [18, 16], [1, 0], {"C": 40, "H": 77, "O": 10, "P": 1}),  # PG 34:1
            ("LMGP0402", [16, 14], [0, 0], {"C": 36, "H": 73, "O": 9, "P": 1}),  # PG O-30:0
            ("LMGP0403", [18, 16], [0, 0], {"C": 40, "H": 79, "O": 9, "P": 1}),  # PG P-34:0
            ("LMGP0405", [16], [0], {"C": 22, "H": 45, "O": 9, "P": 1}),  # LPG 16:0
            ("LMGP0406", [18], [0], {"C": 24, "H": 51, "O": 8, "P": 1}),  # LPG O-18:0
            ("LMGP0407", [18], [0], {"C": 24, "H": 49, "O": 8, "P": 1}),  # LPG P-18:0
            ("LMGP0601", [18, 16], [1, 0], {"C": 43, "H": 81, "O": 13, "P": 1}),  # PI 34:1
            ("LMGP0602", [16, 14], [0, 0], {"C": 39, "H": 77, "O": 12, "P": 1}),  # PI O-30:0
            ("LMGP0603", [18, 16], [0, 0], {"C": 43, "H": 83, "O": 12, "P": 1}),  # PI P-34:0
            ("LMGP0605", [16], [0], {"C": 25, "H": 49, "O": 12, "P": 1}),  # LPI 16:0
            ("LMGP0606", [18], [0], {"C": 27, "H": 55, "O": 11, "P": 1}),  # LPI O-18:0
            ("LMGP0607", [18], [0], {"C": 27, "H": 53, "O": 11, "P": 1}),  # LPI P-18:0
            ("LMGP0701", [18, 16], [1, 0], {"C": 43, "H": 82, "O": 16, "P": 2}),  # PIP 34:1
            #TODO ("LMGP0705", ?, ?, {?}),  # LPIP ?:?
            ("LMGP0801", [19, 18], [2, 2], {"C": 46, "H": 83, "O": 19, "P": 3}),  # PIP2 37:4
            ("LMGP0901", [19, 18], [2, 2], {"C": 46, "H": 84, "O": 22, "P": 4}),  # PIP3 37:4
            ("LMGP1001", [18, 16], [1, 0], {"C": 37, "H": 71, "O": 8, "P": 1}),  # PA 34:1
            ("LMGP1002", [16, 14], [0, 0], {"C": 33, "H": 67, "O": 7, "P": 1}),  # PA O-30:0
            ("LMGP1003", [18, 16], [0, 0], {"C": 37, "H": 73, "O": 7, "P": 1}),  # PA P-34:0
            ("LMGP1005", [16], [0], {"C": 19, "H": 39, "O": 7, "P": 1}),  # LPA 16:0
            ("LMGP1006", [18], [0], {"C": 21, "H": 45, "O": 6, "P": 1}),  # LPA O-18:0
            ("LMGP1007", [18], [0], {"C": 21, "H": 43, "O": 6, "P": 1}),  # LPA P-18:0
            ("LMGP1201", [18, 18, 18, 18], [2, 2, 2, 2], {"C": 81, "H": 142, "O": 17, "P": 2}),  # CL 72:8
            ("LMSP0201", [18, 16], [1, 0], {"C": 34, "H": 67, "O": 3, "N": 1}),  # Cer 34:1;O2
            ("LMSP0301", [18, 16], [1, 0], {"C": 39, "H": 79, "O": 6, "N": 2, "P": 1}),  # SM 34:1;O2
            ("LMSP0501AA", [18, 16], [1, 0], {"C": 40, "H": 77, "O": 8, "N": 1}),  # HexCer 34:1;O2
            ("LMSP0501AB", [18, 12], [1, 0], {"C": 42, "H": 79, "O": 13, "N": 1}),  # Hex2Cer 30:1;O2
            ("LMST0102", [18], [0], {"C": 45, "H": 80, "O": 2}),  # CE 18:0
        ]
        for i, (*params, expected_formula) in enumerate(test_lipids):
            lpd = LipidWithChains(*params)
            self.assertDictEqual(lpd.formula, expected_formula,
                                 msg="lipid {} should have had formula: {} (had: {}) ({})".format(str(lpd), 
                                                                                                  expected_formula, 
                                                                                                  lpd.formula, 
                                                                                                  i + 1))

    def test_str_reorder_chains_sn_not_known(self):
        """ tests that the chains in __str__ output are reordered in descending carbon count then unsaturation count if sn-position not known """
        # TG 14:0_15:1_16:2
        lpd_a = LipidWithChains("LMGL0301", [14, 15, 16], [0, 1, 2])
        # TG 15:1_14:0_16:2
        lpd_b = LipidWithChains("LMGL0301", [15, 14, 16], [1, 0, 2])
        # TG 16:2_15:1_14:0
        lpd_c = LipidWithChains("LMGL0301", [16, 15, 14], [2, 1, 0])
        # all of these should produce the same str(): TG 16:2_15:1_14:0
        self.assertEqual(str(lpd_a), "TG 16:2_15:1_14:0",
                         msg="str(lpd_a) should be TG 16:2_15:1_14:0, was {}".format(str(lpd_a)))
        self.assertEqual(str(lpd_b), "TG 16:2_15:1_14:0",
                         msg="str(lpd_b) should be TG 16:2_15:1_14:0, was {}".format(str(lpd_b)))
        self.assertEqual(str(lpd_c), "TG 16:2_15:1_14:0",
                         msg="str(lpd_c) should be TG 16:2_15:1_14:0, was {}".format(str(lpd_c)))


if __name__ == '__main__':
    # run all defined TestCases for only this module if invoked directly
    unittest.main(verbosity=2)

