"""
lipidimea/_lipidlib/parser.py
Dylan Ross (dylan.ross@pnnl.gov)

    module for parsing lipids from strings
"""


from typing import List, Optional, Tuple, Union, Dict, Any
import re

from .lipids import LMAPS, Lipid, LipidWithChains


# regex for parsing lipid information from a lipid name in standard abbreviated format
# in order to keep it readable I have included a bunch of indentation, but at execution
# time this gets stripped out and the "[SPACE]" token gets replaced with an actual space
# where it is needed in the pattern
_LIPID_NAME_REGEX = re.sub(r"\s+", "", """
    ^
    (?P<lcl>
        [A-Za-z123]+
    )
    [SPACE]
    (?P<fam>
        O-|P-|d
    )?
    (
        (?P<fac_1>
            [0-9]+
        )
        :
        (?P<fau_1>
            [0-9]+
        )
        (?P<fadb_1>
            [(]
            [0-9]+
            [EZ]*
            (
                ,
                [0-9]+
                [EZ]*
            )*
            [)]
        )?
        (
            ;(?P<oxsf_1>O[0-9]*H*|Ep|OOH)
        )?
    )
    (
        (?P<sn>
            [/_]
        )
        (
            (?P<fac_2>
            [0-9]+
            )
            :
            (?P<fau_2>
                [0-9]+
            )
            (?P<fadb_2>
                [(]
                [0-9]+
                [EZ]*
                (
                    ,
                    [0-9]+
                    [EZ]*
                )*
                [)]
            )?
            (
                ;(?P<oxsf_2>O[0-9]*H*|Ep|OOH)
            )?
        )
    )?
    (
        [/_]
        (
            (?P<fac_3>
            [0-9]+
            )
            :
            (?P<fau_3>
                [0-9]+
            )
            (?P<fadb_3>
                [(]
                [0-9]+
                [EZ]*
                (
                    ,
                    [0-9]+
                    [EZ]*
                )*
                [)]
            )?
            (
                ;(?P<oxsf_3>O[0-9]*H*|Ep|OOH)
            )?
        )
    )?
    (
        [/_]
        (
            (?P<fac_4>
            [0-9]+
            )
            :
            (?P<fau_4>
                [0-9]+
            )
            (?P<fadb_4>
                [(]
                [0-9]+
                [EZ]*
                (
                    ,
                    [0-9]+
                    [EZ]*
                )*
                [)]
            )?
            (
                ;(?P<oxsf_4>O[0-9]*H*|Ep|OOH)
            )?
        )
    )?
    $
""").replace('[SPACE]', '[ ]')


def _suffixes_combinable(suffixes: List[str]) -> Tuple[bool, Optional[str]]:
    """ 
    determine if the list of suffixes is combinable

    Parameters
    ----------
    suffixes : ``list(str)``
        list of suffixes
    
    Returns
    -------
    combinable : ``bool``
        flag indicating if suffixes are combinable
    mod_type : ``str`` or ``None``
        type of oxidized modifications to combine, "O" or None 
    """
    # check for O variants
    all_o_variants = True  # flag indicating that all suffixes are O variants
    for suffix in suffixes:
        if len(suffix) < 3:
            if suffix[0] == "O":
                if len(suffix) > 1 and not suffix[1].isdigit():
                    all_o_variants = False
            else:
                all_o_variants = False
        else:
            all_o_variants = False
    if all_o_variants:
        return True, "O"
    #TODO: check for other modifications like Ep or OOH
    # assume False for any cases not explicitly covered
    return False, None


def _combine_o_variants(suffixes: List[str]) -> str:
    """
    combine variants of O (O, O1, O2 ...)

    Parameters
    ----------
    suffixes : ``list(str)``
        list of suffixes
    
    Returns
    -------
    combined : ``str``
        combined oxy suffix
    """
    cnt = 0
    for suffix in suffixes:
        if len(suffix) > 1:
            cnt += int(suffix[1])
        else:
            cnt += 1
    return "O{}".format(cnt)


def _combined_oxy_suffix_from_oxy_suffix_chains(oxy_suffix_chains: List[str]) -> Optional[str]:
    """
    come up with a single oxy suffix value from possibly multiple values from different chains
    so that the LMAPS ID prefix can be looked up. 

    TODO: Need to come up with whatever appropriate sematics for combining multiple oxy suffixes.
            For instance ['O', 'O', ''] should resolve to 'O2', but what should happen with 
            something like ['O', 'Ep', 'OOH']? No clue. For now I will implement combining "like"
            suffixes (i.e., the first case above) and revisit the latter case at some later point
    
    Parameters
    ----------
    oxy_suffix_chains : ``list(str)``
        list of oxidation suffixes for each FA chain

    Returns
    -------
    combined_oxy_suffix : ``str`` or ``None``
        single combined oxidation suffix for the lipid, None if cannot be combined
    """    
    # set what functions to use for combining different mod_types
    comb_funcs = {
        "O": _combine_o_variants,
    }
    # convert oxy_suffix_chains to only non-empty oxy suffixes
    non_empty = [_ for _ in oxy_suffix_chains if _ != ""]
    if len(non_empty) == 0:
        return ""
    elif len(non_empty) == 1:
        return non_empty[0]
    else:
        combinable, mod_type = _suffixes_combinable(non_empty)
        if combinable:
            # combine "like" suffixes
            # use the appropriate combining function based on mod_type
            return comb_funcs[mod_type](non_empty)
        else:
            # else ... IDK what to do from here
            return None


def _get_lmid_prefix(lipid_class_abbrev: str, fa_mod: str, n_unsat: int, oxy_suffix: str) -> Optional[str]:
    """
    fetch specific lipid class info (using LMAPS ID prefix) based on
    lipid class abbreviation, fatty acid modifier, number of chains, and oxidation suffix

    Parameters
    ----------
    lipid_class_abbrev : ``str``

    fa_mod

    Returns
    -------
    lmid_prefix : ``str`` or ``None``
        LMAPS ID prefix or None if unable to find a matching one
    """
    for lmid_prefix, data in LMAPS.items():
        lipid_class_abbrev_ = data["class_abbrev"]
        fa_mod_ = data.get("fa_mod", "")
        n_chains_ = data["n_chains"]
        oxy_suffix_ = data.get("oxy_suffix", "")
        if (lipid_class_abbrev == lipid_class_abbrev_ and fa_mod == fa_mod_ and oxy_suffix == oxy_suffix_):
            # handle the special case of determining unsaturated vs. saturated FAs
            if lmid_prefix == "LMFA0101" and n_unsat > 0:
                return "LMFA0103"
            return lmid_prefix
    # if no prefix was found return None
    return None
    

def _try_lipid(init_args: Tuple[Any], init_kwargs: Dict[Any, Any], with_chains: bool) -> Optional[Union[Lipid, LipidWithChains]]:
    """
    Attempts to create and return a Lipid or LipidWithChains instance, 
    catches ValueErrors from cases where the parsed information was incorrect
    and returns None indicating a failure to parse. This handles cases where
    a name is technically parsable in terms of its form, but the information
    may not be correct/complete enough to initialize and actual Lipid or 
    LipidWithChains instance.

    Parameters
    ----------
    init_args : ``tuple(...)``
    init_kwargs : ``dict(...)``
        args/kwargs passed on to initialize the Lipid or LipidWithChains instance
    with_chains : ``bool``
        if true try to init a LipidWithChains instance, otherwise a Lipid instance

    Returns
    -------
    lipid : ``Lipid`` or ``LipidWithChains`` or ``None``
        instance of Lipid or LipidWithChains if successful, otherwise None
    """
    try:
        if with_chains:
            return LipidWithChains(*init_args, **init_kwargs)
        else:
            return Lipid(*init_args, **init_kwargs)
    except ValueError:
        # I think all of the validation that is done when initializing Lipid/LipidWithChains
        # should raise ValueErrors, so this should handle any of those
        return None


def parse_lipid_name(name: str) -> Optional[Union[Lipid, LipidWithChains]]:
    """
    Parses a lipid name in standard format and returns a corresponding instance of a ``Lipid`` object (or subclass). 
    If the name is not able to be parsed, returns ``None``

    Parameters
    ----------
    name : ``str``
        lipid name in standard format

    Returns
    -------
    lipid : ``LipidIMEA.lipids.Lipid`` or subclass
        instance of Lipid (or subclass), or ``None`` if unable to parse
    """
    mat = re.search(_LIPID_NAME_REGEX, name)
    if mat is None:
        # name does not match the pattern
        return None
    # get a dict with all of the matched info
    parsed = mat.groupdict()
    # pull the info out
    lipid_class_abbrev = parsed['lcl']
    fa_mod = parsed['fam'] if parsed['fam'] is not None else ''
    if parsed['sn'] is None:
        # only one oxy suffix could have been provided, that would be in oxsf_1
        oxy_suffix = parsed['oxsf_1'] if parsed['oxsf_1'] is not None else ''
        # only one composition element was provided, could by monoacyl species or sum composition
        fa_carbon = int(parsed['fac_1']) 
        fa_unsat = int(parsed['fau_1'])
        # NOTE (Dylan Ross): This is a bad heuristic to use because a valid annotation like LPC 24:0 
        #                    will cause an error due to the long chain length making the n_acyl chain
        #                    guess 2 chains which does not make sense for LPC. Likewise for something
        #                    like PC 24:0 if the chain guess threshold is reduced then this gets guessed 
        #                    as 1 chain which again is not correct for PC. In any case this static
        #                    logic for guessing number of chains is not suited to the task. It is better
        #                    to map lipid class abbreviations to n_chains instead
        # determine the most likely number of chains just based on FA carbon number
        # 1-23 = 1, 24-47 = 2, 48-71 = 3, 72+ = 4
        # which is just c // 24 + 1
        #n_chains_guess = (fa_carbon) // 24 + 1
        # this can be None, in which case this should return None
        if (lmid_prefix := _get_lmid_prefix(lipid_class_abbrev, fa_mod, fa_unsat, oxy_suffix)) is not None:
            if (lpd := _try_lipid((lmid_prefix, fa_carbon, fa_unsat),
                                  {},
                                  False)) is not None:
                # check for monoacyl lipids which can be upgraded to LipidWithChains
                if lpd is not None and lpd.n_chains == 1:
                    # add 0s to fill FA carbon/unsat chains
                    zero_pad = [0 for _ in range(lpd.n_chains_full - 1)]
                    return _try_lipid((lmid_prefix, [fa_carbon,] + zero_pad, [fa_unsat,] + zero_pad), 
                                    {},
                                    True)
                else:
                    # FA1 is the sum composition, stay with Lipid
                    return lpd
            else:
                # could not initialize a Lipid
                return None
        else:
            # could not find a corresponding LMID prefix
            return None
    else:
        # individual FA chains were specified, use LipidWithChains
        sn_is_known = parsed['sn'] == '/'
        fa_carbon_chains = [int(_) for _ in [parsed.get("fac_{}".format(i + 1)) for i in range(4)] if _ is not None]
        fa_unsat_chains = [int(_) for _ in [parsed.get("fau_{}".format(i + 1)) for i in range(4)] if _ is not None]
        pos_and_stereo = []
        pos_specified = False
        # each chain could have its own oxy suffix
        oxy_suffix_chains = []
        for i in range(len(fa_carbon_chains)):
            fadb = parsed['fadb_{}'.format(i + 1)]
            if fadb is not None:
                pos_and_stereo.append(fadb)
                pos_specified = True
            else:
                pos_and_stereo.append('')
            # add each suffix if exists
            oxy_suffix_chains.append(parsed['oxsf_{}'.format(i + 1)])
        # convert Nones into empty strings in oxy_suffix_chains
        oxy_suffix_chains = [_ if _ is not None else "" for _ in oxy_suffix_chains]
        if not pos_specified:
            n_chains = len([_ for _ in fa_carbon_chains if _ > 0])
            comb_oxy_suff = _combined_oxy_suffix_from_oxy_suffix_chains(oxy_suffix_chains)
            if comb_oxy_suff is not None:
                if (lmid_prefix := _get_lmid_prefix(lipid_class_abbrev, 
                                                    fa_mod, 
                                                    sum(fa_unsat_chains), 
                                                    comb_oxy_suff)) is not None:
                    # no positions or sterochem specified
                    return _try_lipid((lmid_prefix, fa_carbon_chains, fa_unsat_chains),
                                      {"sn_pos_is_known": sn_is_known, "oxy_suffix_chains": oxy_suffix_chains},
                                      True)
                else:
                    return None
        # better to not raise an error here, return None to signal failure to parse
        return None
        stereo_specified = False
        fa_unsat_pos, fa_unsat_stereo = [], []
        for ps in pos_and_stereo:
            if ps == '':
                fa_unsat_pos.append([])
                fa_unsat_stereo.append([])
            else:
                unpacked = ps.strip('()').split(',')
                if unpacked and len(unpacked[0]) == 1:
                    fa_unsat_pos.append([int(_) for _ in unpacked])
                elif unpacked and len(unpacked[0]) > 1:
                    stereo_specified = True
                    p, s = [], []
                    for db in unpacked:
                        p.append(int(db[:-1]))
                        s.append(db[-1])
                    fa_unsat_pos.append(p)
                    fa_unsat_stereo.append(s)
        if not stereo_specified:
            fa_unsat_stereo = None
        return LipidWithChains(lipid_class_abbrev, fa_carbon_chains, fa_unsat_chains, 
                               fa_unsat_pos=fa_unsat_pos, fa_unsat_stereo=fa_unsat_stereo, 
                               fa_mod=fa_mod, sn_pos_is_known=sn_is_known)

