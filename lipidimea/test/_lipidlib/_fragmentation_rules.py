"""
lipidlib/test/_fragmentation_rules.py

Dylan Ross (dylan.ross@pnnl.gov)

    tests for the lipidlib/_fragmentation_rules.py module
"""


from unittest import TestCase, main as utmain

from lipidlib._fragmentation_rules import (
    _FragRule, _FragRuleStatic, _FragRuleDynamic, load_rules
)


class Test_FragRule(TestCase):
    """ tests for the _FragRule class """

    def test_init_fragrule_no_errs(self):
        """ initialize a _FragRule object, there should be no errors """
        fr = _FragRule(True, "label", {"C": 1, "H": 4}, False, False, None)

    def test_init_fragrule_static_false_n_chains_none(self):
        """ initialize _FragRule with static set to False and n_chains set to None, should raise an error """
        with self.assertRaises(ValueError, 
                               msg="should have gotten a ValueError for static=False and n_chains=None"):
            fr = _FragRule(False, "label", {"C": 1, "H": 4}, False, False, None)

    def test_init_fragrule_bad_formula(self):
        """ initialize _FragRule objects with bad formulas, these should raise errors """
        # unrecognized element in formula
        with self.assertRaises(ValueError,
                               msg="should have gotten a ValueError for unrecognized element"):
            rule = {"C": 1, "H": 4, "bad element": 1}
            fr = _FragRule(True, "label", rule, False, False, None)
        # negative element count
        with self.assertRaises(ValueError,
                               msg="should have gotten a ValueError for negative element count"):
            rule = {"C": 1, "H": 4, "O": -1}
            fr = _FragRule(True, "label", rule, False, False, None)
        # dynamic rule but specified static=True
        with self.assertRaises(ValueError,
                               msg="should have gotten a ValueError for a dynamic rule definition but static set to True"):
            rule = {"C": 1, "H": 4, "O": "c"}
            fr = _FragRule(True, "label", rule, False, False, None)
        # bad expression in dynamic rule definition
        with self.assertRaises(ValueError,
                               msg="should have gotten a ValueError for bad expression in dynamic rule definition"):
            rule = {"C": 1, "H": 4, "O": "bad expression"}
            fr = _FragRule(False, "label", rule, False, False, None)
    
    def test_mz_neutral_loss(self):
        """ test the _FragRule._mz() method with and without neutral loss set """
        # not a neutral loss
        fr = _FragRule(True, "label", {"C": 1, "H": 4}, False, False, None)
        self.assertEqual(fr._mz(1., 3., None), 1.,
                         msg="incorrect value returned from _mz method")
        # neutral loss
        fr = _FragRule(True, "label", {"C": 1, "H": 4}, False, True,  None)
        self.assertEqual(fr._mz(1., 3., None), 2.,
                         msg="incorrect value returned from _mz method")

    def test_mz_deuterium_labeled(self):
        """ test the _FragRule._mz() method with deuterium label """
        # not a neutral loss
        fr = _FragRule(True, "label", {"C": 1, "H": 4}, False, False, None)
        self.assertAlmostEqual(fr._mz(0., 0., 1), 1.006277,
                         msg="incorrect value returned from _mz method")
        # neutral loss
        fr = _FragRule(True, "label", {"C": 1, "H": 4}, False, True,  None)
        self.assertAlmostEqual(fr._mz(0., 0., 1), -1.006277,
                         msg="incorrect value returned from _mz method")

    def test_label_diagnostic(self):
        """ test the _label() method of _FragRule, a '*' should be added in front of diagnostic fragment labels """
        # not diagnostic
        fr = _FragRule(True, "label", {"C": 1, "H": 4}, False, False, None)
        self.assertEqual(fr._label(), "label",
                         msg="label should not have had * prepended")
        # diagnostic
        fr = _FragRule(True, "label", {"C": 1, "H": 4}, True, False, None)
        self.assertEqual(fr._label(), "*label", 
                         msg="label should have had * prepended")


class Test_FragRuleStatic(TestCase):
    """ tests for the _FragRuleStatic class """

    def test_mz_neutral_loss(self):
        """ test the _FragRuleStatic.mz() method with and without neutral loss set """
        # not a neutral loss
        frs = _FragRuleStatic("label", {"C": 1, "H": 4})  # diagnostic=False, neutral_loss=False
        self.assertAlmostEqual(frs.mz(0.), 16.0313,
                         msg="incorrect value returned from mz method") 
        # neutral loss
        frs = _FragRuleStatic("label", {"C": 1, "H": 4}, neutral_loss=True)  # diagnostic=False
        self.assertAlmostEqual(frs.mz(0.), -16.0313,
                         msg="incorrect value returned from mz method")

    def test_mz_deuterium_labeled(self):
        """ test the _FragRuleStatic.mz() method with deuterium label """
        # not a neutral loss
        frs = _FragRuleStatic("label", {"C": 1, "H": 4})  # diagnostic=False, neutral_loss=False
        self.assertAlmostEqual(frs.mz(0., d_label=1), 17.037577,
                         msg="incorrect value returned from mz method") 
        # neutral loss
        frs = _FragRuleStatic("label", {"C": 1, "H": 4}, neutral_loss=True)  # diagnostic=False
        self.assertAlmostEqual(frs.mz(0., d_label=1), -17.037577,
                         msg="incorrect value returned from mz method") 
    

class Test_FragRuleDynamic(TestCase):
    """ tests for the _FragRuleDynamic class """

    def test_mz_neutral_loss(self):
        """ test the _FragRuleDynamic.mz() method with and without neutral loss set """
        # not a neutral loss
        frd = _FragRuleDynamic("label", {"C": "c", "H": "2 * (c - u + 1)"}, 1)  # diagnostic=False, neutral_loss=False
        self.assertAlmostEqual(frd.mz(0., 8, 1), 112.125201,
                               msg="incorrect value returned from mz method") 
        # neutral loss
        frd = _FragRuleDynamic("label", {"C": "c", "H": "2 * (c - u + 1)"}, 1, neutral_loss=True)  # diagnostic=False
        self.assertAlmostEqual(frd.mz(0., 8, 1), -112.125201,
                               msg="incorrect value returned from mz method")

    def test_mz_deuterium_labeled(self):
        """ test the _FragRuleDynamic.mz() method with deuterium label """
        # not a neutral loss
        frd = _FragRuleDynamic("label", {"C": "c", "H": "2 * (c - u + 1)"}, 1)  # diagnostic=False, neutral_loss=False
        self.assertAlmostEqual(frd.mz(0., 8, 1, d_label=1), 112.125201 + 1.006277,
                               msg="incorrect value returned from mz method") 
        # neutral loss
        frd = _FragRuleDynamic("label", {"C": "c", "H": "2 * (c - u + 1)"}, 1, neutral_loss=True)  # diagnostic=False
        self.assertAlmostEqual(frd.mz(0., 8, 1, d_label=1), -112.125201 - 1.006277,
                               msg="incorrect value returned from mz method")

    def test_dynamic_labels(self):
        """ test the _FragRuleDynamic.label() method with different label formats and c and u values """
        frd = _FragRuleDynamic("label({c}:{u})", {"C": 1, "H": 4}, 1)
        self.assertEqual(frd.label(8, 1), "label(8:1)",
                         msg="incorrect dynamic label")
        self.assertEqual(frd.label(22, 2), "label(22:2)",
                         msg="incorrect dynamic label")
        frd = _FragRuleDynamic("label({u}:{c})", {"C": 1, "H": 4}, 1)
        self.assertEqual(frd.label(8, 1), "label(1:8)",
                         msg="incorrect dynamic label")
        self.assertEqual(frd.label(22, 2), "label(2:22)",
                         msg="incorrect dynamic label")
        frd = _FragRuleDynamic("label({c}:)", {"C": 1, "H": 4}, 1)
        self.assertEqual(frd.label(8, 1), "label(8:)",
                         msg="incorrect dynamic label")
        frd = _FragRuleDynamic("label(:{u})", {"C": 1, "H": 4}, 1)
        self.assertEqual(frd.label(8, 1), "label(:1)",
                         msg="incorrect dynamic label")

    def test_label_diagnostic(self):
        """ test the _FragRuleDynamic.label() method, a '*' should be added in front of diagnostic fragment labels """
        # not diagnostic
        frd = _FragRuleDynamic("label({c}:{u})", {"C": 1, "H": 4}, 1)
        self.assertEqual(frd.label(8, 1), "label(8:1)",
                         msg="label should not have had * prepended")
        # diagnostic
        frd = _FragRuleDynamic("label({c}:{u})", {"C": 1, "H": 4}, 1, diagnostic=True)
        self.assertEqual(frd.label(8, 1), "*label(8:1)", 
                         msg="label should have had * prepended")


class TestLoadRules(TestCase):
    """ tests for the load_rules function """

    def test_bad_ionization(self):
        """ call load_rules with an invalid value for ionization param, should raise an error """
        with self.assertRaises(ValueError, 
                               msg="should have gotten a ValueError for invalid ionization param"):
            load_rules("arbitrary_lmid_prefix", "bad_ionization")

    def test_undefined_lmid_prefix(self):
        """ call load_rules with an undefined LMID prefix, should still load the "any" rules """
        found, rules = load_rules("undefined_lmid_prefix", "POS")
        # first, the found flag must be False
        self.assertFalse(found,
                         msg="found flag should have been False")
        # next, make sure the proper number of rules were loaded from any.yml
        self.assertAlmostEqual(len(rules), 6,
                               msg="6 rules should have been loaded from any.yml")

    def test_pe_pos_neg_rules(self):
        """ load rules for the PE class for POS and NEG ionization modes, make sure correct number are loaded """
        # POS
        found, rules = load_rules("LMGP0201", "POS")
        self.assertTrue(found, 
                        msg="found flag should have been True")
        self.assertEqual(len(rules), 9,
                         "9 rules should have been loaded (6 from any + 3 from class)")
        # NEG
        found, rules = load_rules("LMGP0201", "NEG")
        self.assertTrue(found, 
                        msg="found flag should have been True")
        self.assertEqual(len(rules), 11,
                         msg="11 rules should have been loaded (4 from any + 7 from class)")

    def test_pc_neg_rules(self):
        """ load rules for the PC class for NEG ionization modes, there should be only the any rules """
        found, rules = load_rules("LMGP0101", "NEG")
        self.assertFalse(found, 
                        msg="found flag should have been False")
        self.assertEqual(len(rules), 4,
                         msg="4 rules should have been loaded from any.yml")


if __name__ == '__main__':
    # run all defined TestCases for only this module if invoked directly
    utmain(verbosity=2)

