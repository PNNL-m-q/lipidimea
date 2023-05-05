"""
LipidIMEA/msms/_fragmentation_rules.py

Dylan Ross (dylan.ross@pnnl.gov)

    Rules defining fragments formed for different lipid classes
"""


import yaml
from mzapy.isotopes import monoiso_mass


# lipid classes with fragmentation rules defined
_FRAG_RULE_CLASSES = [
    'Cer', 'PC', 'PE', 'PG', 
    'PS', 'SM', 'TG'
]


class _FragRule():
    
    def __init__(self, label, ionization, lipid_class, rule, diagnostic, neutral_loss, n_chains, acyl_chain_type):
        self.lbl = label
        self.ionization = ionization
        self.lipid_class = lipid_class
        self.rule = rule
        self.diagnostic = diagnostic
        self.neutral_loss = neutral_loss
        self.n_chains = n_chains
        acyl_chain_type = acyl_chain_type
    
    def _mz(self, mz, pre_mz, d_label):
        """ determine whether to treat this m/z as a neutral loss """
        # self._mz() defined by subclass, computes the m/z 
        d = monoiso_mass({'H': -d_label, 'D': d_label}) if d_label is not None else 0.
        if self.neutral_loss:
            return pre_mz - mz - d
        else:
            return mz + d
    
    def _label(self, label):
        """ add a * to diagnostic fragment labels """
        return '*' + label if self.diagnostic else label
        
    
class _FragRuleStatic(_FragRule):
    
    def __init__(self, 
                 label, ionization, lipid_class, rule,
                 diagnostic=False, neutral_loss=False, n_chains=1, acyl_chain_type='standard',
                 ):
        """
        Parameters
        ----------
        label : ``str``
        ionization : ``str``
            ionization mode, 'POS' or 'NEG'
        lipid_class : ``str``
            lipid class abbreviation
            TODO (Dylan Ross): this could later be adapted to use LipidMAPS classification
                               system instead of simple lipid class abbreviation
        rule : ``dict(str:int)``
            dictionary mapping element to count
        """
        self.static = True
        super().__init__(label, ionization, lipid_class, rule, diagnostic, neutral_loss, n_chains, acyl_chain_type)
    
    def mz(self, pre_mz, d_label=None):
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
                 label, ionization, lipid_class, rule,
                 diagnostic=False, neutral_loss=False, n_chains=1, acyl_chain_type='standard'):
        """
        Parameters
        ----------
        label : ``str``
        ionization : ``str``
            ionization mode, 'POS' or 'NEG'
        lipid_class : ``str``
            lipid class abbreviation
            TODO (Dylan Ross): this could later be adapted to use LipidMAPS classification
                               system instead of simple lipid class abbreviation
        rule : ``dict(str:(str or int))``
            dictionary mapping element to static count (int) or dynamic rule (str) 
        """
        self.static = False
        super().__init__(label, ionization, lipid_class, rule, diagnostic, neutral_loss, n_chains, acyl_chain_type)
    
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
    
    
def _load_rules(lipid_class, ionization):
    rules = []
    with open('../../../../git/LipidIMEA/LipidIMEA/msms/rules/any.yaml', 'r')as yff:
        rules_ = yaml.safe_load(yff)['ionization'][ionization]
    if lipid_class in _FRAG_RULE_CLASSES:
        yf = '../../../../git/LipidIMEA/LipidIMEA/msms/rules/{}.yaml'.format(lipid_class)
        with open(yf, 'r') as yff:
            rules_ += yaml.safe_load(yff)['ionization'][ionization]
    for rule in rules_:
        nl = 'neutral_loss' in rule and rule['neutral_loss']
        diag = 'diagnostic' in rule and rule['diagnostic']
        n_chains = rule['n_chains'] if 'n_chains' in rule else 1
        if 'static' in rule and not rule['static']:
            rule = _FragRuleDynamic(rule['label'], ionization, lipid_class, rule['rule'],
                                    diagnostic=diag, neutral_loss=nl, n_chains=n_chains)
        else:
            rule = _FragRuleStatic(rule['label'], ionization, lipid_class, rule['rule'],
                                   diagnostic=diag, neutral_loss=nl, n_chains=n_chains)
        rules.append(rule)
    return rules

