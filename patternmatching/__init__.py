"""Python Pattern Matching

Python pattern matching library.

"""

from collections.abc import Sequence, Mapping
from functools import wraps

infinity = float('inf')


class Record:
    """Mutable "named tuple"-like base class."""
    __slots__ = ()

    def __init__(self, *args):
        for field, value in zip(self.__slots__, args):
            setattr(self, field, value)

    def __getitem__(self, index):
        return getattr(self, self.__slots__[index])

    def __eq__(self, that):
        if not isinstance(that, type(self)):
            return NotImplemented
        return (self.__slots__ == that.__slots__
                and all(item == iota for item, iota in zip(self, that)))

    def __repr__(self):
        args = ', '.join(repr(item) for item in self)
        return '%s(%s)' % (type(self).__name__, args)

    def __getstate__(self):
        return tuple(self)

    def __setstate__(self, state):
        self.__init__(*state)


class Case(Record):
    """Three-ple of `name`, `predicate`, and `action`.

    `Matcher` objects successively try a sequence of `Case` predicates. When a
    match is found, the `Case` action is applied.

    """
    __slots__ = 'name', 'predicate', 'action'

base_cases = []


class Mismatch(Exception):
    "Raised by `action` functions of `Case` records to abort on mismatch."
    pass


###############################################################################
# Match Case: __match__
###############################################################################

def match_predicate(matcher, value, pattern):
    "Return True if `pattern` has `__match__` attribute."
    return hasattr(pattern, '__match__')

def match_action(matcher, value, pattern):
    "Match `value` by calling `__match__` attribute of `pattern`."
    attr = getattr(pattern, '__match__')
    return attr(matcher, value)

base_cases.append(Case('__match__', match_predicate, match_action))


###############################################################################
# Match Case: patterns
###############################################################################

class APattern(Sequence):
    """Abstract base class extending `Sequence` to define equality and hashing.

    Defines one slot, `_details`, for comparison and hashing.

    Used by `Pattern` and `PatternMixin` types.

    """
    # pylint: disable=abstract-method
    __slots__ = ('_details',)

    def __eq__(self, that):
        return self._details == that._details

    def __ne__(self, that):
        return self._details != that._details

    def __hash__(self):
        return hash(self._details)

    def __match__(self, matcher, value):
        """Match `pattern` to `value` with `Pattern` semantics.

        The `Pattern` type is used to define semantics like regular expressions.

        >>> match([0, 1, 2], [0, 1] + anyone)
        True
        >>> match([0, 0, 0, 0], 0 * repeat)
        True
        >>> match('blue', either('red', 'blue', 'yellow'))
        True
        >>> match([2, 4, 6], exclude(like(lambda num: num % 2)) * repeat(min=3))
        True

        """
        names = matcher.names
        len_value = len(value)

        # Life is easier with generators. I tried twice to write "visit"
        # recursively without success. Consider:
        #
        # match('abc', 'a' + 'b' * repeat * group + 'bc')
        #
        # Notice the "'b' * repeat" clause is nested within a group
        # clause. When recursing, the "'b' * repeat" clause will match greedily
        # against 'abc' at offset 1 but then the whole pattern will fail as
        # 'bc' does not match at offset 2. So backtracking of the nested clause
        # is required. Generators communicate multiple end offsets and support
        # the needed backtracking.

        def visit(pattern, index, offset, count):
            len_pattern = len(pattern)

            if index == len_pattern:
                yield offset
                return

            item = pattern[index]

            if isinstance(item, Repeat):
                if count > item.max:
                    return

                if item.greedy:
                    if offset < len_value:
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

                    if offset < len_value:
                        for end in visit(item.pattern, 0, offset, count):
                            for stop in visit(pattern, index, end, count + 1):
                                yield stop

                return

            elif isinstance(item, Group):
                for end in visit(item.pattern, 0, offset, 0):
                    if item.name is None:
                        for stop in visit(pattern, index + 1, end, 0):
                            yield stop
                    else:
                        segment = value[offset:end]
                        names.push()

                        try:
                            name_store(names, item.name, segment)
                        except Mismatch:
                            names.undo()
                        else:
                            for stop in visit(pattern, index + 1, end, 0):
                                yield stop

                            names.undo()

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

                for end in visit(pattern, index + 1, offset + 1, 0):
                    yield end

            else:
                if offset >= len_value:
                    return

                names.push()

                try:
                    matcher.visit(value[offset], item)
                except Mismatch:
                    pass
                else:
                    for end in visit(pattern, index + 1, offset + 1, 0):
                        yield end

                names.undo()

                return

        for end in visit(self, 0, 0, 0):
            return value[:end]

        raise Mismatch


def make_tuple(value):
    """Return value as tuple.

    >>> make_tuple((1, 2, 3))
    (1, 2, 3)
    >>> make_tuple('abc')
    ('a', 'b', 'c')
    >>> make_tuple([4, 5, 6])
    (4, 5, 6)
    >>> make_tuple(None)
    (None,)

    """
    if isinstance(value, tuple):
        return value
    if isinstance(value, Sequence):
        return tuple(value)
    return (value,)


class Pattern(APattern):
    """Wrap tuple to extend addition operator.

    >>> Pattern()
    Pattern()
    >>> Pattern([1, 2, 3])
    Pattern(1, 2, 3)
    >>> Pattern() + [1, 2, 3]
    Pattern(1, 2, 3)
    >>> None + Pattern()
    Pattern(None)
    >>> list(Pattern(4, 5, 6))
    [4, 5, 6]

    """
    def __init__(self, *args):
        self._details = make_tuple(args[0] if len(args) == 1 else args)

    def __getitem__(self, index):
        return self._details[index]

    def __len__(self):
        return len(self._details)

    def __add__(self, that):
        return Pattern(self._details + make_tuple(that))

    def __radd__(self, that):
        return Pattern(make_tuple(that) + self._details)

    def __repr__(self):
        args = ', '.join(repr(value) for value in self._details)
        return '%s(%s)' % (type(self).__name__, args)


class PatternMixin(APattern):
    """Abstract base class to wrap a tuple to extend multiplication and
    addition.

    """
    def __getitem__(self, index):
        if index == 0:
            return self
        raise IndexError

    def __len__(self):
        return 1

    def __add__(self, that):
        return Pattern(self) + that

    def __radd__(self, that):
        return that + Pattern(self)

    def __mul__(self, that):
        return that.__rmul__(self)

    def __getattr__(self, name):
        return getattr(self._details, name)

    def __repr__(self):
        pairs = zip(self._details.__slots__, self._details)
        tokens = ('%s=%s' % (name, repr(value)) for name, value in pairs)
        return '%s(%s)' % (type(self).__name__, ', '.join(tokens))


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

    def __match__(self, matcher, value):
        "Pass because `anyone` matches any one thing."
        pass

    def __repr__(self):
        return 'anyone'

anyone = Anyone()


###############################################################################
# Match Case: repeat
###############################################################################

def sequence(value):
    """Return value as sequence.

    >>> sequence('abc')
    'abc'
    >>> sequence(1)
    (1,)
    >>> sequence([1])
    [1]

    """
    return value if isinstance(value, Sequence) else (value,)

class _Repeat(Record):
    __slots__ = 'pattern', 'min', 'max', 'greedy'

class Repeat(PatternMixin):
    """Pattern specifying repetition with min/max count and greedy parameters.

    Inherits from `PatternMixin` which defines multiplication operators to
    capture patterns.

    >>> Repeat()
    Repeat(pattern=(), min=0, max=inf, greedy=True)
    >>> repeat = Repeat()
    >>> repeat(max=1)
    Repeat(pattern=(), min=0, max=1, greedy=True)
    >>> maybe = repeat(max=1)
    >>> Repeat(anyone)
    Repeat(pattern=anyone, min=0, max=inf, greedy=True)
    >>> anyone * repeat
    Repeat(pattern=anyone, min=0, max=inf, greedy=True)
    >>> anything = anyone * repeat
    >>> anyone * repeat(min=1)
    Repeat(pattern=anyone, min=1, max=inf, greedy=True)
    >>> something = anyone * repeat(min=1)
    >>> padding = anyone * repeat(greedy=False)

    """
    def __init__(self, pattern=(), min=0, max=infinity, greedy=True):
        # pylint: disable=redefined-builtin
        self._details = _Repeat(pattern, min, max, greedy)

    def __rmul__(self, that):
        return type(self)(sequence(that), *tuple(self._details)[1:])

    def __call__(self, min=0, max=infinity, greedy=True, pattern=()):
        # pylint: disable=redefined-builtin
        return type(self)(pattern, min, max, greedy)

repeat = Repeat()
maybe = repeat(max=1)
anything = anyone * repeat
something = anyone * repeat(min=1)
padding = anyone * repeat(greedy=False)


###############################################################################
# Match Case: groups
###############################################################################

class _Group(Record):
    __slots__ = 'pattern', 'name'

class Group(PatternMixin):
    """Pattern specifying a group with name parameter.

    Inherits from `PatternMixin` which defines multiplication operators to
    capture patterns.

    >>> Group()
    Group(pattern=(), name=None)
    >>> Group(['red', 'blue', 'yellow'], 'color')
    Group(pattern=['red', 'blue', 'yellow'], name='color')
    >>> group = Group()
    >>> ['red', 'blue', 'yellow'] * group('color')
    Group(pattern=['red', 'blue', 'yellow'], name='color')

    """
    def __init__(self, pattern=(), name=None):
        self._details = _Group(pattern, name)

    def __rmul__(self, that):
        return type(self)(sequence(that), *tuple(self._details)[1:])

    def __call__(self, name=None, pattern=()):
        return type(self)(pattern, name)

group = Group()


###############################################################################
# Match Case: options
###############################################################################

class _Options(Record):
    __slots__ = ('options',)

class Options(PatternMixin):
    "Pattern specifying a sequence of options to match."
    def __init__(self, *options):
        self._details = _Options(tuple(map(sequence, options)))

    def __call__(self, *options):
        return type(self)(*options)

    def __rmul__(self, that):
        return type(self)(*sequence(that))

    def __repr__(self):
        args = ', '.join(map(repr, self._details.options))
        return '%s(%s)' % (type(self).__name__, args)


class Either(Options):
    "Pattern specifying that any of options may match."
    pass

either = Either()


class Exclude(Options):
    "Pattern specifying that none of options may match."
    pass

exclude = Exclude()


###############################################################################
# Match Case: names
###############################################################################

class Name(Record):
    """Name objects simply wrap a `value` to be used as a name.

    >>> match([1, 2, 3], [Name('head'), 2, 3])
    True
    >>> bound.head == 1
    True

    """
    __slots__ = ('value',)

    def __match__(self, matcher, value):
        "Store `value` in `matcher` with `name` and return `value`."
        name_store(matcher.names, self.value, value)

def name_store(names, name, value):
    """Store `value` in `names` with given `name`.

    If `name` is already present in `names` then raise `Mismatch` on inequality
    between `value` and stored value.

    """
    if name in names:
        if value == names[name]:
            pass  # Prefer equality comparison to inequality.
        else:
            raise Mismatch
    names[name] = value

class Binder:
    """Binder objects return Name objects on attribute lookup.

    A few attributes behave specially:

    * `bind.any` returns an `Anyone` object.
    * `bind.push`, `bind.pop`, and `bind.reset` raise an AttributeError
      because the names would conflict with `Bounder` attributes.

    >>> bind = Binder()
    >>> bind.head
    Name('head')
    >>> bind.tail
    Name('tail')
    >>> bind.any
    anyone
    >>> bind.push
    Traceback (most recent call last):
        ...
    AttributeError

    """
    def __getattr__(self, name):
        if name == 'any':
            return anyone
        if name in ('push', 'pop', 'reset'):
            raise AttributeError
        return Name(name)

bind = Binder()


###############################################################################
# Match Case: likes
###############################################################################

import re

like_errors = (
    AttributeError, LookupError, NotImplementedError, TypeError, ValueError
)

class Like(Record):
    # pylint: disable=missing-docstring
    __slots__ = 'pattern', 'name'

    def __match__(self, matcher, value):
        """Apply `pattern` to `value` and store result in `matcher`.

        Given `pattern` is expected as `Like` instance and deconstructed by
        attribute into `pattern` and `name`.

        When `pattern` is text then it is used as a regular expression.

        When `name` is None then the result is not stored in `matcher.names`.

        Raises `Mismatch` if callable raises exception in `like_errors` or
        result is falsy.

        >>> match('abcdef', like('abc.*'))
        True
        >>> match(123, like(lambda num: num % 2 == 0))
        False

        """
        pattern = self.pattern
        name = self.name

        if isinstance(pattern, str):
            if not isinstance(value, str):
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
            name_store(matcher.names, name, result)

def like(pattern, name='match'):
    """Return `Like` object with given `pattern` and `name`, default "match".

    >>> like('abc.*')
    Like('abc.*', 'match')
    >>> like('abc.*', 'prefix')
    Like('abc.*', 'prefix')

    """
    return Like(pattern, name)


###############################################################################
# Match Case: types
###############################################################################

def type_predicate(matcher, value, pattern):
    "Return True if `pattern` is an instance of `type`."
    return isinstance(pattern, type)

def type_action(matcher, value, pattern):
    """Match `value` as subclass or instance of `pattern`.

    >>> match(1, int)
    True
    >>> match(True, bool)
    True
    >>> match(True, int)
    True
    >>> match(bool, int)
    True
    >>> match(0.0, int)
    False
    >>> match(float, int)
    False

    """
    if isinstance(value, type) and issubclass(value, pattern):
        return value
    if isinstance(value, pattern):
        return value
    raise Mismatch

base_cases.append(Case('types', type_predicate, type_action))


###############################################################################
# Match Case: literals
###############################################################################

literal_types = (type(None), bool, int, float, complex, str, bytes)

def literal_predicate(matcher, value, pattern):
    "Return True if `value` and `pattern` instance of `literal_types`."
    literal_pattern = isinstance(pattern, literal_types)
    return literal_pattern and isinstance(value, literal_types)

def literal_action(matcher, value, pattern):
    """Match `value` as equal to `pattern`.

    >>> match(1, 1)
    True
    >>> match('abc', 'abc')
    True
    >>> match(1, 1.0)
    True
    >>> match(1, True)
    True

    """
    if value == pattern:
        return value
    raise Mismatch

base_cases.append(Case('literals', literal_predicate, literal_action))


###############################################################################
# Match Case: equality
###############################################################################

def equality_predicate(matcher, value, pattern):
    "Return True if `value` equals `pattern`."
    try:
        return value == pattern
    except Exception:  # pylint: disable=broad-except
        return False

def equality_action(matcher, value, pattern):
    """Match `value` as equal to `pattern`.

    >>> identity = lambda value: value
    >>> match(identity, identity)
    True
    >>> match('abc', 'abc')
    True
    >>> match(1, 1.0)
    True
    >>> match(1, True)
    True

    """
    return value

base_cases.append(Case('equality', equality_predicate, equality_action))


###############################################################################
# Match Case: sequences
###############################################################################

def sequence_predicate(matcher, value, pattern):
    """Return True if `value` is instance of type of `pattern` and `pattern` is
    instance of Sequence and lengths are equal.

    """
    return isinstance(pattern, Sequence) and isinstance(value, type(pattern))

def sequence_action(matcher, value, pattern):
    """Iteratively match items of `pattern` with `value` in sequence.

    Return tuple of results of matches.

    >>> match([0, 'abc', {}], [int, str, dict])
    True
    >>> match((0, True, bool), (0.0, 1, int))
    True
    >>> match([], ())
    False

    """
    if len(value) != len(pattern):
        raise Mismatch

    pairs = zip(value, pattern)
    return tuple(matcher.visit(item, iota) for item, iota in pairs)

base_cases.append(Case('sequences', sequence_predicate, sequence_action))


###############################################################################
# Store bound names in a stack.
###############################################################################

class Bounder:
    """Stack for storing names bound to values for `Matcher`.

    >>> Bounder()
    Bounder([])
    >>> bound = Bounder([{'foo': 0}])
    >>> bound.foo
    0
    >>> len(bound)
    1
    >>> bound.pop()
    {'foo': 0}
    >>> len(bound)
    0
    >>> bound.push({'bar': 1})
    >>> len(bound)
    1

    """
    def __init__(self, maps=()):
        self._maps = list(maps)

    def __getattr__(self, attr):
        try:
            return self._maps[-1][attr]
        except (IndexError, KeyError):
            raise AttributeError(attr)

    def __getitem__(self, key):
        try:
            return self._maps[-1][key]
        except IndexError:
            raise KeyError(key)

    def __eq__(self, that):
        return self._maps[-1] == that

    def __ne__(self, that):
        return self._maps[-1] != that

    def __iter__(self):
        return iter(self._maps[-1])

    def __len__(self):
        return len(self._maps)

    def push(self, mapping):
        # pylint: disable=missing-docstring
        self._maps.append(mapping)

    def pop(self):
        # pylint: disable=missing-docstring
        return self._maps.pop()

    def reset(self, func=None):
        # pylint: disable=missing-docstring
        if func is None:
            del self._maps[:]
        else:
            @wraps(func)
            def wrapper(*args, **kwargs):
                start = len(self._maps)
                try:
                    return func(*args, **kwargs)
                finally:
                    while len(self._maps) > start:
                        self.pop()
            return wrapper

    def __repr__(self):
        return '%s(%r)' % (type(self).__name__, self._maps)


###############################################################################
# Stack of mappings.
###############################################################################

class MapStack(Mapping):
    # pylint: disable=missing-docstring
    def __init__(self, maps=()):
        self._maps = list(maps) or [{}]

    def push(self):
        # pylint: disable=missing-docstring
        self._maps.append({})

    def pull(self):
        # pylint: disable=missing-docstring
        _maps = self._maps
        mapping = _maps.pop()
        accumulator = _maps[-1]
        accumulator.update(mapping)

    def undo(self):
        # pylint: disable=missing-docstring
        return self._maps.pop()

    def __getitem__(self, key):
        for mapping in reversed(self._maps):
            if key in mapping:
                return mapping[key]
        raise KeyError(key)

    def __setitem__(self, key, value):
        self._maps[-1][key] = value

    def __delitem__(self, key):
        del self._maps[-1][key]

    def pop(self, key, default=None):
        # pylint: disable=missing-docstring
        return self._maps[-1].pop(key, default)

    def __iter__(self):
        return iter(set().union(*self._maps))

    def __len__(self):
        return len(set().union(*self._maps))

    def __repr__(self):
        return '%s(%r)' % (type(self).__name__, self._maps)

    def get(self, key, default=None):
        # pylint: disable=missing-docstring
        return self[key] if key in self else default

    def __contains__(self, key):
        return any(key in mapping for mapping in reversed(self._maps))

    def __bool__(self):
        return any(self._maps)

    def copy(self):
        # pylint: disable=missing-docstring
        return dict(self)

    def reset(self):
        # pylint: disable=missing-docstring
        del self._maps[1:]
        self._maps[0].clear()


###############################################################################
# Matcher objects put it all together.
###############################################################################

class Matcher:
    """Container for match function state with list of pattern cases.

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
    def __init__(self, cases=base_cases):
        self.cases = cases
        self.bound = Bounder()
        self.names = MapStack()

    def match(self, value, pattern):
        # pylint: disable=missing-docstring
        names = self.names
        try:
            self.visit(value, pattern)
        except Mismatch:
            return False
        else:
            self.bound.push(names.copy())
        finally:
            names.reset()
        return True

    def visit(self, value, pattern):
        # pylint: disable=missing-docstring
        for name, predicate, action in self.cases:
            if predicate(self, value, pattern):
                return action(self, value, pattern)
        raise Mismatch


matcher = Matcher()
match = matcher.match
bound = matcher.bound


###############################################################################
# Pattern Matching
###############################################################################

__all__ = [
    'Matcher', 'match',
    'Name', 'Binder', 'bind', 'Bounder', 'bound',
    'Like', 'like', 'like_errors',
    'literal_types',
    'Anyone', 'anyone',
    'Pattern', 'Exclude', 'exclude', 'Either', 'either', 'Group', 'group',
    'Repeat', 'repeat', 'maybe', 'anything', 'something', 'padding',
]

__title__ = 'patternmatching'
__version__ = '3.0.1'
__build__ = 0x030001
__author__ = 'Grant Jenks'
__license__ = 'Apache 2.0'
__copyright__ = '2015-2019, Grant Jenks'
