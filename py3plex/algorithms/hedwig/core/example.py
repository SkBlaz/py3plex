'''
Example-related classes.

@author: anze.vavpetic@ijs.si
'''


class Example:
    '''
    Represents an example with its score, label, id and annotations.
    '''
    ClassLabeled = 'class'
    Ranked = 'ranked'

    def __init__(self, id, label, score, annotations=[], weights={}):
        self.id = id
        self.label = label
        self.score = score
        if not type(score) in [str]:
            self.target_type = Example.Ranked
        else:
            self.target_type = Example.ClassLabeled
        self.annotations = annotations
        self.weights = weights

    def __str__(self):
        if self.target_type == Example.Ranked:
            return '<id=%d, score=%.5f, label=%s>' % (self.id,
                                                      self.score,
                                                      self.label)
        else:
            return '<id=%d, class=%s, label=%s>' % (self.id,
                                                    self.score,
                                                    self.label)
