"""Experimental pattern matching."""

from sys import hexversion
from collections import namedtuple, Sequence

Case = namedtuple('Case', 'name predicate rule')
_cases = []

class Mismatch(Exception):
    pass

###############################################################################
# Match names
###############################################################################

Name = namedtuple('Name', 'value')

class Binder(object):
    def __getattr__(self, name):
        if name == 'result':
            raise AttributeError("can not bind name 'result'")
        return Name(name)

bind = Binder()

def _name_predicate(matcher, value, pattern):
    return isinstance(pattern, Name)
    
def _name_rule(matcher, value, pattern):
    name = pattern.value
    if name == 'any':
        return value
    elif name in matcher.names:
        if value != matcher.names[name]:
            raise Mismatch
    matcher.names[name] = value
    return value

_cases.append(Case('names', _name_predicate, _name_rule))

###############################################################################
# Match patterns
###############################################################################

Pattern = namedtuple('Pattern', 'pattern')

def like(pattern):
    return Pattern(pattern)

def _pattern_predicate(matcher, value, pattern):
    return isinstance(pattern, Pattern)

import re

if hexversion > 0x03000000:
    unicode = str

_pattern_errors = (
    AttributeError, LookupError, NotImplementedError, TypeError, ValueError
)

def _pattern_rule(matcher, value, pattern):
    pattern = pattern.pattern

    if isinstance(pattern, (str, unicode)):
        if not isinstance(value, (str, unicode)):
            raise Mismatch
        func = lambda value: re.match(pattern, value)
    else:
        func = pattern

    try:
        result = func(value)
    except _pattern_errors:
        raise Mismatch

    if not result:
        raise Mismatch
    return result

_cases.append(Case('patterns', _pattern_predicate, _pattern_rule))

###############################################################################
# Match types
###############################################################################

def _type_predicate(matcher, value, pattern):
    return type(value) == type and type(pattern) == type

def _type_rule(matcher, value, pattern):
    if not issubclass(value, pattern):
        raise Mismatch
    return value

_cases.append(Case('types', _type_predicate, _type_rule))

###############################################################################
# Match literals
###############################################################################

if hexversion < 0x03000000:
    _literal_types = (type(None), bool, int, float, long, complex, basestring)
else:
    _literal_types = (type(None), bool, int, float, complex, str, bytes)

def _literal_predicate(matcher, value, pattern):
    return (
        isinstance(value, type(pattern))
        and isinstance(value, _literal_types)
    )

def _literal_rule(matcher, value, pattern):
    if value != pattern:
        raise Mismatch
    return value

_cases.append(Case('literals', _literal_predicate, _literal_rule))

###############################################################################
# Match sequences
###############################################################################

def _sequence_predicate(matcher, value, pattern):
    return (
        isinstance(value, type(pattern))
        and isinstance(value, Sequence)
        and len(value) == len(pattern)
    )

if hexversion < 0x03000000:
    from itertools import izip as zip

# todo: support bind.many
# class Many(object):
#     def __init__(self, count=slice(None)):
#         """Initialize Many object.

#         `count` should be a `slice` object such that:
#             `slice(None, None, None)` - any number of values
#             `slice(None, 10, None)` - exactly ten values
#             `slice(0, 10, None)` - zero to ten values (inclusive)
#             `slice(5, None, None)` - five or more values
#         The third argument to slice may define a type annotation (a la PEP 484)
#         """
#         self.count = count
#     def __getitem__(self, index):
#         if isinstance(index, slice):
#             return self.__class__(count=index)
#         else:
#             return self.__class__(count=slice(index))
# many = Many()
# # Many should have special significance in _sequence_rule which permits
# # binding to multiple values.

def _sequence_rule(matcher, value, pattern):
    args = (matcher.visit(one, two) for one, two in zip(value, pattern))
    type_value = type(value)
    if hasattr(type_value, '_make'):
        return type_value._make(args)
    else:
        return type_value(args)

_cases.append(Case('sequences', _sequence_predicate, _sequence_rule))

###############################################################################
# Matching algorithm
###############################################################################

class Matcher(object):
    def __init__(self, cases=_cases):
        self.names = {}
        self.cases = _cases
    def __call__(self):
        return self.__class__(cases=self.cases)
    def visit(self, value, pattern):
        for name, predicate, rule in self.cases:
            if predicate(self, value, pattern):
                return rule(self, value, pattern)
        raise Mismatch

matcher = Matcher()

###############################################################################
# Bound names
###############################################################################

class AttrMap(object):
    def __init__(self, names):
        self._attrs = names
    def __getitem__(self, name):
        return self._attrs[name]

class Bounder(object):
    def __init__(self):
        self._maps = [None]
    def __getattr__(self, name):
        return self._maps[-1][name]
    def push(self, names):
        self._maps.append(AttrMap(names))
    def pop(self):
        return self._maps.pop()

bound = Bounder()

###############################################################################
# Match function
###############################################################################

def match(value, pattern, push=False, matcher=matcher):
    try:
        matcher = matcher()
        result = matcher.visit(value, pattern)
        names = matcher.names
        names['result'] = result
        if not push:
            bound.pop()
        bound.push(names)
        return True
    except Mismatch:
        return False
