'''
Predicate-related classes.

@author: anze.vavpetic@ijs.si
'''

class Predicate:
    '''
    Represents a predicate as a member of a certain rule.
    '''
    i = -1

    def __init__(self, label, kb, producer_pred):
        self.label = label
        self.kb = kb

        # Whose predicate's out var this predicate consumes
        self.producer_predicate = producer_pred
        if self.producer_predicate:
            producer_pred.consumer_predicate = self

        # Which predicate consumes this predicate's out var
        self.consumer_predicate = None

    @staticmethod
    def _avar():
        '''
        Anonymous var name generator.
        '''
        Predicate.i = Predicate.i + 1
        return 'X%d' % Predicate.i


class UnaryPredicate(Predicate):
    '''
    A unary predicate.
    '''
    def __init__(self, label, members, kb,
                 producer_pred=None,
                 custom_var_name=None,
                 negated=False):
        Predicate.__init__(self, label, kb, producer_pred)

        if not producer_pred:
            if not custom_var_name:
                self.input_var = Predicate._avar()
            else:
                self.input_var = custom_var_name
        else:
            self.input_var = producer_pred.output_var

        self.output_var = self.input_var
        self.negated = negated
        self.domain = {self.input_var: members}


class BinaryPredicate(Predicate):
    '''
    A binary predicate.
    '''
    def __init__(self, label, pairs, kb, producer_pred=None):
        '''
        The predicate's name and the tuples satisfying it.
        '''
        Predicate.__init__(self, label, kb, producer_pred)

        # The input var should match with the producers output var
        if not producer_pred:
            self.input_var = Predicate._avar()
        else:
            self.input_var = producer_pred.output_var

        self.output_var = Predicate._avar()
        if producer_pred:
            prod_out_var = self.producer_predicate.output_var
            potential_inputs = self.producer_predicate.domain[prod_out_var]

            # Find which inputs have pairs
            inputs = potential_inputs & kb.get_domains(label)[0]
            outputs = kb.get_empty_domain()
            for el1 in kb.bits_to_indices(inputs):
                outputs |= pairs[el1]
        else:
            # No producer predicate.
            inputs, outputs = kb.get_domains(label)

        self.domain = {self.input_var: inputs, self.output_var: outputs}
