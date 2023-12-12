"""
lipidimea/lipids/parser.py

Dylan Ross (dylan.ross@pnnl.gov)

    module for parsing lipids
"""


import re


from lipidimea.lipids import LMAPS, Lipid, LipidWithChains


# regex for parsing lipid information from a lipid name in standard abbreviated format
_LIPID_NAME_REGEX = """
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
"""


def _get_lmid_prefix(lipid_class_abbrev, fa_mod, n_chains, oxy_suffix):
    """
    fetch specific lipid class info (using LMAPS ID prefix) based on
    lipid class abbreviation, fatty acid modifier, and number of chains
    """
    for lmid_prefix, data in LMAPS.items():
        lipid_class_abbrev_ = data['class_abbrev']
        fa_mod_ = data.get('fa_mod', '')
        n_chains_ = data['n_chains']
        oxy_suffix_ = data.get('oxy_suffix', '')
        # TODO (Dylan Ross): Now what happens when we need to negotiate between the more general description of 
        #                    oxidation that happens at the class level (like "Oxidized PEs") vs. the more specific
        #                    structural level in a certain lipid species (like "PE 18:0_16:1;O2"). In other words,
        #                    when it comes to this step of trying to figure out the appropriate LMAPS prefix given
        #                    all of the info you know for a certain lipid which includes the specific oxidation,
        #                    how should this be compared against the info that is contained in the class definitions
        #                    from lmaps.yaml (and how should these modifications be reflected in there?)
        if lipid_class_abbrev == lipid_class_abbrev_ and fa_mod == fa_mod_ and n_chains == n_chains_ and oxy_suffix == oxy_suffix_:
            return lmid_prefix
    msg = '_get_lmid_prefix: cannot find lmid prefix for lipid class abbrev: {}, fa_mod: {}, n_chains: {}, oxy_suffix: {}'
    raise ValueError(msg.format(lipid_class_abbrev, fa_mod, n_chains, oxy_suffix))


def _oxy_suffix_from_oxy_suffix_chains(oxy_suffix_chains):
    """
    come up with a single oxy suffix value from possibly multiple values from different chains
    so that the LMAPS ID prefix can be looked up. 

    TODO (Dylan Ross): For now I am just taking any individual suffixes that are not '' and treating whichever
                       is longest as the one to look up LMAPS ID prefix, probably a bad idea? I think I really
                       should actually parse them and come up with whatever appropriate sematics for combining 
                       them. For instance ['O', 'O', ''] should resolve to 'O2', but what should happen with 
                       something like ['O', 'Ep', 'OOH']? No clue. 
    """
    if len(''.join(oxy_suffix_chains)) == 0:
        return ''
    else:
        raise RuntimeError('not sure how to combine multiple oxy suffixes into single one yet')


def parse_lipid_name(name):
    """
    Parses a lipid name in standard format and returns a corresponding instance of a ``Lipid`` object (or subclass). 
    If the name is not able to be parsed, returns ``None``

    Parameters
    ----------
    name : ``str``
        lipid name in standard format

    Returns
    -------
    lipid : ``lipidimea.lipids.Lipid`` or subclass
        instance of Lipid (or subclass), or ``None`` if unable to parse
    """
    # strip out the whitespace from the lipid name regex but put the space back in in the one
    # spot where it needs to be
    mat = re.search(re.sub(r'\s+', '', _LIPID_NAME_REGEX).replace('[SPACE]', '[ ]'), name)
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
        # determine the most likely number of chains just based on FA carbon number
        # 1-24 = 1, 25-48 = 2, 49-72 = 3, 73+ = 4
        # which is just (c - 1) // 24 + 1
        n_chains_guess = (fa_carbon - 1) // 24 + 1
        lmid_prefix = _get_lmid_prefix(lipid_class_abbrev, fa_mod, n_chains_guess, oxy_suffix)
        lpd = Lipid(lmid_prefix, fa_carbon, fa_unsat)
        # check for monoacyl lipids which can be upgraded to LipidWithChains
        if lpd.n_chains == 1 and lpd.n_chains_full == 1:
            # check for db positions/stereo
            return LipidWithChains(lmid_prefix, (fa_carbon,), (fa_unsat,))
        else:
            # FA1 is the sum composition, use Lipid
            return lpd
    else:
        # individual FA chains were specified, use LipidWithChains
        sn_is_known = parsed['sn'] == '/'
        fa_carbon_chains = [int(parsed['fac_{}'.format(i)]) for i in [1, 2, 3, 4] if parsed['fac_{}'.format(i)] is not None]
        fa_unsat_chains = [int(parsed['fau_{}'.format(i)]) for i in [1, 2, 3, 4] if parsed['fau_{}'.format(i)] is not None]
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
        oxy_suffix_chains = [_ if _ is not None else '' for _ in oxy_suffix_chains]
        if not pos_specified:
            n_chains = len([_ for _ in fa_carbon_chains if _ > 0])
            lmid_prefix = _get_lmid_prefix(lipid_class_abbrev, fa_mod, n_chains, _oxy_suffix_from_oxy_suffix_chains(oxy_suffix_chains))
            # no positions or sterochem specified
            return LipidWithChains(lmid_prefix, fa_carbon_chains, fa_unsat_chains, sn_pos_is_known=sn_is_known, oxy_suffix_chains=oxy_suffix_chains)
        raise RuntimeError('not ready to handle double bond positions or stereochem yet')
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

