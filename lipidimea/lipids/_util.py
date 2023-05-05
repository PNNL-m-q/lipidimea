"""
pyliquid/lipids/_util.py

Dylan Ross (dylan.ross@pnnl.gov)

    internal module with utilities related to lipid identification
"""


from itertools import product


# regex for parsing lipid information from a lipid name in standard abbreviated format
_LIPID_NAME_REGEX = """
    ^
    (?P<lcl>
        [A-Za-z123]+
    )
    [(]
    (?P<fam>
        O-|P-|d
    )*
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
        )*
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
            )*
        )
    ){0,1}
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
            )*
        )
    ){0,1}
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
            )*
        )
    ){0,1}
    [)]
    $
"""


# define valid acyl chain types
_ACYL_CHAIN_TYPES = [
    'Standard',
    'Plasmalogen',
    'Ether',
    'OxoCHO',
    'OxoCOOH',
    'Monohydro',
    'Dihydro',
    'Trihydro',
    'Hydroxy',
    'OOH',
    'OOHOH',
    'F2IsoP'
]


class _AcylChain():
    """
    internal class for representing acyl chain information

    Attributes
    ----------
    carbons : ``int``
        carbon count
    unsats : ``int``
        unsaturation count
    oh_pos : ``int``
        hydroxyl position
    oh_cnt : ``int``
        hydroxyl count
    me_pos : ``list(int)``
        methyl positions
    me_cnt : ``int``
        methyl count
    ooh_cnt : ``int``
        hydroperoxyl count
    acyl_chain_type : ``str``
        type of acyl chain
    """

    def __init__(self, carbons, unsats, acyl_chain_type, 
                 oh_pos=None, oh_cnt=None, me_pos=None, me_cnt=None, ooh_cnt=None):
        """
        create a new instance of _AcylChain

        Parameters
        ----------
        carbons : ``int``
            carbon count
        unsats : ``int``
            unsaturation count
        acyl_chain_type : ``str``
            type of acyl chain
        oh_pos : ``int``, optional
            hydroxyl position
        oh_cnt : ``int``, optional
            hydroxyl count
        me_pos : ``list(int)``, optional
            methyl positions
        me_cnt : ``int``, optional
            methyl count
        ooh_cnt : ``int``, optional
            hydroperoxyl count
        """
        # validate and store all of the parameters
        self._validate_composition(carbons, unsats)
        self.carbons = carbons
        self.unsats = unsats
        self._validate_acyl_chain_type(acyl_chain_type)
        self.acyl_chain_type = acyl_chain_type
        # TODO (Dylan Ross): implement validation of these modification values
        #self._validate_modifications(oh_pos, oh_cnt, me_pos, me_cnt, ooh_cnt)
        self.oh_pos = oh_pos if oh_pos is not None else -1
        self.oh_cnt = oh_cnt if oh_cnt is not None else 0
        self.me_pos = me_pos if me_pos is not None else []
        self.me_cnt = me_cnt if me_cnt is not None else 0
        self.ooh_cnt = ooh_cnt if ooh_cnt is not None else 0

    def _validate_composition(self, carbons, unsats):
        """ validate that the composition makes sense """
        # carbon count must be > 0 
        if carbons <= 0 :
            msg = '_AcylChain: _validate_composition: fa_carbon must be > 0 (was: {})'
            raise ValueError(msg.format(carbons))
        # unsaturation count must be between 0 and (fa_carbon // 2 + fa_carbon % 2 - 1)
        max_unsat = carbons // 2 + carbons % 2 - 1
        if unsats < 0 or unsats > max_unsat: 
            msg = '_AcylChain: _validate_composition: unsats must be between 0 and carbons // 2 + carbons % 2 - 1 = {} (was: {})'
            raise ValueError(msg.format(max_unsat, unsats))

    def _validate_acyl_chain_type(self, acyl_chain_type):
        """ raises a ValueError if acyl_chain_type is not defined in _ACYL_CHAIN_TYPES """
        if acyl_chain_type not in _ACYL_CHAIN_TYPES:
            msg = '_AcylChain: _validate_acyl_chain_type: invalid acyl chain type ({})'
            raise ValueError(msg.format(acyl_chain_type))

    def __repr__(self):
        s = '_AcylChain(acyl_chain_type="{}", carbons={}, unsats={})'
        return s.format(self.acyl_chain_type, self.carbons, self.unsats)


def _get_c_u_combos(lipid, min_c, max_c, odd_c):
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


def _create_sum_comp_db(file, iteration_params):
    """
    Creates a SQLite database with lipid ids at the level of sum composition
    uses enumeration over lipid class, FA composition, and MS adduct to produce database
    
    Parameters
    ----------
    file : ``str``
        filename to save the database under
    iteration_params : ``dict(...)``
        parameters for iterating over lipid classes, map lipid class name to list of adducts and FA compositions
    """

