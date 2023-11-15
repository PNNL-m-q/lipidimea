"""
LipidIMEA/lipids/__init__.py

Dylan Ross (dylan.ross@pnnl.gov)

    sub-package for handling lipid annotation
"""


import re
from os import path as op

from mzapy.isotopes import monoiso_mass
import yaml

from LipidIMEA.lipids._util import LIPID_NAME_REGEX


# load the classifications from YAML file
with open(op.join(op.dirname(op.dirname(op.abspath(__file__))), '_include/lmaps.yml'), 'r') as _yf:
    LMAPS = yaml.safe_load(_yf)


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
    lipid : ``LipidIMEA.lipids.Lipid`` or subclass
        instance of Lipid (or subclass), or ``None`` if unable to parse
    """
    # strip out the whitespace from the lipid name regex but put the space back in in the one
    # spot where it needs to be
    mat = re.search(re.sub(r'\s+', '', LIPID_NAME_REGEX).replace('[SPACE]', '[ ]'), name)
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
        s = '{} {}{}:{}{}{}'
        # this extra chains thing helps to identify lyso- lipids, only works if there is one chain though
        # otherwise it introduces ambiguity
        extra_chains = '_0:0' * (self.n_chains_full - self.n_chains) if self.n_chains == 1 else ''
        oxy_suffix = ';' + self.oxy_suffix if self.oxy_suffix != '' else ''
        return s.format(self.lipid_class_abbrev, self.fa_mod, self.fa_carbon, self.fa_unsat, extra_chains, oxy_suffix)


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

