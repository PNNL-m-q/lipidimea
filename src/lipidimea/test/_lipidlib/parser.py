"""
lipidlib/test/parser.py

Dylan Ross (dylan.ross@pnnl.gov)

    tests for lipidlib/parser.py module
"""


from unittest import TestCase, main as utmain


from lipidlib.parser import (
    _suffixes_combinable, _combine_o_variants, _combined_oxy_suffix_from_oxy_suffix_chains, 
    _get_lmid_prefix, parse_lipid_name
)


class Test_SuffixesCombinable(TestCase):
    """ tests for the _suffixes_combinable function """

    def test_O_variants(self):
        """ tests that any combination of O variants should be combinable """
        o_variants = [
            ["O", "O"],
            ["O", "O", "O"],
            ["O", "O", "O", "O"],
            ["O", "O2"],
            ["O2", "O"],
            ["O2", "O2"],
            ["O2", "O", "O2"],
            ["O2", "O2", "O2"],
        ]
        for o_variant in o_variants:
            combinable, mod_type = _suffixes_combinable(o_variant)
            self.assertTrue(combinable,
                            msg="O variant {} should be combinable".format(o_variant))
            self.assertEqual(mod_type, "O",
                             msg="O variant {} should have had modification type O (had: {})".format(o_variant, 
                                                                                                     mod_type))

    def test_oxy_suffix_combinable(self):
        """ test oxy suffix chains where suffixes are not combinable """
        oscs = [
            ["O", "Ep"],
            ["O", "Ep"],
            ["OOH", "O"],
        ]
        for osc in oscs:
            combinable, mod_type = _suffixes_combinable(osc)
            self.assertFalse(combinable,
                             msg="oxy suffixes {} should not be combinable".format(osc))
            self.assertIsNone(mod_type,
                              msg="oxy suffixes {} should have modification type None (had: {})".format(osc, mod_type))


class Test_CombineOVariants(TestCase):
    """ tests for the _combine_o_variants function """

    def test_combine_o_variants(self):
        """ test that O variants of oxy suffixes get properly combined """
        o_variants = [
            (["O", "O"], "O2"),
            (["O", "O", "O"], "O3"),
            (["O", "O", "O", "O"], "O4"),
            (["O", "O2"], "O3"),
            (["O2", "O"], "O3"),
            (["O2", "O2"], "O4"),
            (["O2", "O", "O2"], "O5"),
            (["O2", "O2", "O2"], "O6"),
        ]
        for o_variant, expected in o_variants:
            self.assertEqual(_combine_o_variants(o_variant), expected,
                            msg="O variant {} did not combine to expected ({})".format(o_variant, expected))


class Test_CombinedOxySuffixFromOxySuffixChains(TestCase):
    """ tests for the _combined_oxy_suffix_from_oxy_suffix_chains function """

    def test_oxy_suffix_all_empty(self):
        """ test combining oxy suffix chains with all empty suffixes """
        oscs = [
            [""], 
            ["", ""],
            ["", "", ""],
            ["", "", "", ""],
        ]
        for osc in oscs:
            comb = _combined_oxy_suffix_from_oxy_suffix_chains(osc)
            self.assertEqual(comb, "",
                             msg="empty oxy_suffix_chains should combine to \"\"")

    def test_oxy_suffix_single(self):
        """ test combining oxy suffix chains with single non empty values """
        oscs = [
            (["Ep"], "Ep"), 
            (["", "OOH"], "OOH"),
            (["", "O", ""], "O"),
            (["", "", "", "O4"], "O4"),
        ]
        for osc, expected in oscs:
            comb = _combined_oxy_suffix_from_oxy_suffix_chains(osc)
            self.assertEqual(comb, expected,
                             msg="empty oxy_suffix_chains should combine to {}".format(expected))

    def test_oxy_suffix_combinable(self):
        """ test oxy suffix chains where suffixes are combinable """
        oscs = [
            (["O", "O"], "O2"),
            (["O", "O", "O"], "O3"),
            (["O", "O", "O", "O"], "O4"),
            (["O", "O2"], "O3"),
            (["O2", "O"], "O3"),
            (["O2", "O2"], "O4"),
            (["O2", "O", "O2"], "O5"),
            (["O2", "O2", "O2"], "O6"),
        ]
        for osc, expected in oscs:
            comb = _combined_oxy_suffix_from_oxy_suffix_chains(osc)
            self.assertEqual(comb, expected,
                             msg="oxy suffixes {} did not combine to expected ({})".format(osc, expected))

    def test_oxy_suffix_not_combinable(self):
        """ test oxy suffix chains where suffixes are not combinable """
        oscs = [
            ["O", "Ep"],
            ["O", "", "Ep"],
            ["", "OOH", "O"],
        ]
        for osc in oscs:
            comb = _combined_oxy_suffix_from_oxy_suffix_chains(osc)
            self.assertIsNone(comb,
                              msg="oxy suffixes {} should have combined to None".format(osc))


class Test_GetLmidPrefix(TestCase):
    """ tests for the _get_lmid_prefix function """

    def test_good_lmid_prefixes(self):
        """ run _get_lmid_prefix on a few examples that should work, ensure the correct prefix is returned """
        test_lipids = [
            # ((class_abbrev, fa_mod, n_unsat, oxy_suffix), expected LMID prefix),
            (("FA", "", 0, ""), "LMFA0101"),
            (("FA", "", 1, ""), "LMFA0103"),
            (("CAR", "", 0, ""), "LMFA0707"),
            (("MG", "", 0, ""), "LMGL0101"),
            (("DG", "", 0, ""), "LMGL0201"),
            (("TG", "", 0, ""), "LMGL0301"),
            (("TG", "O-", 0, ""), "LMGL0302"),
            (("MGDG", "", 0, ""), "LMGL0501AA"),
            (("DGDG", "", 0, ""), "LMGL0501AD"),
            (("PC", "", 0, ""), "LMGP0101"),
            (("PC", "O-", 0, ""), "LMGP0102"),
            (("PC", "P-", 0, ""), "LMGP0103"),
            (("LPC", "", 0, ""), "LMGP0105"),
            (("LPC", "O-", 0, ""), "LMGP0106"),
            (("LPC", "P-", 0, ""), "LMGP0107"),
            (("PE", "", 0, ""), "LMGP0201"),
            (("PE", "O-", 0, ""), "LMGP0202"),
            (("PE", "P-", 0, ""), "LMGP0203"),
            (("LPE", "", 0, ""), "LMGP0205"),
            (("LPE", "O-", 0, ""), "LMGP0206"),
            (("LPE", "P-", 0, ""), "LMGP0207"),
            (("PS", "", 0, ""), "LMGP0301"),
            (("PS", "O-", 0, ""), "LMGP0302"),
            (("PS", "P-", 0, ""), "LMGP0303"),
            (("LPS", "", 0, ""), "LMGP0305"),
            (("LPS", "O-", 0, ""), "LMGP0306"),
            (("LPS", "P-", 0, ""), "LMGP0307"),
            (("PG", "", 0, ""), "LMGP0401"),
            (("PG", "O-", 0, ""), "LMGP0402"),
            (("PG", "P-", 0, ""), "LMGP0403"),
            (("LPG", "", 0, ""), "LMGP0405"),
            (("LPG", "O-", 0, ""), "LMGP0406"),
            (("LPG", "P-", 0, ""), "LMGP0407"),
            (("PI", "", 0, ""), "LMGP0601"),
            (("PI", "O-", 0, ""), "LMGP0602"),
            (("PI", "P-", 0, ""), "LMGP0603"),
            (("LPI", "", 0, ""), "LMGP0605"),
            (("LPI", "O-", 0, ""), "LMGP0606"),
            (("LPI", "P-", 0, ""), "LMGP0607"),
            (("PIP", "", 0, ""), "LMGP0701"),
            (("LPIP", "", 0, ""), "LMGP0705"),
            (("PIP2", "", 0, ""), "LMGP0801"),
            (("PIP3", "", 0, ""), "LMGP0901"),
            (("PA", "", 0, ""), "LMGP1001"),
            (("PA", "O-", 0, ""), "LMGP1002"),
            (("PA", "P-", 0, ""), "LMGP1003"),
            (("LPA", "", 0, ""), "LMGP1005"),
            (("LPA", "O-", 0, ""), "LMGP1006"),
            (("LPA", "P-", 0, ""), "LMGP1007"),
            (("CL", "", 0, ""), "LMGP1201"),
            (("Cer", "", 0, "O2"), "LMSP0201"),
            (("SM", "", 0, "O2"), "LMSP0301"),
            (("HexCer", "", 0, "O2"), "LMSP0501AA"),
            (("Hex2Cer", "", 0, "O2"), "LMSP0501AB"),
            (("CE", "", 0, ""), "LMST0102"),
            #(("", "", , ""), ""),
        ]
        for lipid_info, expected in test_lipids:
            prefix = _get_lmid_prefix(*lipid_info)
            self.assertEqual(prefix, expected,
                             msg="lipid info {} should correspond to LMID prefix {} (got: {})".format(lipid_info, 
                                                                                                      expected, 
                                                                                                      prefix))
            
    def test_bad_lmid_prefixes(self):
        """ run _get_lmid_prefix on a few examples that should not work, ensure None is returned """
        test_lipids = [
            # ((class_abbrev, fa_mod, n_unsat, oxy_suffix), fail_reason),
            (("undefined lipid_class_abbrev", "", 0, ""), "not a defined lipid class abbreviation"),
            (("PC", "unrecognized fa_mod", 0, ""), "unrecognized FA modifier for normal PC"),
            (("PC", "", 0, "O2"), "no classification for oxidized glycerophospholipids yet"),
            (("SM", "", 0, ""), "SM class should have O2 oxy suffix (1)"),
            (("SM", "", 0, "O3"), "SM class should have O2 oxy suffix (2)"),
        ]
        for lipid_info, fail_reason in test_lipids:
            prefix = _get_lmid_prefix(*lipid_info)
            self.assertIsNone(prefix,
                                msg="should have gotten None as LMID prefix, " + fail_reason)


class TestParseLipidName(TestCase):
    """ tests for the parse_lipid_name function """

    def test_good_lipids_sum_comp(self):
        """ tests some example lipid names at sum compoision level that should all work """
        test_lipids = [
            # (lipid_name, (lmid_prefix, fa_carbon, fa_unsat))
            ("PC 34:1", ("LMGP0101", 34, 1)),
            ("PC O-34:1", ("LMGP0102", 34, 1)),
            ("PC P-34:1", ("LMGP0103", 34, 1)),
            ("LPC 18:1", ("LMGP0105", 18, 1)),
            ("LPC O-18:1", ("LMGP0106", 18, 1)),
            ("LPC P-18:1", ("LMGP0107", 18, 1)),
            ("SM 34:1;O2", ("LMSP0301", 34, 1)),
        ]
        for name, (lmid_prefix, sum_c, sum_u) in test_lipids:
            lpd = parse_lipid_name(name)
            self.assertEqual(lpd.lmaps_id_prefix, lmid_prefix,
                             msg="incorrect LMID prefix, expected: {} was: {}".format(lmid_prefix, 
                                                                                      lpd.lmaps_id_prefix))
            self.assertEqual(lpd.fa_carbon, sum_c,
                             msg="incorrect sum carbons, expected: {} was: {}".format(sum_c, 
                                                                                      lpd.fa_carbon))
            self.assertEqual(lpd.fa_unsat, sum_u,
                             msg="incorrect sum unsaturation, expected: {} was: {}".format(sum_u, 
                                                                                           lpd.fa_unsat))

    def test_good_lipids_with_chains(self):
        """ tests some example lipid names with individual chains specified that should all work """
        test_lipids = [
            # (lipid_name, (lmid_prefix, fa_carbon_chains, fa_unsat_chains, sn_pos_is_known))
            ("PC 18:1_16:0", ("LMGP0101", [18, 16], [1, 0], False)),
            ("PC 18:1/16:0", ("LMGP0101", [18, 16], [1, 0], True)),
            ("PC O-18:1_16:0", ("LMGP0102", [18, 16], [1, 0], False)),
            ("PC O-18:1/16:0", ("LMGP0102", [18, 16], [1, 0], True)),
            ("PC P-18:1_16:0", ("LMGP0103", [18, 16], [1, 0], False)),
            ("PC P-18:1/16:0", ("LMGP0103", [18, 16], [1, 0], True)),
            ("LPC 18:1", ("LMGP0105", [18, 0], [1, 0], False)),
            ("LPC O-18:1", ("LMGP0106", [18, 0], [1, 0], False)),
            ("LPC P-18:1", ("LMGP0107", [18, 0], [1, 0], False)),
            ("SM 18:1;O2_16:0", ("LMSP0301", [18, 16], [1, 0], False)),
            ("SM 18:1;O2/16:0", ("LMSP0301", [18, 16], [1, 0], True)),
        ]
        for name, (lmid_prefix, c_chains, u_chains, sn_pos) in test_lipids:
            lpd = parse_lipid_name(name)
            self.assertEqual(lpd.lmaps_id_prefix, lmid_prefix,
                             msg="incorrect LMID prefix, expected: {} was: {}".format(lmid_prefix, 
                                                                                      lpd.lmaps_id_prefix))
            self.assertEqual(lpd.fa_carbon_chains, c_chains,
                             msg="incorrect sum carbons, expected: {} was: {}".format(c_chains, 
                                                                                      lpd.fa_carbon_chains))
            self.assertEqual(lpd.fa_unsat_chains, u_chains,
                             msg="incorrect sum unsaturation, expected: {} was: {}".format(u_chains, 
                                                                                           lpd.fa_unsat_chains))
            self.assertEqual(lpd.sn_pos_is_known, sn_pos,
                             msg="incorrect sn_position_is_known, expected: {} was: {}".format(sn_pos, 
                                                                                               lpd.sn_pos_is_known))

    def test_lyso_lipids(self):
        """ tests some examples of lyso lipids which can be parsed with or without explicit 0:0 """
        test_lipids = [
            # (lipid_name, (lmid_prefix, fa_carbon_chains, fa_unsat_chains, sn_pos_is_known))
            ("LPC 18:1", ("LMGP0105", [18, 0], [1, 0], False)),
            ("LPC O-18:1", ("LMGP0106", [18, 0], [1, 0], False)),
            ("LPC 18:1_0:0", ("LMGP0105", [18, 0], [1, 0], False)),
            ("LPC O-18:1_0:0", ("LMGP0106", [18, 0], [1, 0], False)),
            ("LPC 18:1/0:0", ("LMGP0105", [18, 0], [1, 0], True)),
            ("LPC O-18:1/0:0", ("LMGP0106", [18, 0], [1, 0], True)),
            ("LPC 0:0/18:1", ("LMGP0105", [0, 18], [0, 1], True)),
            ("LPC O-0:0/18:1", ("LMGP0106", [0, 18], [0, 1], True)),
        ]
        for name, (lmid_prefix, c_chains, u_chains, sn_pos) in test_lipids:
            lpd = parse_lipid_name(name)
            self.assertEqual(lpd.lmaps_id_prefix, lmid_prefix,
                             msg="incorrect LMID prefix, expected: {} was: {}".format(lmid_prefix, 
                                                                                      lpd.lmaps_id_prefix))
            self.assertEqual(lpd.fa_carbon_chains, c_chains,
                             msg="incorrect sum carbons, expected: {} was: {}".format(c_chains, 
                                                                                      lpd.fa_carbon_chains))
            self.assertEqual(lpd.fa_unsat_chains, u_chains,
                             msg="incorrect sum unsaturation, expected: {} was: {}".format(u_chains, 
                                                                                           lpd.fa_unsat_chains))
            self.assertEqual(lpd.sn_pos_is_known, sn_pos,
                             msg="incorrect sn_position_is_known, expected: {} was: {}".format(sn_pos, 
                                                                                               lpd.sn_pos_is_known))

    def test_bad_lipids(self):
        """ tests some example lipid names that should all not work, returning None """
        test_lipids = [
            # (lipid_name, fail_reason)
            ("not a lipid", "not a lipid"),
            ("PC(34:1)", "wrong lipid name format"),
            ("PC 34:1_A;PC 34:1_B", "valid name but stuff comes after it")
        ]
        for name, fail_reason in test_lipids:
            lpd = parse_lipid_name(name)
            self.assertIsNone(lpd,
                              msg="should have gotten None from parse_lipid, " + fail_reason)


if __name__ == '__main__':
    # run all defined TestCases for only this module if invoked directly
    utmain(verbosity=2)