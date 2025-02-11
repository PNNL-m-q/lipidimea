"""
lipidimea/_lipidlib/_fragmentation_rules.py
Dylan Ross (dylan.ross@pnnl.gov)

    Rules defining fragments formed for different lipid classes
"""


from os import path as op
from glob import glob
from re import compile
from typing import Any, Optional, Union, Dict, List, Tuple

import yaml
from mzapy.isotopes import monoiso_mass, valid_element


class _FragRule():
    """ 
    base class for fragmentation rules defining shared behavior between _FragRuleStatic
    and _FragRuleDynamic subclasses. Not really meant to be used directly.

    Attributes
    ----------
    static : ``bool``
        this fragmentation rule is static (i.e., the molecular formula is not dependent upon
        FA composition)
    label : ``str``
        fragmentation rule label
    rule : ``dict(str:(int or str))``
            fragmentation rule definition (a molecular formula as a dict mapping elements to counts, 
            counts are ints if the rule is static or str containing an expression for computing the 
            count from FA carbon/unsaturation counts if the rule is dynamic)
    diagnostic : ``bool``
        this fragmentation rule is diagnostic for a particular lipid class
    neutral_loss : ``bool``
        this fragmentation rule corresponds to a neutral loss
    n_chains : ``int or None``
        number of FA chains associated with this fragmentation rule, None if not applicable
    """

    def __init__(self, 
                 static: bool, label: str, rule: Dict[str, Union[int, str]], diagnostic: bool, 
                 neutral_loss: bool, n_chains: Optional[int]) -> None:
        """
        init a new _FragRule, simply store all of the fields

        Parameters
        ----------
        static : ``bool``
            this fragmentation rule is static (i.e., the molecular formula is not dependent upon
            FA composition)
        label : ``str``
            fragmentation rule label
        rule : ``dict(str:(int or str))``
            fragmentation rule definition (a molecular formula as a dict mapping elements to counts, 
            counts are ints if the rule is static or str containing an expression for computing the 
            count from FA carbon/unsaturation counts if the rule is dynamic)
        diagnostic : ``bool``
            this fragmentation rule is diagnostic for a particular lipid class
        neutral_loss : ``bool``
            this fragmentation rule corresponds to a neutral loss
        n_chains : ``int or None``
            number of FA chains associated with this fragmentation rule, None if not applicable
        """
        self.static = static
        self.lbl = label
        self.diagnostic = diagnostic
        self.neutral_loss = neutral_loss
        # make sure n_chains is not None if static is False
        if not self.static and n_chains is None:
            msg = "_FragRule: __init__: n_chains should not be None if the rule is dynamic"
            raise ValueError(msg)
        self.n_chains = n_chains
        # validate the rule
        self._validate_rule(rule)
        self.rule = rule
    
    def _validate_rule(self, rule: Dict[str, Union[int, str]]) -> None:
        """
        make sure the rule definition makes sense, it must be a dictionary consisting of valid 
        elements mapped to either integers or strings containing evaluatable expressions with c
        and/or u as variables. Raises a ValueError if the format is incorrect.

        Parameters
        ----------
        rule : ``dict(str:(int or str))``
            fragmentation rule definition (a molecular formula as a dict mapping elements to counts, 
            counts are ints if the rule is static or str containing an expression for computing the 
            count from FA carbon/unsaturation counts if the rule is dynamic)
        """
        # simple pattern for expressions
        pat = compile(r'^[ cu0-9\+\*\-\(\)]+$')
        for element, count in rule.items():
            if not valid_element(element):
                msg = "_FragRule: _validate_rule: invalid element ('{}') in fragmentation rule definition"
                raise ValueError(msg.format(element))
            if type(count) is int:
                # fragmentation rules should not have negative element counts
                if count < 0:
                    msg = "_FragRule: _validate_rule: explicit element counts must be >= 0"
                    raise ValueError(msg)
            else:
                # count must be a string
                # make sure this is not a static fragmentation rule
                if self.static:
                    msg = "_FragRule: _validate_rule: rule definition is dynamic but self.static is True"
                    raise ValueError(msg)
                # make sure it fits the expected pattern
                if not pat.match(count):
                    msg = "_FragRule: _validate_rule: count expression ('{}') does not match pattern"
                    raise ValueError(msg.format(count))

    def _mz(self, 
            frag_mz: float, pre_mz: float, d_label: Optional[int]) -> float:
        """ 
        compute m/z for the fragment rule, dealing with neutral loss and/or deuterium 
        labels if needed, subclasses should implement self.mz(...) method that acutually
        computes the m/z (with different call signatures according the whether the rule
        is static/dynamic) then uses this method to make final adjustments before 
        returning the computed m/z

        Parameters
        ----------
        rule_mz : ``float``
            m/z computed from the formula of the fragmentation rule, may need to be 
            modified to account for the rule being a neutral loss and/or having a 
            deuterium label
        pre_mz : ``float``
            a precursor m/z for neutral loss fragmentation rules, always required
        d_label : ``int``
            optional deuterium label for computing fragments for labeled lipids, if
            None then do not make any adjustments
        
        Returns
        -------
        rule_mz : ``float``
            fragmentation rule m/z 
        """
        # self.mz() defined by subclass, computes the m/z 
        d = monoiso_mass({'H': -d_label, 'D': d_label}) if d_label is not None else 0.
        if self.neutral_loss:
            return pre_mz - frag_mz - d
        else:
            return frag_mz + d
    
    def _label(self) -> str:
        """ add a '*' to diagnostic fragment labels or just return ``self.lbl`` """
        return '*' + self.lbl if self.diagnostic else self.lbl
        
    def __str__(self) -> str:
        return self._label()
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._label()})"
    

class _FragRuleStatic(_FragRule):
    """ Static fragmentation rule (molecular formula does not depend on FA composition) """
    
    def __init__(self, 
                 label: str, rule: Dict[str, Union[int, str]],
                 diagnostic: bool = False, neutral_loss: bool = False) -> None:
        """
        initialize a new static fragmentation rule

        Parameters
        ----------
        label : ``str``
            fragmentation rule label
        rule : ``dict(str:int)``
            rule definition as molecular formula (dictionary mapping element to count)
        diagnostic : ``bool``
            this fragmentation rule is diagnostic for a particular lipid class
        diagnostic : ``bool``, default=False
            this fragmentation rule is diagnostic for a particular lipid class
        neutral_loss : ``bool``, default=False
            this fragmentation rule corresponds to a neutral loss
        """
        super().__init__(True, label, rule, diagnostic, neutral_loss, None)
    
    def mz(self, 
           pre_mz: float, 
           d_label: Optional[int] = None) -> float:
        """ 
        compute m/z for the fragment rule

        Parameters
        ----------
        pre_mz : ``float``
            precursor m/z, used for neutral loss calcs
        d_label : ``int``, optional
            optional deuterium label for computing fragments for labeled lipids, if
            None then do not make any adjustments
        
        Returns
        -------
        rule_mz : ``float``
            fragmentation rule m/z 
        """
        return self._mz(monoiso_mass(self.rule), pre_mz, d_label)
    
    def label(self) -> str:
        """ returns label for this fragmentation rule as ``str`` """
        return self._label()

    
class _FragRuleDynamic(_FragRule):
    """ Dynamic fragmentation rule (molecular formula depends on FA composition) """
    
    def __init__(self, 
                 label: str, rule: Dict[str, Union[int, str]], n_chains: int,
                 diagnostic: bool = False, neutral_loss: bool = False) -> None:
        """
        initialize a new dynamic fragmentation rule

        Parameters
        ----------
        label : ``str``
            fragmentation rule label
        rule : ``dict(str:(str or int))``
            dictionary mapping element to static count (int) or dynamic rule (str) 
        n_chains : ``int``
            number of chains for fragmentation rule
        diagnostic : ``bool``, default=False
            this fragmentation rule is diagnostic for a particular lipid class
        neutral_loss : ``bool``, default=False
            this fragmentation rule corresponds to a neutral loss
        """
        super().__init__(False, label, rule, diagnostic, neutral_loss, n_chains)
    
    def mz(self, 
           pre_mz: float, c: int, u: int, 
           d_label: Optional[int] = None) -> float:
        """ 
        compute m/z for the fragment rule

        Parameters
        ----------
        pre_mz : ``float``
            precursor m/z, used for neutral loss calcs
        c : ``int``
            acyl chain carbon count
        u : ``int``
            acyl chain unsaturation count
        d_label : ``int``, optional
            optional deuterium label for computing fragments for labeled lipids, if
            None then do not make any adjustments
        
        Returns
        -------
        rule_mz : ``float``
            fragmentation rule m/z 
        """
        formula = {}
        for element, count in self.rule.items():
            if type(count) is int:
                formula[element] = count
            elif type(count) is str:
                formula[element] = eval(count.format(c=c, u=u))
        return self._mz(monoiso_mass(formula), pre_mz, d_label)
    
    def label(self, c: int, u: int) -> str:
        """ returns label for this fragmentation rule as ``str`` """
        return self._label().format(c=c, u=u)
    
    
# see which classes have fragmentation rules defined
_FRAG_RULE_CLASSES = [op.splitext(op.split(_)[-1])[0] for _ in glob(op.abspath(op.join(__file__, op.pardir, '_include/rules/LM*')))]


def load_rules(lmaps_prefix: str, ionization: str) -> Tuple[bool, List[_FragRule]]:
    """
    Load all fragmentation rules relevant to a particular lipid class and ionization
    as well as the general rules (`any.yaml`)

    Parameters
    ----------
    lmaps_prefix : ``str``
        LipidMAPS classification prefix
    ionization : ``str``
        "POS" or "NEG"
    
    Returns
    -------
    found : ``bool``
        flag indicating whether there were class-specific rules that were found
    rules : ``list(_FragRule)``
        list of applicable fragmentation rules
    """
    # ionization should be "POS" or "NEG"
    if ionization not in ["POS", "NEG"]:
        msg = "load_rules: ionization must be either 'POS' or 'NEG', was: {}"
        raise ValueError(msg.format(ionization))
    rule_dir = op.abspath(op.join(__file__, op.pardir, '_include/rules'))
    rules = []
    any_path = op.join(rule_dir, 'any.yaml')
    with open(any_path, 'r')as yff:
        rules_ = yaml.safe_load(yff)[ionization]
    found = False
    if lmaps_prefix in _FRAG_RULE_CLASSES:
        yf_pth = op.join(rule_dir, '{}.yaml'.format(lmaps_prefix))
        with open(yf_pth, 'r') as yf:
            ion_rules = yaml.safe_load(yf).get(ionization)
            if ion_rules is not None:
                rules_ += ion_rules
                found = True
    for rule in rules_:
        nl = 'neutral_loss' in rule and rule['neutral_loss']
        diag = 'diagnostic' in rule and rule['diagnostic']
        n_chains = rule['n_chains'] if 'n_chains' in rule else None
        if 'static' in rule and not rule['static']:
            rule = _FragRuleDynamic(rule['label'], rule['rule'], n_chains,
                                    diagnostic=diag, neutral_loss=nl)
        else:
            rule = _FragRuleStatic(rule['label'], rule['rule'],
                                   diagnostic=diag, neutral_loss=nl)
        rules.append(rule)
    return found, rules
