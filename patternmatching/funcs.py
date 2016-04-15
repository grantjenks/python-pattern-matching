"""Function-based Implementation

Python pattern matching using a function-based approach.

"""

from sys import hexversion
from collections import namedtuple, Sequence

Case = namedtuple('Case', 'name predicate action')
cases = []

class Mismatch(Exception):
    pass

###############################################################################
# Match anyone
###############################################################################

class Anyone(object): pass

anyone = Anyone()

def anyone_predicate(matcher, value, pattern):
    return isinstance(pattern, Anyone)

def anyone_action(matcher, value, pattern):
    return value

cases.append(Case('anyone', anyone_predicate, anyone_action))

###############################################################################
# Match names
###############################################################################

Name = namedtuple('Name', 'value')

class Binder(object):
    def __getattr__(self, name):
        if name == 'any':
            return anyone
        elif name in ('_push', '_pop', 'restore'):
            raise AttributeError
        else:
            return Name(name)

bind = Binder()

def name_predicate(matcher, value, pattern):
    return isinstance(pattern, Name)
    
def name_store(matcher, name, value):
    if name in matcher.names:
        if value != matcher.names[name]:
            raise Mismatch
    matcher.names[name] = value

def name_action(matcher, value, pattern):
    name_store(matcher, pattern.value, value)
    return value

cases.append(Case('names', name_predicate, name_action))

###############################################################################
# Match Like objects
###############################################################################

Like = namedtuple('Like', 'pattern name')

def like(pattern, name='result'):
    return Like(pattern, name)

def like_predicate(matcher, value, pattern):
    return isinstance(pattern, Like)

import re

if hexversion > 0x03000000:
    unicode = str

like_errors = (
    AttributeError, LookupError, NotImplementedError, TypeError, ValueError
)

def like_action(matcher, value, pattern):
    name = pattern.name
    pattern = pattern.pattern

    if isinstance(pattern, (str, unicode)):
        if not isinstance(value, (str, unicode)):
            raise Mismatch
        func = lambda value: re.match(pattern, value)
    else:
        func = pattern

    try:
        result = func(value)
    except like_errors:
        raise Mismatch

    if not result:
        raise Mismatch

    if name is not None:
        name_store(matcher, name, result)

    return result

cases.append(Case('likes', like_predicate, like_action))

###############################################################################
# Match types
###############################################################################

def type_predicate(matcher, value, pattern):
    return type(pattern) == type

def type_action(matcher, value, pattern):
    if type(value) == type and issubclass(value, pattern):
        return value
    elif isinstance(value, pattern):
        return value
    else:
        raise Mismatch

cases.append(Case('types', type_predicate, type_action))

###############################################################################
# Match literals
###############################################################################

if hexversion < 0x03000000:
    literal_types = (type(None), bool, int, float, long, complex, basestring)
else:
    literal_types = (type(None), bool, int, float, complex, str, bytes)

def literal_predicate(matcher, value, pattern):
    return (
        isinstance(pattern, literal_types)
        and isinstance(value, literal_types)
    )

def literal_action(matcher, value, pattern):
    if value != pattern:
        raise Mismatch
    return value

cases.append(Case('literals', literal_predicate, literal_action))

###############################################################################
# Match sequences
###############################################################################

def sequence_predicate(matcher, value, pattern):
    return (
        isinstance(value, type(pattern))
        and isinstance(value, Sequence)
        and len(value) == len(pattern)
    )

if hexversion < 0x03000000:
    from itertools import izip as zip

def sequence_action(matcher, value, pattern):
    args = (matcher.visit(one, two) for one, two in zip(value, pattern))
    type_value = type(value)
    if issubclass(type_value, tuple) and hasattr(type_value, '_make'):
        return type_value._make(args) # namedtuple case
    else:
        return type_value(args)

cases.append(Case('sequences', sequence_predicate, sequence_action))

###############################################################################
# Matching algorithm
###############################################################################

class Matcher(object):
    def __init__(self, cases=cases):
        self.names = {}
        self.cases = cases
    def __call__(self):
        return self.__class__(cases=self.cases)
    def visit(self, value, pattern):
        for name, predicate, action in self.cases:
            if predicate(self, value, pattern):
                return action(self, value, pattern)
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
    def __repr__(self):
        return repr(self._attrs)

from functools import wraps

class Bounder(object):
    def __init__(self):
        self._maps = []
    def __getitem__(self, index):
        return self._maps[index]
    def __getattr__(self, name):
        return self[-1][name]
    def __len__(self):
        return len(self._maps)
    def __repr__(self):
        return repr(self._maps)
    def _push(self, names):
        self._maps.append(AttrMap(names))
    def _pop(self):
        return self._maps.pop()
    def restore(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = len(self)
            try:
                return func(*args, **kwargs)
            finally:
                while len(self) > start:
                    self._pop()
        return wrapper

bound = Bounder()

###############################################################################
# Match function
###############################################################################

def match(value, pattern, matcher=matcher):
    try:
        matcher = matcher()
        result = matcher.visit(value, pattern)
        names = matcher.names
        if names:
            bound._push(names)
        return True
    except Mismatch:
        return False
