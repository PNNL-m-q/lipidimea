"""
lipidimea/lipids/_util.py

Dylan Ross (dylan.ross@pnnl.gov)

    internal module with utilities related to lipid identification
"""


from itertools import product


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

