'''
Multiple-testing adjustment methods.

@author: anze.vavpetic@ijs.si
'''


def _holdout(ruleset):
    '''
    TODO: The holdout approach.
    '''
    return ruleset


def fwer(ruleset, alpha=0.05):
    '''
    The Holm-Bonferroni direct adjustment method to control the FWER.
    '''
    m = float(len(list(ruleset)))
    ruleset = sorted(ruleset, key=lambda r: r.pval)
    for k, rule in enumerate(ruleset):
        if rule.pval > alpha/(m + 1 - (k + 1)):
            ruleset = ruleset[:k]
            break

    return ruleset


def fdr(ruleset, q=0.05):
    '''
    The Benjamini-Hochberg-Yekutieli direct adjustment
    method to control the FDR.
    '''
    m = float(len(list(ruleset)))
    ruleset = sorted(ruleset, key=lambda r: r.pval)
    for k, rule in enumerate(ruleset):
        if rule.pval > ((k + 1)*q)/m:
            ruleset = ruleset[:k]
            break

    return ruleset

def none(ruleset):
    return ruleset
