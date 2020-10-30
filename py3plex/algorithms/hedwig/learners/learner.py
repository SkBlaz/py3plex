'''
Main learner class.

@author: anze.vavpetic@ijs.si
'''

from ..core import UnaryPredicate, Rule, Example
from ..core.settings import logger
from ..stats.significance import is_redundant
from ..stats.scorefunctions import interesting


class Learner:
    '''
    Learner class, supporting various types of induction
    from the knowledge base.

    TODO:
        - bottom clause approach
        - feature construction
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
                 use_negations=False,
                 optimal_subclass=False):
        self.kb = kb
        self.n = n  # Beam length
        self.min_sup = min_sup
        self.sim = sim
        self.extending = Learner.Improvement
        self.depth = depth  # Max number of conjunctions
        self.use_negations = use_negations
        self.optimal_subclass = optimal_subclass

        if kb.is_discrete_target():
            self.target = list(
                self.kb.class_values)[0] if not target else target
        else:
            self.target = None

        self.pruned_subclasses = self._pruned_subclasses()
        self.pruned_superclasses_closure = self._pruned_superclasses()
        self.implicit_roots = self._implicit_roots()

    def _pruned_subclasses(self):
        def min_sup(pred):
            return self.kb.n_members(pred) >= self.min_sup

        pruned_subclasses = {}
        for pred in self.kb.predicates:
            subclasses = self.kb.get_subclasses(pred)
            pruned_subclasses[pred] = filter(min_sup, subclasses)

        return pruned_subclasses

    def _pruned_superclasses(self):
        def min_sup(pred):
            return self.kb.n_members(pred) >= self.min_sup

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
        root_pred = self.kb.get_root()

        rules = [Rule(self.kb, predicates=[root_pred], target=self.target)]

        rules = self.__induce_level(rules)

        interesting_rules = list(filter(interesting, rules))

        return interesting_rules

    def __induce_level(self, rules):
        '''
        Specializes the rules for the last level with unary predicates.
        '''
        while True:
            old_score = self.group_score(rules)
            new_rules = rules[:]
            for i, rule in enumerate(rules):
                specializations = self.specialize(rule)
                self.extend(new_rules, specializations)

            # Take the first N rules
            rules = sorted(new_rules,
                           key=lambda rule: rule.score,
                           reverse=True)[:self.n]

            new_score = self.group_score(rules)

            logger.debug("Old score: %.3f, New score: %.3f" %
                         (old_score, new_score))

            if 1 - abs(old_score / (new_score + 0.0001)) < 0.01:
                break

        return rules

    def extend(self, rules, specializations):
        '''
        Extends the ruleset in the given way.
        '''
        if self.extending == Learner.Default:
            return rules.extend(specializations)
        elif self.extending == Learner.Improvement:
            return self.extend_replace_worst(rules, specializations)
        elif self.extending == Learner.Similarity:
            return self.extend_with_similarity(rules, specializations)

    def extend_with_similarity(self, rules, specializations):
        '''
        Extends the list based on how similar is 'new_rule'
        to the rules contained in 'rules'.
        '''
        for new_rule in specializations:
            tmp_rules = rules[:]
            for rule in tmp_rules:
                sim = rule.similarity(new_rule)
                if sim >= self.sim and len(rules) > 0.5 * self.n:
                    break
            else:
                rules.append(new_rule)

    def extend_replace_worst(self, rules, specializations):
        '''
        Extends the list by replacing the worst rules.
        '''
        def is_similar(new_rule):
            for rule in rules[:]:
                if rule.similarity(new_rule) == 1:
                    return True
            return False

        improved = False
        for new_rule in sorted(specializations, key=lambda rule: rule.score):
            worst = sorted(rules, key=lambda rule: rule.score)[0]
            if len(rules) < self.n:
                rules.append(new_rule)
                improved = True
            elif new_rule.score > worst.score and not is_similar(new_rule):
                self._replace(rules, worst, new_rule)
                improved = True
        return improved

    def _replace(self, rules, worst, new_rule):
        idx = rules.index(worst)
        rules[idx] = new_rule

    def specialize(self, rule):
        '''
        Returns a list of all specializations of 'rule'.
        '''
        def is_unary(p):
            return isinstance(p, UnaryPredicate)

        def specialize_optimal_subclass(rule):
            rules = []
            eligible_preds = rule.shared_var[rule.latest_var]
            for pred in filter(is_unary, eligible_preds):
                for sub_class in self.get_subclasses(pred):
                    logger.debug('Swapping with %s' % sub_class)
                    new_rule = rule.clone_swap_with_subclass(pred, sub_class)
                    if self.can_specialize(new_rule):
                        rules.append(new_rule)
                        rules.extend(specialize_optimal_subclass(new_rule))
            return rules

        logger.debug('Specializing rule: %s' % rule)
        specializations = []
        eligible_preds = rule.shared_var[rule.latest_var]

        # Swapping unary predicates with subclasses, swap only
        # the predicates with the latest variable
        if not self.optimal_subclass:
            for pred in filter(is_unary, eligible_preds):
                logger.debug('Predicate to swap: %s' % pred.label)
                for sub_class in self.get_subclasses(pred):
                    logger.debug('Swapping with %s' % sub_class)
                    new_rule = rule.clone_swap_with_subclass(pred, sub_class)
                    if self.can_specialize(new_rule):
                        specializations.append(new_rule)
        else:
            specializations.extend(specialize_optimal_subclass(rule))

        if self.use_negations:

            # Negate the last predicate
            for pred in filter(is_unary, eligible_preds):
                logger.debug('Predicate to negate: %s' % pred.label)
                new_rule = rule.clone_negate(pred)
                if self.can_specialize(new_rule):
                    specializations.append(new_rule)

        # This makes sure we are not specializing a default rule by appending,
        # this rule should instead be reached by the specialization step above.
        if not (len(eligible_preds) == 1 and
                (eligible_preds[0].label == self.kb.get_root().label
                 or self.is_implicit_root(eligible_preds[0].label))):

            # Calculate the union of superclasses of each predicate
            supers = set()
            for pred in eligible_preds:
                if type(pred) == str:
                    supers.update(self.get_superclasses(pred.label))
                    supers.add(pred)

            # Calculate the top-most left-most non-ancestor
            for lvl in sorted(self.kb.levels.keys()):

                level = self.kb.levels[lvl]
                diff = level.difference(supers)
                if diff:

                    # The next predicate to specialize with is the left-most
                    for pred in sorted(list(diff)):

                        # Appending a new predicate, the last predicate
                        # is always the producer
                        last_pred = rule.predicates[-1]
                        new_rule = rule.clone_append(pred,
                                                     producer_pred=last_pred)
                        if self.can_specialize(new_rule) and \
                           self.non_redundant(rule, new_rule):
                            specializations.append(new_rule)
                            break

        # Introduce new binary relation
        if isinstance(rule.predicates[-1], UnaryPredicate):
            specializations.extend(self.specialize_add_relation(rule))

        logger.debug('All specializations %s' %
                     [str(rule) for rule in specializations])

        return specializations

    def specialize_add_relation(self, rule):
        '''
        Specialize with new binary relation.
        '''
        specializations = []
        for pred in self.kb.binary_predicates:

            last_pred = rule.predicates[-1]
            new_rule = rule.clone_append(pred,
                                         producer_pred=last_pred,
                                         bin=True)

            if self.can_specialize(new_rule):
                specializations.append(new_rule)
        return specializations

    def can_specialize(self, rule):
        '''
        Is the rule good enough to be further refined?
        '''
        return rule.coverage >= self.min_sup and rule.size() <= self.depth

    def non_redundant(self, rule, new_rule):
        '''
        Is the rule non-redundant compared to its immediate generalization?
        '''
        if new_rule.score < rule.score:
            return False

        if rule.target_type == Example.Ranked:
            return True
        else:
            return not is_redundant(rule, new_rule)

    def group_score(self, rules):
        '''
        Calculates the score of the whole list of rules.
        '''
        return sum([rule.score for rule in rules])
