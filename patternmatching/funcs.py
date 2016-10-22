"""Functional Python Pattern Matching

Python pattern matching using a function-based approach.

TODO:

* Protect Name('result') from binder.

"""

from collections import namedtuple, Sequence
from functools import wraps
from sys import hexversion

infinity = float('inf')


class Case(namedtuple('Case', 'name predicate action')):
    """Three-ple of `name`, `predicate`, and `action`.

    `Matcher` objects successively try a sequence of `Case` predicates. When a
    match is found, the `Case` action is applied.

    """
    pass

base_cases = []


class Mismatch(Exception):
    "Raised by `Matcher` `Case` `action` functions to abort on mismatch."
    pass


class Details(Sequence):
    """Abstract base class extending `Sequence` to define equality and hashing.

    Assumes an attribute, `_details`, exists for comparison and hashing. Used
    by `Pattern` and `PatternMixin` types.

    """
    def __eq__(self, that):
        return self._details == that._details

    def __ne__(self, that):
        return self._details != that._details

    def __hash__(self):
        return hash(self._details)


class Pattern(Details):
    """Wraps a tuple to extend the addition operator.

    >>> Pattern()
    Pattern()
    >>> Pattern([1, 2, 3])
    Pattern(1, 2, 3)
    >>> Pattern() + [1, 2, 3]
    Pattern(1, 2, 3)
    >>> None + Pattern()
    Pattern(None,)
    >>> list(Pattern(4, 5, 6))
    [4, 5, 6]

    """
    def __init__(self, *iterable):
        if len(iterable) == 1:
            iterable = iterable[0]
        is_tuple = isinstance(iterable, tuple)
        self._details = iterable if is_tuple else tuple(iterable)

    def __getitem__(self, index):
        return self._details[index]

    def __len__(self):
        return len(self._details)

    def __add__(self, that):
        if isinstance(that, tuple):
            pass
        elif isinstance(that, Sequence):
            that = tuple(that)
        else:
            that = (that,)
        return Pattern(self._details + that)

    def __radd__(self, that):
        if isinstance(that, tuple):
            pass
        elif isinstance(that, Sequence):
            that = tuple(that)
        else:
            that = (that,)
        return Pattern(that + self._details)

    def __repr__(self):
        return '%s%r' % (type(self).__name__, self._details)

    __str__ = __repr__


class PatternMixin(Details):
    """Abstract base class to wrap a tuple to extend multiplication and
    addition.

    """
    def __getitem__(self, index):
        if index == 0:
            return self
        else:
            raise IndexError

    def __len__(self):
        return 1

    def __add__(self, that):
        return Pattern(self) + that

    def __radd__(self, that):
        return that + Pattern(self)

    def __mul__(self, that):
        return that.__rmul__(self)

    def __rmul__(self, that):
        if not isinstance(that, Sequence):
            that = (that,)
        return type(self)(that, *self._details[1:])

    def __getattr__(self, name):
        return getattr(self._details, name)

    def __repr__(self):
        return repr(self._details)

    __str__ = __repr__


###############################################################################
# Match Case: anyone
###############################################################################

class Anyone(PatternMixin):
    """Match any one thing.

    >>> Anyone()
    anyone
    >>> match('blah', Anyone())
    True
    >>> anyone + [1, 2, 3]
    Pattern(anyone, 1, 2, 3)
    >>> (4, 5) + anyone + None
    Pattern(4, 5, anyone, None)

    """
    def __init__(self):
        self._details = ()

    def __repr__(self):
        return 'anyone'

    __str__ = __repr__

anyone = Anyone()

def anyone_predicate(matcher, value, pattern):
    "Return True if `pattern` is an instance of `Anyone`."
    return isinstance(pattern, Anyone)

def anyone_action(matcher, value, anyone):
    "Return `value` because `anyone` matches any one thing."
    return value

base_cases.append(Case('anyone', anyone_predicate, anyone_action))


###############################################################################
# Match Case: names
###############################################################################

class Name(namedtuple('Name', 'value')):
    """Name objects simply wrap a `value` to be used as a name.

    >>> match([1, 2, 3], [Name('head'), 2, 3])
    True
    >>> bound.head == 1
    True

    """
    pass

class Binder(object):
    """Binder objects return Name objects on attribute lookup.

    A few attributes behave specially:

    * `bind.any` returns an `Anyone` object.
    * `bind._push`, `bind._pop`, and `bind.restore` raise an AttributeError
      because the names would conflict with `Bounder` attributes.

    >>> bind = Binder()
    >>> bind.head
    Name(value='head')
    >>> bind.tail
    Name(value='tail')
    >>> bind.any
    anyone
    >>> bind._push
    Traceback (most recent call last):
        ...
    AttributeError

    """
    def __getattr__(self, name):
        if name == 'any':
            return anyone
        elif name in ('_push', '_pop', 'restore'):
            raise AttributeError
        else:
            return Name(name)

bind = Binder()

def name_predicate(matcher, value, pattern):
    "Return True if `pattern` is an instance of `Name`."
    return isinstance(pattern, Name)

def name_store(matcher, name, value):
    """Store `value` in `matcher.names` with given `name`.

    If `name` is already present in `matcher.names` then raise `Mismatch` on
    inequality between `value` and stored value.

    """
    if name in matcher.names:
        if value != matcher.names[name]:
            raise Mismatch
    matcher.names[name] = value

def name_action(matcher, value, name):
    "Store `value` in `matcher` with name, `name.value`."
    name_store(matcher, name.value, value)
    return value

base_cases.append(Case('names', name_predicate, name_action))


###############################################################################
# Match Case: likes
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

base_cases.append(Case('likes', like_predicate, like_action))

###############################################################################
# Match Case: types
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

base_cases.append(Case('types', type_predicate, type_action))


###############################################################################
# Match Case: literals
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

base_cases.append(Case('literals', literal_predicate, literal_action))


###############################################################################
# Match Case: sequences
###############################################################################

def sequence_predicate(matcher, value, pattern):
    return (
        isinstance(value, type(pattern))
        and isinstance(pattern, Sequence)
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

base_cases.append(Case('sequences', sequence_predicate, sequence_action))


###############################################################################
# Match Case: patterns
###############################################################################

_Repeat = namedtuple('Repeat', 'pattern min max greedy')

class Repeat(PatternMixin):
    def __init__(self, pattern=(), min=0, max=infinity, greedy=True):
        self._details = _Repeat(pattern, min, max, greedy)

    def __call__(self, min=0, max=infinity, greedy=True, pattern=()):
        return type(self)(pattern, min, max, greedy)

repeat = Repeat()
maybe = repeat(max=1)
anything = anyone * repeat
something = anyone * repeat(min=1)
padding = anyone * repeat(greedy=False)


_Group = namedtuple('Group', 'pattern name')

class Group(PatternMixin):
    def __init__(self, pattern=(), name=''):
        self._details = _Group(pattern, name)

    def __call__(self, name='', pattern=()):
        return type(self)(pattern, name)

group = Group()


_Options = namedtuple('Options', 'options')

class Options(PatternMixin):
    def __init__(self, *options):
        self._details = _Options(options)

    def __call__(self, options=()):
        return type(self)(*options)

    def __rmul__(self, that):
        if not isinstance(that, Sequence):
            that = (that,)
        return type(self)(*that)

    def __repr__(self):
        return '%s%r' % (type(self).__name__, self._details.options)

    __str__ = __repr__


class Either(Options):
    pass

either = Either()


class Exclude(Options):
    pass

exclude = Exclude()


NONE = object()

def pattern_predicate(matcher, value, pattern):
    return isinstance(pattern, (Pattern, PatternMixin))

def pattern_action(matcher, sequence, pattern):
    names = matcher.names
    len_sequence = len(sequence)

    def visit(pattern, index, offset, count):
        len_pattern = len(pattern)

        if index == len_pattern:
            yield offset
            return

        while True:
            item = pattern[index]

            if isinstance(item, Repeat):
                if count > item.max:
                    return

                if item.greedy:
                    if offset < len_sequence:
                        for end in visit(item.pattern, 0, offset, count):
                            for stop in visit(pattern, index, end, count + 1):
                                yield stop

                    if count >= item.min:
                        for stop in visit(pattern, index + 1, offset, 0):
                            yield stop
                else:
                    if count >= item.min:
                        for stop in visit(pattern, index + 1, offset, 0):
                            yield stop

                    if offset < len_sequence:
                        for end in visit(item.pattern, 0, offset, count):
                            for stop in visit(pattern, index, end, count + 1):
                                yield stop

                return

            elif isinstance(item, Group):
                for end in visit(item.pattern, 0, offset, 0):
                    if item.name:
                        prev = names.pop(item.name, NONE)
                        names[item.name] = sequence[offset:end]

                    for stop in visit(pattern, index + 1, end, 0):
                        yield stop

                    if item.name and prev is not NONE:
                        names[item.name] = prev

                return

            elif isinstance(item, Either):
                for option in item.options:
                    for end in visit(option, 0, offset, 0):
                        for stop in visit(pattern, index + 1, end, 0):
                            yield stop
                return

            elif isinstance(item, Exclude):
                for option in item.options:
                    for end in visit(option, 0, offset, 0):
                        return

            else:
                if offset >= len_sequence:
                    return
                else:
                    try:
                        matcher.visit(sequence[offset], item)
                    except Mismatch:
                        return

                # if offset >= len_sequence:
                #     return
                # elif matcher.match(sequence[offset], item): # TODO: Wrong. See sequences.
                #     pass
                # else:
                #     return

            index += 1
            offset += 1

            if index == len_pattern:
                yield offset
                return

    for end in visit(pattern, 0, 0, 0):
        return sequence[:end]

base_cases.append(Case('patterns', pattern_predicate, pattern_action))


###############################################################################
# Store bound names in a stack.
###############################################################################

class Bounder(object):
    """Bounder objects.

    todo

    """
    def __init__(self, maps=[]):
        self._maps = maps

    def __getattr__(self, name):
        return self[-1][name]

    def __getitem__(self, index):
        return self._maps[index]

    def __len__(self):
        return len(self._maps)

    def _push(self, names):
        self._maps.append(names)

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

    def __repr__(self):
        return '%s(%r)' % (type(self).__name__, self._maps)

    __str__ = __repr__


###############################################################################
# Matcher objects put it all together.
###############################################################################

class Matcher(object):
    """Matcher objects.

    todo

    >>> matcher = Matcher()
    >>> matcher.match(None, None)
    True
    >>> matcher.match(0, int)
    True
    >>> match = matcher.match
    >>> match([1, 2, 3], [1, bind.middle, 3])
    True
    >>> matcher.bound.middle
    2
    >>> bound = matcher.bound
    >>> match([(1, 2, 3), 4, 5], [bind.any, 4, bind.tail])
    True
    >>> bound.tail
    5

    """
    def __init__(self, cases=base_cases, bounder=Bounder):
        self._bound = bounder()
        self._cases = cases
        self._names = {}

    def match(self, value, pattern):
        _names = self._names
        try:
            _names['result'] = self.visit(value, pattern)
        except Mismatch:
            return False
        else:
            self._bound._push(_names.copy())
        finally:
            _names.clear()
        return True

    def visit(self, value, pattern):
        for name, predicate, action in self._cases:
            if predicate(self, value, pattern):
                return action(self, value, pattern)
        raise Mismatch

    @property
    def bound(self):
        return self._bound

    @property
    def names(self):
        return self._names


matcher = Matcher()
match = matcher.match
bound = matcher.bound
