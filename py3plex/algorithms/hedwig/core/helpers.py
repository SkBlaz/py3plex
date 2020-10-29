'''
Helper functions.

@author: anze.vavpetic@ijs.si
'''
from math import sqrt

from .settings import W3C, HEDWIG


def avg(x):
    n = float(len(x))
    if n:
        return sum(x) / n
    else:
        return 0


def std(x):
    n = float(len(x))
    if n:
        return sqrt((sum(i * i for i in x) - sum(x)**2 / n) / n)
    else:
        return 0


def user_defined(uri):
    '''
    Is this resource user defined?
    '''
    return not uri.startswith(W3C) and not uri.startswith(HEDWIG) and \
        not anonymous_uri(uri)


def anonymous_uri(uri):
    return not uri.startswith('http')
