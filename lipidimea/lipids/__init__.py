"""
LipidIMEA/lipids/__init__.py

Dylan Ross (dylan.ross@pnnl.gov)

    sub-package for handling lipid annotation
"""


from os import path as op

import yaml

from mzapy.isotopes import monoiso_mass


# load the classifications from YAML file
with open(op.join(op.dirname(op.dirname(op.abspath(__file__))), '_include/lmaps.yml'), 'r') as _yf:
    LMAPS = yaml.safe_load(_yf)


class Lipid():
    """
    class used for representing an individual lipid species. 
    stores classification information (using Lipid MAPS classification system)

    Attributes
    ----------
    lipid_class_abbrev : ``str``
        lipid class standard abbreviation from Lipid MAPS (e.g., PC, TG, ...)
    fa_carbon : ``int``
        fatty acid carbon count (all acyl chains)
    fa_unsat : ``int``
        fatty acid unsaturation count (all acyl chains)
    fa_mod : ``str``
        fatty acid modifier, if any (indicates things like ether/plasmenyl lipids: 'O-', 'P-'), '' otherwise
    oxy_suffix : ``str``
        useful for sphingolipids to indicate the type of backbone (should mostly be 'O2' for mammalian
        sphingolipids based on sphingosine), but also applies to oxidized phospholipids (hydroxy, epoxide,
        hydroperoxy). '' if no such oxy suffix is needed
    lmaps_category : ``str``
        Lipid MAPS classification, category
    lmaps_class : ``str``
        Lipid MAPS classification, class
    lmaps_subclass : ``str``
        Lipid MAPS classification, subclass
    lmaps_id_prefix : ``str``
        Lipid MAPS classification, LMID prefix
    formula : ``dict(int:str)``
        molecular formula as a dictionary mapping elements (str) to their counts (int)
    n_chains : ``int``
        acyl/alkyl chain count
    n_chains_full : ``int``
        count of total available acyl/alkyl chain positions available, useful to discern lyso- lipids
    """

    def __init__(self, lmid_prefix, fa_carbon, fa_unsat):
        """
        inits a new instance of a Lipid object using LipidMAPS prefix (to specify lipid class)
        and sum composition

        Parameters
        ----------
        lmid_prefix : ``str``
            Lipid MAPS ID prefix denoting lipid classification
        fa_carbon : ``int``
            fatty acid carbon count (all acyl chains)
        fa_unsat : ``int``
            fatty acid unsaturation count (all acyl chains)
        """
        lipid_info = LMAPS[lmid_prefix]
        self.lipid_class_abbrev = lipid_info['class_abbrev']
        # carbon count must be > 0 
        if fa_carbon <= 0 :
            msg = 'Lipid: __init__: fa_carbon must be > 0 (was: {})'
            raise ValueError(msg.format(fa_carbon))
        # unsaturation count must be between 0 and (fa_carbon // 2 + fa_carbon % 2 - 1)
        max_unsat = fa_carbon // 2 + fa_carbon % 2 - 1
        if fa_unsat < 0 or fa_unsat > max_unsat: 
            msg = 'Lipid: __init__: fa_unsat must be between 0 and fa_carbon // 2 + fa_carbon % 2 - 1 = {} (was: {})'
            raise ValueError(msg.format(max_unsat, fa_unsat))
        self.fa_carbon = fa_carbon
        self.fa_unsat = fa_unsat
        self.fa_mod = lipid_info.get('fa_mod', '')
        self.oxy_suffix = lipid_info.get('oxy_suffix', '')
        # fetch classification information using lipid class abbrev and fa modifier
        self.lmaps_category, self.lmaps_class, self.lmaps_subclass = lipid_info['classification']
        self.lmaps_id_prefix = lmid_prefix
        # construct the molecular formula using FA composition and rules lipid_info
        self.formula = {}
        for element, count in lipid_info['formula'].items():
            if type(count) is int:
                self.formula[element] = count
            elif type(count) is str:
                self.formula[element] = eval('lambda c, u: ' + count)(self.fa_carbon, self.fa_unsat)
        # get number of acyl chains and ionization
        self.n_chains = lipid_info['n_chains']
        # n_chains_full is present in some lipid classes to indicate lyso- species
        self.n_chains_full = lipid_info.get('n_chains_full', self.n_chains)

    def __repr__(self):
        s = '{}(lipid_class_abbrev="{}", fa_carbon={}, fa_unsat={}, fa_mod="{}", lmid_prefix="{}")'
        return s.format(self.__class__.__name__, self.lipid_class_abbrev, self.fa_carbon, self.fa_unsat, self.fa_mod, self.lmaps_id_prefix)

    def __str__(self):
        s = '{} {}{}:{}{}'
        oxy_suffix = ';' + self.oxy_suffix if self.oxy_suffix != '' else ''
        return s.format(self.lipid_class_abbrev, self.fa_mod, self.fa_carbon, self.fa_unsat, oxy_suffix)


class LipidWithChains(Lipid):
    """
    Subclass of ``Lipid`` that contains additional information regarding the composition of individual FA chains

    Attributes
    ----------
    fa_carbon_chains : ``list(int)``
        fatty acid carbon count for individual chains
    fa_unsat_chains : ``list(int)``
        fatty acid unsaturation count for individual chains
    fa_unsat_pos : ``list(list(int))``
        lists of double bond positions for each fatty acid
    fa_unsat_stereo : ``list(list(str))``
        lists of double bond stereochemistry for each fatty acid
    sn_pos_is_known : ``bool``, default=False
        indicates whether the sn position of the chains is known or ambiguous
    oxy_suffix_chains : ``list(str)``
        oxidation suffix (str, '' if no modification) for individual chains
    """

    def __init__(self, lmid_prefix, fa_carbon_chains, fa_unsat_chains, 
                 fa_unsat_pos=None, fa_unsat_stereo=None, sn_pos_is_known=False, oxy_suffix_chains=None):
        """
        inits a new instance of a LipidWithChains object using lipid class, fatty acid composition (split by FA chain), 
        fatty acid modifier (if any), and double bond positions/stereochemistry (if known)

        Parameters
        ----------
        lipid_class_abbrev : ``str``
            lipid class standard abbreviation from Lipid MAPS (e.g., PC, TG, ...)
        fa_carbon_chains : list(``int``)
            fatty acid carbon count (all acyl chains, in order of sn- position)
        fa_unsat_chains : list(``int``)
            fatty acid unsaturation count (all acyl chains, in order of sn- position)
        fa_mod : ``str``, default=''
            fatty acid modifier, if any (indicates things like ether/plasmenyl lipids: O-, P-, d), '' otherwise
        fa_unsat_pos : ``list(list(int))``, optional
            lists of double bond positions for each fatty acid, in order of sn- position, if known
        fa_unsat_stereo : ``list(list(str))``, optional
            lists of double bond stereochemistry for each fatty acid, in order of sn- position, if known. 
            requires fa_unsat_pos to be set
        sn_pos_is_known : ``bool``, default=False
            indicates whether the sn position of the chains is known or ambiguous
        oxy_suffix_chains : ``list(str)``, optional
            oxidation suffix (str, '' if no modification) for individual chains. Defaults to empty strings if
            not provided
        """
        # init superclass using sum FA composion
        super().__init__(lmid_prefix, sum(fa_carbon_chains), sum(fa_unsat_chains))
        # validate the fatty acid composition
        self._validate_composition(fa_carbon_chains, fa_unsat_chains, fa_unsat_pos, fa_unsat_stereo)
        # store the chain-specific fatty acid compositions
        self.fa_carbon_chains = fa_carbon_chains
        self.fa_unsat_chains = fa_unsat_chains
        self.oxy_suffix_chains = oxy_suffix_chains if oxy_suffix_chains is not None else ['' for _ in range(self.n_chains)]
        self.fa_unsat_pos = fa_unsat_pos
        self.fa_unsat_stereo = fa_unsat_stereo
        self.sn_pos_is_known = sn_pos_is_known
        

    def _validate_composition(self, fa_carbon_chains, fa_unsat_chains, fa_unsat_pos, fa_unsat_stereo):
        """
        checks the elements of FA composition that have been specified and makes sure they make sense together, raises
        ``ValueError``s if any of the values are improper

        Parameters
        ----------
        fa_carbon_chains : list(``int``)
            fatty acid carbon count (all acyl chains, in order of sn- position)
        fa_unsat_chains : list(``int``)
            fatty acid unsaturation count (all acyl chains, in order of sn- position)
        fa_unsat_pos : ``list(list(int))``
            lists of double bond positions for each fatty acid, in order of sn- position, if known
        fa_unsat_stereo : ``list(list(str))``
            lists of double bond stereochemistry for each fatty acid, in order of sn- position, if known. 
            requires fa_unsat_pos to be set
        """
        # make sure composition elements have the same lengths
        if len(fa_carbon_chains) != len(fa_unsat_chains):
            msg = ('LipidWithChains: _validate_composition: fatty acid carbons specified for {} chains but fatty acid '
                   'unsaturations specified for {} chains')
            raise ValueError(msg.format(len(fa_carbon_chains), len(fa_unsat_chains)))
        # check that the number of chains provided matches what is expected given the lipid class
        fa_chain_count = len([_ for _ in fa_carbon_chains if _ > 0])
        if fa_chain_count != self.n_chains:
            msg = ('LipidWithChains: _validate_composition: lipid class {} expects {} chains, but fatty acid '
                   'composition was specified for {} chains')
            raise ValueError(msg.format(self.lmaps_id_prefix, self.n_chains, fa_chain_count))
        # if double bond positions are provided, validate them
        if fa_unsat_pos is not None:
            # first check that length is same as unsaturations
            if len(fa_unsat_pos) != len(fa_unsat_chains):
                msg = ('LipidWithChains: _validate_composition: {} chains specified but {} sets of double bond '
                       'positions specified')
                raise ValueError(msg.format(len(fa_unsat_chains), len(fa_unsat_pos)))
            # then check that the number of positions in each chain matched the number of unsaturations in each chain
            for unsat, pos in zip(fa_unsat_chains, fa_unsat_pos):
                if len(pos) != unsat:
                    msg = ('LipidWithChains: _validate_composition: specified double bond positions {} '
                           'do no match number of double bonds for this chain: {}')
                    raise ValueError(msg.format(pos, unsat))
        # if double bond stereochem is provided, validate them
        if fa_unsat_stereo is not None:
            # first check that unsaturation positions have been provided
            if fa_unsat_pos is None:
                msg = ('LipidWithChains: _validate_composition: unsaturation stereochemistry was '
                       'provided but no unsaturation positions were specified')
                raise ValueError(msg)
            # then check that length is same as unsaturations
            if len(fa_unsat_stereo) != len(fa_unsat_chains):
                msg = ('LipidWithChains: _validate_composition: {} chains specified but {} '
                       'sets of double bond stereochemistry specified')
                raise ValueError(msg.format(len(fa_unsat_chains), len(fa_unsat_stereo)))
            # then check that the number of stereochem in each chain matched the number of unsaturations in each chain
            for unsat, ster in zip(fa_unsat_chains, fa_unsat_stereo):
                if len(ster) != unsat:
                    msg = ('LipidWithChains: _validate_composition: specified double bond stereochemistry '
                           '{} do no match number of double bonds for this chain: {}')
                    raise ValueError(msg.format(ster, unsat))

    def __str__(self):
        s = '{} {}'.format(self.lipid_class_abbrev, self.fa_mod)
        posns = ['' for _ in self.fa_carbon_chains] if self.fa_unsat_pos is None else self.fa_unsat_pos
        stereos = ['' for _ in self.fa_carbon_chains] if self.fa_unsat_stereo is None else self.fa_unsat_stereo
        idata = list(zip(self.fa_carbon_chains, self.fa_unsat_chains, posns, stereos, self.oxy_suffix_chains))
        if self.sn_pos_is_known:
            # iterate through the chains in provided order and use / separator
            sep = '/'
        else:
            # iterate through chains in order of descending carbon count, unsaturation level and use _ separator
            idata.sort(key=lambda p: (-p[0], -p[1]))
            sep = '_'
        # add the fatty acid compositions
        for c, u, p, st, oxsf in idata:
            s += '{}:{}'.format(c, u)
            if p != '' and p != []:
                s += '('
                if st != '':
                    l = list(zip(p, st))
                    l.sort(key=lambda p: p[0])
                    for a, b in l:
                        s += '{}{},'.format(a, b)
                else:
                    p.sort()
                    for c in p:
                        s += '{},'.format(c)
                s = s.rstrip(',')
                s += ')'
            oxsf = ';' + oxsf if oxsf != '' else ''
            s += oxsf
            s += sep
        s = s.rstrip(sep)
        return s

    def add_db_positions(self, fa_unsat_pos, fa_unsat_stereo=None):
        """
        Add double bond positions (and optionally sterechemistry, if known) to this ``LipidWithChains`` instance,
        double bond positions/stereo must match with the already specified acyl chain composition and be in the same
        order

        Parameters
        ----------
        fa_unsat_pos : ``list(list(int))``
            lists of double bond positions for each fatty acid
        fa_unsat_stereo : ``list(list(str))``, optional
            lists of double bond stereochemistry for each fatty acid, if known
        """
        # re-validate the FA composition with updated double bond positions
        self._validate_composition(self.fa_carbon_chains, self.fa_unsat_chains, fa_unsat_pos, fa_unsat_stereo)
        # if that worked, store the new db positions/stereo
        self.fa_unsat_pos = fa_unsat_pos
        self.fa_unsat_stereo = fa_unsat_stereo

