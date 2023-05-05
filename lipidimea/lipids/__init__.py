"""
pyliquid/lipids/__init__.py

Dylan Ross (dylan.ross@pnnl.gov)

    sub-module for handling lipid identifications
"""


import re

from mzapy.isotopes import monoiso_mass

from pyliquid.lipids._util import _LIPID_NAME_REGEX, _AcylChain
from pyliquid.lipids._lmaps_classification import _iterate_all_lipid_classifications


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
    lipid : ``pyliquid.lipids.Lipid`` or subclass
        instance of Lipid (or subclass), or ``None`` if unable to parse
    """
    # strip out the whitespace from the lipid name regex
    mat = re.search(re.sub(r'\s+', '', _LIPID_NAME_REGEX), name)
    if mat is None:
        # name does not match the pattern
        return None
    # get a dict with all of the matched info
    parsed = mat.groupdict()
    # pull the info out
    lipid_class_abbrev = parsed['lcl']
    fa_mod = parsed['fam'] if parsed['fam'] is not None else ''
    if parsed['sn'] is None:
        # only one composition element was provided, could by monoacyl species or sum composition
        fa_carbon = int(parsed['fac_1']) 
        fa_unsat = int(parsed['fau_1'])
        # check for LPC, LPE... change to PC, PE, ... with 0:0 chain
        if lipid_class_abbrev in ['LPC', 'LPE', 'LPS', 'LPG', 'LPI', 'LPIP', 'LPA']:
            lipid_class_abbrev = lipid_class_abbrev[1:]
            return LipidWithChains(lipid_class_abbrev, (fa_carbon, 0), (fa_unsat, 0), fa_mod=fa_mod)
        # check for monoacyl lipids (not lyso- lipids) which can be upgraded to LipidWithChains
        lpd = Lipid(lipid_class_abbrev, fa_carbon, fa_unsat, fa_mod=fa_mod)
        if lpd.n_chains == 1:
            # check for db positions/stereo
            return LipidWithChains(lipid_class_abbrev, (fa_carbon,), (fa_unsat,), fa_mod=fa_mod)
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
        for i in range(len(fa_carbon_chains)):
            fadb = parsed['fadb_{}'.format(i + 1)]
            if fadb is not None:
                pos_and_stereo.append(fadb)
                pos_specified = True
            else:
                pos_and_stereo.append('')
        if not pos_specified:
            # no positions or sterochem specified
            return LipidWithChains(lipid_class_abbrev, fa_carbon_chains, fa_unsat_chains, 
                                   fa_mod=fa_mod, sn_pos_is_known=sn_is_known)
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
        fatty acid modifier, if any (indicates things like ether/plasmenyl lipids: O-, P-, d), '' otherwise
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
    ionization : ``str``
        ionization mode(s) this lipid would be expected to be detected in ('pos', 'neg', or 'both')
    contains_ether : ``bool``
        lipid contains ether
    contains_diether : ``bool``
        lipid contains diether
    contains_plasmalogen : ``bool``
        lipid is a plasmalogen (1Z-alkenyl)
    contains_lcb : ``bool``
        contains LCB
    contains_lcbpoh : ``bool``
        contains LCB + OH
    contains_lcbmoh : ``bool``
        contains LCB - OH
    is_oxo_cho : ``bool``
        is Oxo CHO
    is_oxo_cooh : ``bool``
        is Oxo COOH
    num_oh : ``int``
        number of OH groups
    contains_ooh : ``bool``
        contains OOH (hydroperoxyl)
    contains_f2isop : ``bool``
        contains F2IsoP
    """

    def __init__(self, lipid_class_abbrev, fa_carbon, fa_unsat, fa_mod='', n_chains=None):
        """
        inits a new instance of a Lipid object using lipid class, sum composition, and fatty acid modifier (if any)

        Parameters
        ----------
        lipid_class_abbrev : ``str``
            lipid class standard abbreviation from Lipid MAPS (e.g., PC, TG, ...)
        fa_carbon : ``int``
            fatty acid carbon count (all acyl chains)
        fa_unsat : ``int``
            fatty acid unsaturation count (all acyl chains)
        fa_mod : ``str``, default=''
            fatty acid modifier, if any (indicates things like ether/plasmenyl lipids: O-, P-, d), '' otherwise
        n_chains : ``int``, optional
            if provided, specifies the number of acyl chains, used to identify lyso- lipids

        """
        self.lipid_class_abbrev = lipid_class_abbrev
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
        self.fa_mod = fa_mod
        # fetch classification information using lipid class abbrev and fa modifier
        class_info, lipid_info = self._fetch_classification_info(n_chains)
        self.lmaps_category, self.lmaps_class, self.lmaps_subclass = class_info
        self.lmaps_id_prefix = lipid_info['lm_id_prefix']
        # construct the molecular formula using FA composition and rules lipid_info
        self.formula = self._construct_formula_from_rules(lipid_info)
        # get number of acyl chains and ionization
        self.n_chains, self.ionization = lipid_info['n_chains'], lipid_info['ionization']
        # get "other_props"
        self._unpack_other_props(lipid_info['other_props'])

    def _fetch_classification_info(self, n_chains):
        """
        fetches LMAPS classification info corresponding to lipid class abbreviation and FA modifier

        Parameters
        ----------
        n_chains : ``int``, optional
            if provided, specifies the number of acyl chains, used to identify lyso- lipids

        Returns
        -------
        class_info : ``tuple(str)``
            LMAPS lipid classification info (category, class, subclass)
        lipid_info : ``dict(...)``
            lipid information (formula, ionization, acyl chain count)
        """
        # iterate through all of the classifications defined in pyliquid/_lmaps_classification.py
        for class_info, lipid_info in _iterate_all_lipid_classifications():
            if self.lipid_class_abbrev == lipid_info['class_abbrev']:
                if self.fa_mod == lipid_info['fa_mod']:
                    if n_chains is None:
                        return class_info, lipid_info
                    elif n_chains == lipid_info['n_chains']:
                        # account for difference between sat/unsat FAs
                        return class_info, lipid_info
        # if we reach this point no classification was found
        msg = 'Lipid: _fetch_classification_info: LMAPS classification for lipid class "{}" with FA modifier "{}" not found'
        raise ValueError(msg.format(self.lipid_class_abbrev, self.fa_mod))

    def _construct_formula_from_rules(self, lipid_info):
        """
        uses the rules from lipid_info to construct a molecular formula using the FA composition

        Parameters
        ----------
        lipid_info : ``dict(...)``
            lipid information (formula, ionization, acyl chain count)

        Returns
        -------
        formula : ``dict(str:int)``
            molecular formula as a dictionary mapping elements (str) to their counts (int)
        """
        formula = {}
        formula['C'] = int(lipid_info['formula']['C'](self.fa_carbon))
        formula['H'] = int(lipid_info['formula']['H'](self.fa_carbon, self.fa_unsat))
        formula['N'] = int(lipid_info['formula']['N'])
        formula['O'] = int(lipid_info['formula']['O'])
        formula['S'] = int(lipid_info['formula']['S'])
        formula['P'] = int(lipid_info['formula']['P'])
        return formula

    def _unpack_other_props(self, other_props):
        """
        unpacks the "other_props" attribute of lipid_info into individual structural descriptors:
            ContainsEther, ContainsDiether, ContainsPlasmalogen, ContainsLCB, ContainsLCB+OH, ContainsLCB-OH, IsOxoCHO, 
            IsOxoCOOH, NumOH, ContainsOOH, ContainsF2IsoP
        
        Parameters
        ----------
        other_props : ``list(int)``
            array of properties describing structural features
        """
        self.contains_ether = bool(other_props[0])
        self.contains_diether = bool(other_props[1])
        self.contains_plasmalogen = bool(other_props[2])
        self.contains_lcb = bool(other_props[3])
        self.contains_lcbpoh = bool(other_props[4])
        self.contains_lcbmoh = bool(other_props[5])
        self.is_oxo_cho = bool(other_props[6])
        self.is_oxo_cooh = bool(other_props[7])
        self.num_oh = other_props[8]
        self.contains_ooh = bool(other_props[9])
        self.contains_f2isop = bool(other_props[10])

    def __repr__(self):
        s = '{}(lipid_class_abbrev="{}", fa_carbon={}, fa_unsat={}, fa_mod="{}")'
        return s.format(self.__class__.__name__, self.lipid_class_abbrev, self.fa_carbon, self.fa_unsat, self.fa_mod)

    def __str__(self):
        s = '{}({}{}:{})'
        return s.format(self.lipid_class_abbrev, self.fa_mod, self.fa_carbon, self.fa_unsat)


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
    sn_pos_is_known : ``bool``
        indicates whether the sn position of the chains is known or ambiguous
    """

    def __init__(self, lipid_class_abbrev, fa_carbon_chains, fa_unsat_chains, 
                 fa_mod='', fa_unsat_pos=None, fa_unsat_stereo=None, sn_pos_is_known=False):
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
        """
        # init superclass using sum FA composion
        super().__init__(lipid_class_abbrev, sum(fa_carbon_chains), sum(fa_unsat_chains), 
                         fa_mod=fa_mod, n_chains=len([_ for _ in fa_carbon_chains if _ > 0]))
        # validate the fatty acid composition
        self._validate_composition(fa_carbon_chains, fa_unsat_chains, fa_unsat_pos, fa_unsat_stereo)
        # store the chain-specific fatty acid compositions
        self.fa_carbon_chains = fa_carbon_chains
        self.fa_unsat_chains = fa_unsat_chains
        self.fa_unsat_pos = fa_unsat_pos
        self.fa_unsat_stereo = fa_unsat_stereo
        self.sn_pos_is_known = sn_pos_is_known
        # init _AcylChain instances for each fa
        self._init_acyl_chains()
        

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

    def _init_acyl_chains(self):
        """
        initialize instances of _AcylChain for each acyl chain in this lipid, stored in the instance variable 
        self._acyl_chains which is a list of _AcylChain instances, in order of sn- position. These are used for MS/MS
        calculations

        TODO (Dylan Ross): account for acyl chain types other than 'Standard', 'Ether', and 'Plasmalogen'
        """
        self._acyl_chains = []
        for i, (fac, fau) in enumerate(zip(self.fa_carbon_chains, self.fa_unsat_chains)):
            if fac > 0:
                # skip 0 carbon acyl chains in the case of the lyso lipids
                if self.fa_mod in ['O-', 'P-']:
                    # if sn- position is known only the first acyl chain is ether/plasmalogen and other is standard
                    # if sn- position is not known, then just assign both as ether/plasmalogen
                    acyl_type = 'Ether' if self.fa_mod == 'O-' else 'Plasmalogen' 
                    if self.sn_pos_is_known:
                        if i == 0:
                            self._acyl_chains.append(_AcylChain(fac, fau, acyl_type))
                        else:
                            self._acyl_chains.append(_AcylChain(fac, fau, 'Standard'))
                    else:
                        self._acyl_chains.append(_AcylChain(fac, fau, acyl_type))

                else:
                    # in all other cases, treat the acyl chain type as 'Standard'
                    self._acyl_chains.append(_AcylChain(fac, fau, 'Standard'))

    def __str__(self):
        s = '{}({}'.format(self.lipid_class_abbrev, self.fa_mod)
        posns = ['' for _ in self.fa_carbon_chains] if self.fa_unsat_pos is None else self.fa_unsat_pos
        stereos = ['' for _ in self.fa_carbon_chains] if self.fa_unsat_stereo is None else self.fa_unsat_stereo
        idata = list(zip(self.fa_carbon_chains, self.fa_unsat_chains, posns, stereos))
        if self.sn_pos_is_known:
            # iterate through the chains in provided order and use / separator
            sep = '/'
        else:
            # iterate through chains in order of descending carbon count, unsaturation level and use _ separator
            idata.sort(key=lambda p: (-p[0], -p[1]))
            sep = '_'
        # add the fatty acid compositions
        for c, u, p, st in idata:
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
            s += sep
        s = s.rstrip(sep)
        s += ')'
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

