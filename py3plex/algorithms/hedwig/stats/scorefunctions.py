'''
Score function definitions.

@author: anze.vavpetic@ijs.si
'''
from math import sqrt


def z_score(rule):
    return sqrt(rule.coverage) * (rule.mean - rule.kb.mean) / rule.kb.sd


def t_score(rule):
    return sqrt(rule.coverage) * (rule.mean - rule.kb.mean) / rule.sd


def enrichment_score(rule):
    # The enrichment score of a rule covering all examples is 1
    if rule.coverage == rule.kb.n_examples():
        return 1.0
    if rule.coverage == 0:
        return -1 / float(rule.kb.n_examples())
    increment = {}
    incr1 = 1 / float(rule.coverage)
    incr2 = 1 / float(rule.kb.n_examples() - rule.coverage)
    max_diff = 0
    # All examples
    for ex in rule.kb.examples:
        increment[ex] = -incr2
    for ex in rule.examples():
        increment[ex] = incr1
    partial = 0
    for ex in rule.kb.examples:
        partial += increment[ex]
        if partial > max_diff:
            max_diff = partial
    return max_diff


def wracc(rule):
    nX = rule.coverage
    N = len(rule.kb.examples)
    nXY = rule.distribution[rule.target]
    nY = rule.kb.distribution[rule.target]
    if nX:
        return nX / float(N) * (nXY / float(nX) - nY / float(N))
    else:
        return 0


def precision(rule):
    nX = rule.coverage
    nXY = rule.distribution[rule.target]
    if nX:
        return nXY / float(nX)
    else:
        return 0


def chisq(rule):
    N = len(rule.kb.examples)
    z = rule.distribution[rule.target] / float(N)
    x = rule.coverage / float(N)
    y = rule.kb.distribution[rule.target] / float(N)
    if x not in [0, 1] and y not in [0, 1]:
        return N * (z - x * y)**2 / float(x * y * (1 - x) * (1 - y))
    else:
        return 0


def lift(rule):
    nX = float(rule.coverage)
    N = float(len(rule.kb.examples))
    nXY = rule.distribution[rule.target]
    nY = rule.kb.distribution[rule.target]

    if nX != 0 and N != 0:
        return (nXY / nX) / (nY / N)
    else:
        return 0


def leverage(rule):
    nX = float(rule.coverage)
    N = float(len(rule.kb.examples))
    nXY = rule.distribution[rule.target]
    nY = rule.kb.distribution[rule.target]

    if N != 0:
        return nXY / N - (nX / N) * (nY / N)
    else:
        return 0


def kaplan_meier_AUC(rule):
    examples = rule.kb.bits_to_indices(rule.covered_examples)
    n_examples = float(len(examples))

    if n_examples == 0:
        return 0.0

    def n_alive(examples, day):
        def is_alive(ex):
            return rule.kb.get_score(ex) > day

        return len(filter(is_alive, examples))

    auc, day = 0, 0
    prev = -1
    while True:
        alive = n_alive(examples, day)
        day += 14

        curr = alive / n_examples
        if prev != -1:
            auc += (prev + curr) / 2.0
        prev = curr

        if alive == 0:
            break

    #print auc
    return auc


# Bounds of interest for each score function
# A rule is interesting if its score is in (A, B] as defined below.
_bounds = {
    z_score: (0, float('inf')),
    t_score: (0, float('inf')),
    kaplan_meier_AUC: (0, float('inf')),
    enrichment_score: (-float('inf'), 1),
    wracc: (0, 1),
    precision: (0, 1),
    chisq: (0, float('inf')),
    lift: (1, float('inf')),
    leverage: (0, 1)
}


def interesting(rule):
    '''
    Checks if a given rule is interesting for the given score function
    '''
    score_fun = rule.kb.score_fun
    filtered_bounds = _bounds[score_fun][0] < rule.score <= _bounds[score_fun][
        1]
    return filtered_bounds
