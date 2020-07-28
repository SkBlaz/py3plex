'''
The rule class.

@author: anze.vavpetic@ijs.si
'''
import json
from collections import defaultdict

from .predicate import UnaryPredicate, BinaryPredicate
from .example import Example
from .helpers import avg, std
from .settings import DEFAULT_ANNOTATION_NAME


class Rule:
    '''
    Represents a rule, along with its description, examples and statistics.
    '''
    def __init__(self, kb, predicates=[], target=None):
        self.predicates = predicates
        self.kb = kb
        self.covered_examples = kb.get_full_domain()
        self.target_type = kb.target_type
        self.target = target

        # Allow only unary predicates
        for pred in predicates:
            if isinstance(pred, UnaryPredicate):
                self.covered_examples &= pred.domain[pred.input_var]

        self.head_var = None
        if self.predicates:
            self.head_var = self.predicates[0].input_var

        # Dictionary of predicates that share a certain variable
        self.shared_var = {self.head_var: self.predicates}

        # Predicates that currently can be specialized
        self.latest_var = self.head_var

        # Statistics
        self.score = -1
        self.coverage = -1
        self.mean = -1
        self.sd = -1
        self.distribution = {}
        self.__refresh_coverage()
        self.__refresh_statistics()

        # Validation
        self.pval = -1

    def clone(self):
        '''
        Returns a clone of this rule. The predicates themselves are NOT cloned.
        '''
        new_rule = Rule(self.kb, target=self.target)
        new_rule.predicates = self.predicates[:]
        new_rule.covered_examples = self.covered_examples
        new_rule.latest_var = self.latest_var
        new_rule.head_var = self.head_var
        new_rule.shared_var = {}
        for var in self.shared_var:
            new_rule.shared_var[var] = self.shared_var[var][:]
        return new_rule

    def clone_negate(self, target_pred):
        '''
        Returns a copy of this rule where 'taget_pred' is negated.
        '''
        new_rule = self.clone()

        # Create the instance of the child pred
        producer_pred = target_pred.producer_predicate
        var_name = target_pred.input_var
        members = target_pred.domain[target_pred.input_var].copy()
        members.invert()
        neg_pred = UnaryPredicate(target_pred.label,
                                  members,
                                  self.kb,
                                  producer_pred=producer_pred,
                                  custom_var_name=var_name,
                                  negated=True)

        new_rule._replace_predicate(target_pred, neg_pred)
        return new_rule

    def clone_swap_with_subclass(self, target_pred, child_pred_label):
        '''
        Returns a copy of this rule where
        'target_pred' is swapped for 'child_pred_label'.
        '''
        new_rule = self.clone()

        # Create the instance of the child pred
        producer_pred = target_pred.producer_predicate
        var_name = target_pred.input_var
        child_pred = UnaryPredicate(child_pred_label,
                                    self.kb.get_members(child_pred_label),
                                    self.kb,
                                    producer_pred=producer_pred,
                                    custom_var_name=var_name)

        new_rule._replace_predicate(target_pred, child_pred)
        return new_rule

    def clone_append(self, predicate_label, producer_pred, bin=False):
        '''
        Returns a copy of this rule where 'predicate_label'
        is appended to the rule.
        '''
        if not bin:
            new_rule = self.clone()
            predicate = UnaryPredicate(predicate_label,
                                       self.kb.get_members(predicate_label),
                                       self.kb,
                                       producer_pred=producer_pred)
            new_rule.predicates.append(predicate)
            new_rule.shared_var[producer_pred.output_var].append(predicate)
        else:
            new_rule = self.clone()
            predicate = BinaryPredicate(predicate_label,
                                        self.kb.get_members(predicate_label),
                                        self.kb,
                                        producer_pred=producer_pred)
            new_rule.predicates.append(predicate)

            # Introduce new variable
            new_rule.shared_var[predicate.output_var] = [predicate]
            new_rule.shared_var[predicate.input_var].append(predicate)
            new_rule.latest_var = predicate.output_var

        new_rule.__refresh_coverage()
        new_rule.__refresh_statistics()
        return new_rule

    def _replace_predicate(self, target, replacement):
        '''
        Replaces 'target' with 'replacement' in the rule.
        '''
        Rule.__replace(self.predicates, target, replacement)
        self.covered_examples = self.covered_examples & \
            replacement.domain[replacement.input_var]

        # Reference possible consumers
        replacement.consumer_predicate = target.consumer_predicate

        # Update the backlinks
        if replacement.producer_predicate:
            replacement.producer_predicate.consumer_predicate = replacement
        if replacement.consumer_predicate:
            replacement.consumer_predicate.producer_predicate = replacement

        # Update the shared var list
        shared_list = self.shared_var[target.input_var]
        Rule.__replace(shared_list, target, replacement)

        # Recalc the covered examples and statistics
        self.__refresh_coverage()
        self.__refresh_statistics()

    @staticmethod
    def __replace(l, target, replacement):
        idx = l.index(target)
        l[idx] = replacement

    def __refresh_coverage(self):
        '''
        Recalculates the covered examples.
        '''
        var = self.shared_var[self.head_var]
        self.covered_examples = self.__covered_examples(var)

    def __covered_examples(self, predicates):
        '''
        Recursively calculates the covered examples for a given set of
        predicates that share a variable.
        '''
        covered_examples = self.kb.get_full_domain()
        for pred in predicates:
            if isinstance(pred, BinaryPredicate):

                # Predicates that share the new variable, without 'pred'
                shared = self.shared_var[pred.output_var][:]
                shared.remove(pred)
                existential_cov_examples = self.__covered_examples(shared)
                reverse_members = self.kb.get_reverse_members(pred.label)
                tmp_covered = self.kb.get_empty_domain()

                # Calculate all examples that have a pair for this relation
                for idx in self.kb.bits_to_indices(existential_cov_examples):
                    if reverse_members.has_key(idx):
                        tmp_covered |= reverse_members[idx]
                covered_examples &= tmp_covered
            else:
                covered_examples &= pred.domain[pred.input_var]
        return covered_examples

    def __refresh_statistics(self):
        '''
        Recalculates the statistics for this rule.
        '''
        self.coverage = self.covered_examples.count()

        indices = self.kb.bits_to_indices(self.covered_examples)
        ex_scores = [self.kb.get_score(idx) for idx in indices]

        if self.target_type == Example.Ranked:
            self.mean = avg(ex_scores)
            self.sd = std(ex_scores)
            self.score = self.kb.score_fun(self)
        else:
            self.distribution = defaultdict(int)
            for score in ex_scores:
                self.distribution[score] += 1
            self.score = self.kb.score_fun(self)

    def similarity(self, rule):
        '''
        Calculates the similarity between this rule and 'rule'.
        '''
        intersection = (self.covered_examples & rule.covered_examples).count()
        union = (self.covered_examples | rule.covered_examples).count()
        if union == 0:
            return 1
        else:
            return intersection / float(union)

    def size(self):
        '''
        Returns the number of conjunts.
        '''
        return len(self.predicates)

    def examples(self, positive_only=False):
        '''
        Returns the covered examples.
        '''
        indices = self.kb.bits_to_indices(self.covered_examples)
        all_examples = [self.kb.examples[idx] for idx in indices]

        if positive_only:
            return filter(lambda ex: ex.score == self.target, all_examples)
        else:
            return all_examples

    @property
    def positives(self):
        return self.distribution[self.target]

    def precision(self):
        if self.coverage:
            return self.positives / float(self.coverage)
        else:
            return 0

    def rule_report(self, show_uris=False, latex=False):
        '''
        Rule as string with some statistics.
        '''
        if latex:
            return self._latex_report()
        else:
            return self._plain_report(show_uris=show_uris)

    def _plain_report(self, show_uris=False, human=lambda label, rule: label):
        '''
        Plain text rule report
        '''
        s = self._plain_conjunctions(show_uris=show_uris, human=human) + ' ' + \
            self._plain_statistics()
        return s

    def _plain_conjunctions(self,
                            show_uris=False,
                            human=lambda label, rule: label):
        conjuncts = []
        for pred in self.predicates:

            label = pred.label
            if '#' in label and not show_uris:
                label = pred.label.split('#')[-1]
                label = human(label, self)

            if isinstance(pred, UnaryPredicate):
                anno_names = self.kb.annotation_name.get(
                    pred.label, [DEFAULT_ANNOTATION_NAME])
                predicate_label = '_and_'.join(anno_names)

                if pred.negated:
                    predicate_label = '~' + predicate_label

                conj = '%s(%s, %s)' % (predicate_label, pred.input_var, label)
            else:
                conj = '%s(%s, %s)' % (label, pred.input_var, pred.output_var)
            conjuncts.append(conj)

        s = ', '.join(conjuncts)
        return s

    def _plain_statistics(self):
        if self.target_type == Example.ClassLabeled:
            stats = (self.coverage, self.positives, self.precision(),
                     self.kb.score_fun.__name__, self.score, self.pval)
            return '[cov=%d, pos=%d, prec=%.3f, %s=%.3f, pval=%.3f]' % stats

        else:
            return '[size=%d, score=%.3f]' % (self.coverage, self.score)

    def _latex_report(self):
        '''
        Latex rule report
        '''
        conjuncts = []
        for pred in self.predicates:

            label = pred.label
            if '#' in label:
                label = pred.label.split('#')[-1]

            if isinstance(pred, UnaryPredicate):
                if pred.negated:
                    label = r'$\neg$' + label
                conj = '%s(%s)' % (label, pred.input_var)
            else:
                conj = '%s(%s, %s)' % (label, pred.input_var, pred.output_var)
            conjuncts.append(conj)

        s = r' $\wedge$ '.join(conjuncts)

        return s

    def __str__(self):
        return self.rule_report(show_uris=False)

    @staticmethod
    def ruleset_report(rules,
                       show_uris=False,
                       latex=False,
                       human=lambda label, rule: label):
        if latex:
            return Rule._latex_ruleset_report(rules)
        else:
            return Rule._plain_ruleset_report(rules,
                                              show_uris=show_uris,
                                              human=human)

    @staticmethod
    def _latex_ruleset_report(rules):
        target, var = list(rules)[0].target, list(rules)[0].head_var
        if target:
            head = '%s(%s) $\leftarrow$ ' % (target, var)
        else:
            head = ''

        _tex_report = \
            r'\begin{tabular}{clccccc}\hline' + '\n' \
            r'\textbf{\#} & \textbf{Rule} & \textbf{TP} & \textbf{FP} & \textbf{Precision} & \textbf{Lift} & \textbf{p-value}\\\hline' + '\n'

        for i, rule in enumerate(
                sorted(rules, key=lambda r: r.score, reverse=True)):
            rule_report = rule._latex_report()
            stats = (i + 1, head + rule_report, rule.distribution[rule.target],
                     rule.coverage - rule.distribution[rule.target],
                     rule.distribution[rule.target] / float(rule.coverage),
                     rule.score, rule.pval)
            _tex_report += r'%d & \texttt{%s} & %d & %d & %.2f & %.2f & %.3f\\' % stats
            _tex_report += '\n'

        _tex_report += \
            r'\hline' + '\n' \
            r'\end{tabular}' + '\n'

        return _tex_report

    @staticmethod
    def _plain_ruleset_report(rules,
                              show_uris=False,
                              human=lambda label, rule: label):

        target, var = list(rules)[0].target, list(rules)[0].head_var
        if target:
            head = '\'%s\'(%s) <--\n\t' % (target, var)
        else:
            head = ''

        ruleset = []
        for rule in sorted(rules, key=lambda r: r.score, reverse=True):
            rule = rule._plain_report(show_uris=show_uris, human=human)
            ruleset.append(rule)

        return head + '\n\t'.join(ruleset)

    @staticmethod
    def ruleset_examples_json(rules_per_target, show_uris=False):
        examples_output = []
        for target_class, rules in rules_per_target:
            class_examples = []
            for _, rule in enumerate(
                    sorted(rules, key=lambda r: r.score, reverse=True)):
                examples = rule.examples()
                class_examples.append(
                    (rule._plain_conjunctions(), [ex.label
                                                  for ex in examples]))
            examples_output.append((target_class, class_examples))
        return examples_output

    @staticmethod
    def to_json(rules_per_target, show_uris=False):
        results = {}
        for target, rules in rules_per_target:
            results[target] = [str(rule) for rule in rules]

        return json.dumps(results, indent=2)
