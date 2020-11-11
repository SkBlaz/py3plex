'''
Main learner class.

@author: anze.vavpetic@ijs.si
'''
from itertools import combinations

from ..core import Rule, UnaryPredicate

from .learner import Learner


class OptimalLearner(Learner):
    '''
    Finds the optimal top-k rules.
    '''
    def __init__(self,
                 kb,
                 n=None,
                 min_sup=1,
                 sim=1,
                 depth=4,
                 target=None,
                 use_negations=False,
                 optimal_subclass=True):
        Learner.__init__(self,
                         kb,
                         n=n,
                         min_sup=min_sup,
                         sim=sim,
                         depth=depth,
                         target=target,
                         use_negations=use_negations)

    def induce(self):
        '''
        Induces rules for the given knowledge base.
        '''
        kb = self.kb

        def has_min_sup(pred):
            return kb.get_members(pred).count() >= self.min_sup

        all_predicates = filter(has_min_sup, kb.predicates)
        rules = []
        for depth in range(1, self.depth + 1):
            for attrs in combinations(all_predicates, depth):
                rule = Rule(kb,
                            predicates=self._labels_to_predicates(attrs),
                            target=self.target)
                rules.append(rule)
        rules = sorted(rules, key=lambda r: r.score, reverse=True)
        return rules[:self.n]

    def _labels_to_predicates(self, labels):
        predicates = []
        producer_pred = None
        for label in labels:
            members = self.kb.get_members(label)
            predicates.append(
                UnaryPredicate(label,
                               members,
                               self.kb,
                               producer_pred=producer_pred,
                               custom_var_name='X'))
            producer_pred = predicates[-1]
        return predicates
