'''
Module for ruleset validation.

@author: anze.vavpetic@ijs.si
'''
from .adjustment import fdr
from .significance import apply_fisher


class Validate:
    def __init__(self, kb, significance_test=apply_fisher, adjustment=fdr):
        self.kb = kb
        self.significance_test = significance_test
        self.adjustment = adjustment

    def test(self, ruleset, alpha=0.05, q=0.01):
        '''
        Tests the given ruleset and returns the significant rules.
        '''
        self.significance_test(ruleset)

        if self.adjustment.__name__ == 'fdr':
            ruleset = self.adjustment(ruleset, q=q)
        elif self.adjustment.__name__ == 'fwer':
            ruleset = self.adjustment(ruleset, alpha=alpha)

        return ruleset
