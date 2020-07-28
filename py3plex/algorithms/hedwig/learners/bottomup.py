'''
Main learner class.

@author: anze.vavpetic@ijs.si
'''
from collections import defaultdict

from hedwig.core import UnaryPredicate, Rule, Example
from hedwig.core.settings import logger
from hedwig.stats.significance import is_redundant
from hedwig.stats.scorefunctions import interesting


class BottomUpLearner:
    '''
    Bottom-up learner.
    '''
    Similarity = 'similarity'
    Improvement = 'improvement'
    Default = 'default'

    def __init__(self,
                 kb,
                 n=None,
                 min_sup=1,
                 sim=1,
                 depth=4,
                 target=None,
                 use_negations=False):
        self.kb = kb
        self.n = n  # Beam length
        self.min_sup = min_sup
        self.sim = sim
        self.extending = Learner.Improvement
        self.depth = depth  # Max number of conjunctions
        self.use_negations = use_negations

        if kb.is_discrete_target():
            self.target = list(
                self.kb.class_values)[0] if not target else target
        else:
            self.target = None

        self.pruned_subclasses = self._pruned_subclasses()
        self.pruned_superclasses_closure = self._pruned_superclasses()
        self.implicit_roots = self._implicit_roots()

    def _pruned_subclasses(self):
        min_sup = lambda pred: self.kb.n_members(pred) >= self.min_sup
        pruned_subclasses = {}
        for pred in self.kb.predicates:
            subclasses = self.kb.get_subclasses(pred)
            pruned_subclasses[pred] = filter(min_sup, subclasses)

        return pruned_subclasses

    def _pruned_superclasses(self):
        min_sup = lambda pred: self.kb.n_members(pred) >= self.min_sup
        pruned_superclasses = {}
        for pred in self.kb.predicates:
            superclasses = self.kb.super_classes(pred)
            pruned_superclasses[pred] = filter(min_sup, superclasses)

        return pruned_superclasses

    def _implicit_roots(self):
        implicit_roots = set()
        n_examples = self.kb.n_examples()
        for pred in self.kb.predicates:
            if self.kb.n_members(pred) == n_examples:
                implicit_roots.add(pred)

        return implicit_roots

    def get_subclasses(self, pred):
        return self.pruned_subclasses[pred.label]

    def get_superclasses(self, pred):
        return self.pruned_superclasses_closure[pred]

    def is_implicit_root(self, pred):
        return pred in self.implicit_roots

    def induce(self):
        '''
        Induces rules for the given knowledge base.
        '''
        pass

    def bottom_clause(self):
        pass
