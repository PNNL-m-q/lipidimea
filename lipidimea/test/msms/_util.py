"""
lipidimea/test/msms/_util.py

Dylan Ross (dylan.ross@pnnl.gov)

    tests for the lipidimea/msms/_util.py module
"""


import unittest

import numpy as np

from lipidimea.msms._util import (
    ms2_to_str, 
    str_to_ms2, 
    apply_args_and_kwargs,
    ppm_from_delta_mz,
    tol_from_ppm
)


class TestMS2ToStr(unittest.TestCase):
    """ tests for the ms2_to_str function """

    def test_MTS_empty_arrays(self):
        """ empty arrays as inputs causes a ValueError """
        with self.assertRaises(ValueError,
                               msg="empty arrays should cause an error"):
            mzs, iis, = np.array([]), np.array([])
            s = ms2_to_str(mzs, iis)

    def test_MTS_unbalanced_arrays(self):
        """ arrays with different lengths as inputs causes a ValueError """
        with self.assertRaises(ValueError,
                               msg="arrays with mismatched lengths should cause an error"):
            mzs, iis, = np.array([1.234, 2.345, 3.456]), np.array([100., 200.])
            s = ms2_to_str(mzs, iis)

    def test_MTS_expected_outputs(self):
        """ ensure the expected output strings are produced from known input arrays """
        expected = [
            # (input arrays, output string)
            ((np.array([1.]), np.array([234])), "1.0000:234"),
            ((np.array([1., 2.]), np.array([234, 345])), "1.0000:234 2.0000:345"),
            ((np.array([1.23456789, 2.34567890, 5.678901234]), np.array([12346, 23457, 56789])), "1.2346:12346 2.3457:23457 5.6789:56789"),
        ]
        for (mzs, iis), exp in expected:
            s = ms2_to_str(mzs, iis)
            self.assertEqual(s, exp,
                             msg=f"expected string '{exp}', got string '{s}'")


class TestStrToMS2(unittest.TestCase):
    """ tests for the str_to_ms2 function """

    def test_STM_bad_str_formats(self):
        """ bad spectrum string formats should raise ValueErrors """
        bads = [
            "", "bad spectrum string",
            "1", "1:", "1.:", "1.:1.", 
            "1.:1 1", "1.:1 1:", "1.:1 1.:", "1.:1 1.:1."
        ]
        for bad in bads:
            with self.assertRaises(ValueError,
                                   msg=f"spectrum string '{bad}' should have cause ValueError"):
                mzs, iis = str_to_ms2(bad)
    
    def _arrays_length_and_content_match(self, a, a_exp, a_label):
        """
        helper method that compares the lengths and contents of a and a_exp
        """
        self.assertEqual(len(a), len(a_exp),
                         msg=f"incorrect length of {a_label} array")
        for v, v_exp in zip(a, a_exp):
            self.assertEqual(v, v_exp,
                             msg=f"element {v} of {a_label} array does not match expected value ({v_exp})")

    def test_STM_expected_outputs(self):
        """ good spectrum strings should produce the expected output arrays """
        expected = [
            # (spectrum string, output arrays)
            ("1.:1", (np.array([1.]), np.array([1.]))),
            ("1.:1 2.:2", (np.array([1., 2.]), np.array([1., 2.]))),
            ("1.:1   2.:2", (np.array([1., 2.]), np.array([1., 2.]))),
            ("1.1:1 2.2:2", (np.array([1.1, 2.2]), np.array([1., 2.]))),
            ("1.11111:1   2.22222:2", (np.array([1.11111, 2.22222]), np.array([1., 2.]))),
        ]
        for s, (exp_mzs, exp_iis) in expected:
            mzs, iis = str_to_ms2(s)
            self._arrays_length_and_content_match(mzs, exp_mzs, "mzs")
            self._arrays_length_and_content_match(iis, exp_iis, "iis")
            

# static return value for apply_args_and_kwargs helper functions
_HELPER_VALUE = 420


# trivial helper function for testing apply_args_and_kwargs function
def _helper_no_args_no_kwargs(
                              ) -> int:
    """ take no args, no kwargs, always returns _HELPER_VALUE """
    return _HELPER_VALUE


# trivial helper function for testing apply_args_and_kwargs function
def _helper_one_arg_no_kwargs(arg: int
                              ) -> int:
    """ takes one arg (an int), no kwargs, always returns _HELPER_VALUE + arg """
    return _HELPER_VALUE + arg


# trivial helper function for testing apply_args_and_kwargs function
def _helper_two_args_no_kwargs(arg1: int, arg2: int
                               ) -> int:
    """ takes two args (ints), no kwargs, always returns _HELPER_VALUE + arg1 + arg2 """
    return _HELPER_VALUE + arg1 + arg2


# trivial helper function for testing apply_args_and_kwargs function
def _helper_no_args_one_kwarg(kwarg: int = 0
                              ) -> int:
    """ take no args, one kwarg (int, default=0), always returns _HELPER_VALUE + kwarg """
    return _HELPER_VALUE + kwarg


# trivial helper function for testing apply_args_and_kwargs function
def _helper_no_args_two_kwargs(kwarg1: int = 0, kwarg2: int = 0
                               ) -> int:
    """ take no args, two kwargs (ints, default=0), always returns _HELPER_VALUE + kwarg1 + kwarg2 """
    return _HELPER_VALUE + kwarg1 + kwarg2


# trivial helper function for testing apply_args_and_kwargs function
def _helper_two_args_two_kwargs(arg1: int, arg2: int,
                                kwarg1: int = 0, kwarg2: int = 0
                                ) -> int:
    """ 
        take two args (ints), two kwargs (ints, default=0), 
        always returns _HELPER_VALUE + arg1 + arg2 + kwarg1 + kwarg2 
    """
    return _HELPER_VALUE + arg1 + arg2 + kwarg1 + kwarg2


class TestApplyArgsAndKwargs(unittest.TestCase):
    """ tests for the apply_args_and_kwargs function """

    def test_AAAK_no_args_no_kwargs(self):
        """ wrap a function without args or kwargs """
        self.assertEqual(apply_args_and_kwargs(_helper_no_args_no_kwargs, [], {}), _HELPER_VALUE,
                         msg="did not get correct return value from wrapped function")
    
    def test_AAAK_one_arg_no_kwargs(self):
        """ wrap a function with one arge and no kwargs """
        self.assertEqual(apply_args_and_kwargs(_helper_one_arg_no_kwargs, [1], {}), _HELPER_VALUE + 1,
                         msg="did not get correct return value from wrapped function")

    def test_AAAK_two_args_no_kwargs(self):
        """ wrap a function with two args and no kwargs """
        self.assertEqual(apply_args_and_kwargs(_helper_two_args_no_kwargs, [1, 2], {}), _HELPER_VALUE + 3,
                         msg="did not get correct return value from wrapped function")

    def test_AAAK_no_args_one_kwarg(self):
        """ wrap a function with no args and one kwarg """
        self.assertEqual(apply_args_and_kwargs(_helper_no_args_one_kwarg, [], {}), _HELPER_VALUE,
                         msg="did not get correct return value from wrapped function")
        self.assertEqual(apply_args_and_kwargs(_helper_no_args_one_kwarg, [], {"kwarg": 1}), _HELPER_VALUE + 1,
                         msg="did not get correct return value from wrapped function")

    def test_AAAK_no_args_two_kwargs(self):
        """ wrap a function with no args and two kwargs """
        self.assertEqual(apply_args_and_kwargs(_helper_no_args_two_kwargs, [], {}), _HELPER_VALUE,
                         msg="did not get correct return value from wrapped function")
        self.assertEqual(apply_args_and_kwargs(_helper_no_args_two_kwargs, [], {"kwarg1": 1}), _HELPER_VALUE + 1,
                         msg="did not get correct return value from wrapped function")
        self.assertEqual(apply_args_and_kwargs(_helper_no_args_two_kwargs, [], {"kwarg2": 1}), _HELPER_VALUE + 1,
                         msg="did not get correct return value from wrapped function")
        self.assertEqual(apply_args_and_kwargs(_helper_no_args_two_kwargs, [], {"kwarg1": 1, "kwarg2": 2}), _HELPER_VALUE + 3,
                         msg="did not get correct return value from wrapped function")

    def test_AAAK_two_args_two_kwargs(self):
        """ wrap a function with two args and two kwargs """
        self.assertEqual(apply_args_and_kwargs(_helper_two_args_two_kwargs, [1, 2], {}), _HELPER_VALUE + 3,
                         msg="did not get correct return value from wrapped function")
        self.assertEqual(apply_args_and_kwargs(_helper_two_args_two_kwargs, [1, 2], {"kwarg1": 3}), _HELPER_VALUE + 6,
                         msg="did not get correct return value from wrapped function")
        self.assertEqual(apply_args_and_kwargs(_helper_two_args_two_kwargs, [1, 2], {"kwarg2": 3}), _HELPER_VALUE + 6,
                         msg="did not get correct return value from wrapped function")
        self.assertEqual(apply_args_and_kwargs(_helper_two_args_two_kwargs, [1, 2], {"kwarg1": 3, "kwarg2": 4}), _HELPER_VALUE + 10,
                         msg="did not get correct return value from wrapped function")


class TestPPMFromDeltaMz(unittest.TestCase):
    """ tests for the ppm function """
    
    def test_PFDM_correct_ppms(self):
        """ ensure correct ppms get calculated """
        expected = [
            # (mz, expected ppm, delta_mz)
            (500, 5, 0.0025),
            (500, 10, 0.0050),
            (500, 50, 0.0250),
            (1000, 5, 0.0050),
            (1000, 10, 0.0100),
            (1000, 50, 0.0500),
        ]
        for mz, exp_ppm, delta_mz in expected:
            ppm = ppm_from_delta_mz(delta_mz, mz)
            self.assertAlmostEqual(ppm, exp_ppm, places=3,
                                   msg=f"with delta_mz: {delta_mz} mz: {mz}, expected ppm: {exp_ppm} (got ppm: {ppm})")


class TestTolFromPPM(unittest.TestCase):
    """ tests for the tol_from_ppm function """

    def test_TFP_correct_tolerances(self):
        """ ensure that tolerances are calculated correctly """
        expected = [
            # (mz, ppm, expected tolerance)
            (500, 5, 0.0025),
            (500, 10, 0.0050),
            (500, 50, 0.0250),
            (1000, 5, 0.0050),
            (1000, 10, 0.0100),
            (1000, 50, 0.0500),
        ]
        for mz, ppm, exp_tol in expected:
            tol = tol_from_ppm(mz, ppm)
            self.assertAlmostEqual(tol, exp_tol, places=4,
                                   msg=f"with mz: {mz} ppm: {ppm}, expected tol: {exp_tol} (got tol: {tol})")


if __name__ == "__main__":
    # run the tests for this module if invoked directly
    unittest.main(verbosity=2)
