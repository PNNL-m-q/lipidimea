"""
LipidIMEA/lipids/_util.py

Dylan Ross (dylan.ross@pnnl.gov)

    internal module with utilities related to lipid identification
"""


from itertools import product


# regex for parsing lipid information from a lipid name in standard abbreviated format
LIPID_NAME_REGEX = """
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


def get_c_u_combos(lipid, min_c, max_c, odd_c):
    """
    figure out all possible combinations of FA composition that can produce 
    a lipid's sum composition

    Parameters
    ----------
    lipid : ````
        input lipid
    min_c : ``int``
        minimum FA carbons
    max_c : ``int``
        maximum FA carbons
    odd_c : ``bool``
        include FAs with odd number of carbons
    """
    # lipid.fa_carbon - total carbons
    # lipid.fa_unsat - total unsaturations
    # lipid.n_chains - number of acyl chains
    c_int = 1 if odd_c else 2
    n_chains = lipid.n_chains
    sum_c = lipid.fa_carbon
    sum_u = lipid.fa_unsat
    fas = set()
    for c_perm in set([tuple(sorted(_)) for _ in product(range(min_c, max_c + 1, c_int), repeat=n_chains) if sum(_) == sum_c]):
        for u_perm in [_ for _ in product(range(0, sum_u + 1), repeat=n_chains) if sum(_) == sum_u]:
            for c, u in zip(c_perm, u_perm):
                fas.add((c, u))
    # TODO (Dylan Ross): this does not need to be two steps... ?
    for c, u in fas:
        yield c, u

