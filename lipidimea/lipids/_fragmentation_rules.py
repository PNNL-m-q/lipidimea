"""
lipidimea/lipids/_fragmentation_rules.py

Dylan Ross (dylan.ross@pnnl.gov)

    Rules defining fragments formed for different lipid classes
"""


from os import path as op
from glob import glob

import yaml
from mzapy.isotopes import monoiso_mass


class _FragRule():
    
    def __init__(self, 
                 static, label, ionization, lmaps_prefix, rule, diagnostic, neutral_loss, n_chains):
        self.static = static
        self.lbl = label
        self.ionization = ionization
        self.lmaps_prefix = lmaps_prefix
        self.rule = rule
        self.diagnostic = diagnostic
        self.neutral_loss = neutral_loss
        self.n_chains = n_chains
    
    def _mz(self, 
            mz, pre_mz, d_label):
        """ determine whether to treat this m/z as a neutral loss """
        # self.mz() defined by subclass, computes the m/z 
        d = monoiso_mass({'H': -d_label, 'D': d_label}) if d_label is not None else 0.
        if self.neutral_loss:
            return pre_mz - mz - d
        else:
            return mz + d
    
    def _label(self, 
               label):
        """ add a * to diagnostic fragment labels """
        return '*' + label if self.diagnostic else label
        
    
class _FragRuleStatic(_FragRule):
    
    def __init__(self, 
                 label, ionization, lmaps_prefix, rule,
                 diagnostic=False, neutral_loss=False):
        """
        Parameters
        ----------
        label : ``str``
        ionization : ``str``
            ionization mode, 'POS' or 'NEG'
        lmaps_prefix : ``str``
            LipidMAPS classification prefix
        rule : ``dict(str:int)``
            dictionary mapping element to count
        """
        super().__init__(True, label, ionization, lmaps_prefix, rule, diagnostic, neutral_loss, None)
    
    def mz(self, 
           pre_mz, 
           d_label=None):
        """ 
        Parameters
        ----------
        pre_mz : ``float``
            precursor m/z, used for neutral loss calcs
        """
        formula = self.rule
        return self._mz(monoiso_mass(formula), pre_mz, d_label)
    
    def label(self):
        return self._label(self.lbl)

    
class _FragRuleDynamic(_FragRule):
    
    def __init__(self, 
                 label, ionization, lmaps_prefix, rule, n_chains,
                 diagnostic=False, neutral_loss=False):
        """
        Parameters
        ----------
        label : ``str``
        ionization : ``str``
            ionization mode, 'POS' or 'NEG'
        lmaps_prefix : ``str``
            LipidMAPS classification prefix
        rule : ``dict(str:(str or int))``
            dictionary mapping element to static count (int) or dynamic rule (str) 
        n_chains : ``int``
            number of chains for fragmentation rule
        """
        super().__init__(False, label, ionization, lmaps_prefix, rule, diagnostic, neutral_loss, n_chains)
    
    def mz(self, pre_mz, c, u, d_label=None):
        """ 
        Parameters
        ----------
        pre_mz : ``float``
            precursor m/z, used for neutral loss calcs
        c : ``int``
            acyl chain carbon count
        u : ``int``
            acyl chain unsaturation count
        """
        formula = {}
        for element, count in self.rule.items():
            if type(count) is int:
                formula[element] = count
            elif type(count) is str:
                formula[element] = eval(count.format(c=c, u=u))
        return self._mz(monoiso_mass(formula), pre_mz, d_label)
    
    def label(self, c, u):
        return self._label(self.lbl.format(c=c, u=u))
    
    
# see what classes have fragmentation rules defined
_FRAG_RULE_CLASSES = [op.splitext(op.split(_)[-1])[0] for _ in glob(op.abspath(op.join(__file__, op.pardir, op.pardir, '_include/rules/LM*')))]


def load_rules(lmaps_prefix, ionization):
    """
    Load all fragmentation rules relevant to a particular lipid class and ionization

    Parameters
    ----------
    lmaps_prefix : ``str``
        LipidMAPS classification prefix
    ionization : ``str``
        "POS" or "NEG"
    
    Returns
    -------
    rules : ``list(_FragRule)``
        list of applicable fragmentation rules
    """
    rule_dir = op.abspath(op.join(__file__, op.pardir, op.pardir, '_include/rules'))
    rules = []
    any_path = op.join(rule_dir, 'any.yml')
    with open(any_path, 'r')as yff:
        rules_ = yaml.safe_load(yff)[ionization]
    if lmaps_prefix in _FRAG_RULE_CLASSES:
        yf_pth = op.join(rule_dir, '{}.yml'.format(lmaps_prefix))
        with open(yf_pth, 'r') as yf:
            rules_ += yaml.safe_load(yf)[ionization]
    for rule in rules_:
        nl = 'neutral_loss' in rule and rule['neutral_loss']
        diag = 'diagnostic' in rule and rule['diagnostic']
        n_chains = rule['n_chains'] if 'n_chains' in rule else None
        if 'static' in rule and not rule['static']:
            rule = _FragRuleDynamic(rule['label'], ionization, lmaps_prefix, rule['rule'], n_chains,
                                    diagnostic=diag, neutral_loss=nl)
        else:
            rule = _FragRuleStatic(rule['label'], ionization, lmaps_prefix, rule['rule'],
                                   diagnostic=diag, neutral_loss=nl)
        rules.append(rule)
    return rules

