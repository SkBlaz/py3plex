'''
Significance testing methods.

@author: anze.vavpetic@ijs.si
'''
import scipy.stats as st


def is_redundant(rule, new_rule):
    '''
    Computes the redundancy coefficient of a new rule compared to its
    immediate generalization.

    Rules with a coeff > 1 are deemed non-redundant.
    '''
    return _fisher(new_rule, 'greater') > _fisher(rule, 'greater')


def fisher(rule):
    '''
    Fisher's p-value for one rule.
    '''
    return _fisher(rule, 'two-sided')


def _fisher(rule, alternative):
    '''
    Fisher's p-value for one rule.
        fisher.two_tail   ==> alternative = 'two-sided'
        fisher.left_tail  ==> alternative = 'less'
        fisher.right_tail ==> alternative = 'greater'
    '''
    N = float(len(rule.kb.examples))
    nX = float(rule.coverage)
    nY = rule.kb.distribution[rule.target]
    nXY = rule.distribution[rule.target]
    nXnotY = nX - nXY
    nnotXY = nY - nXY
    nnotXnotY = N - nXnotY - nnotXY
    return st.fisher_exact([[nXY, nXnotY], [nnotXY, nnotXnotY]],
                           alternative=alternative)[1]


def apply_fisher(ruleset):
    '''
    Fisher's exact test to test rule significance.
    '''
    for rule in ruleset:
        rule.pval = fisher(rule)
