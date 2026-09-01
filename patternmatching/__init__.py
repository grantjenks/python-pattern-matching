"""Python Pattern Matching

Python pattern matching library.

"""

import functools
import inspect
import re
from collections.abc import Mapping, Sequence
from contextlib import ContextDecorator
from contextvars import ContextVar
from types import MappingProxyType

infinity = float('inf')


class _Record:
    """Mutable "named tuple"-like base class."""

    __slots__ = ()

    def __init__(self, *args):
        assert len(self.__slots__) == len(args)
        for field, value in zip(self.__slots__, args):
            setattr(self, field, value)

    def __getitem__(self, index):
        return getattr(self, self.__slots__[index])

    def __eq__(self, that):
        if not isinstance(that, type(self)):
            return NotImplemented
        if self.__slots__ != that.__slots__:
            return False
        return all(item == iota for item, iota in zip(self, that))

    def __repr__(self):
        args = ', '.join(repr(item) for item in self)
        return '%s(%s)' % (type(self).__name__, args)

    def __getstate__(self):
        return tuple(self)

    def __setstate__(self, state):
        self.__init__(*state)


class Case(_Record):
    """Three-ple of `name`, `predicate`, and `action`.

    `Matcher` objects successively try a sequence of `Case` predicates. When a
    match is found, the `Case` action is applied.

    """

    __slots__ = 'name', 'predicate', 'action'


default_cases = []


class Mismatch(Exception):
    "Raised by `action` functions of `Case` records to abort on mismatch."


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


default_cases.append(Case('__match__', match_predicate, match_action))


###############################################################################
# Match Case: patterns
###############################################################################


class APattern(Sequence):
    """Abstract base class extending `Sequence` to define equality and hashing.

    Defines one slot, `_details`, for comparison and hashing.

    Used by `Pattern` and `PatternMixin` types.

    """

    __slots__ = ('_details',)

    def __eq__(self, that):
        return self._details == that._details

    def __ne__(self, that):
        return self._details != that._details

    def __hash__(self):
        return hash(self._details)

    def __match__(self, matcher, value):
        return self._match(matcher, value, full=False)

    def _match(self, matcher, value, *, full):
        """Match `pattern` to `value` with `Pattern` semantics.

        The `Pattern` type is used to define semantics like regular expressions.

        >>> bool(match([0, 1, 2], [0, 1] + anyone))
        True
        >>> bool(match([0, 0, 0, 0], 0 * repeat))
        True
        >>> bool(match('blue', either('red', 'blue', 'yellow')))
        True
        >>> bool(match([2, 4, 6], exclude(like(lambda num: num % 2)) * repeat(min=3)))
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
            if not full or end == len_value:
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
    >>> bool(match('blah', Anyone()))
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


class _Repeat(_Record):
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
        self._details = _Repeat(pattern, min, max, greedy)

    def __rmul__(self, that):
        return type(self)(sequence(that), *tuple(self._details)[1:])

    def __call__(self, min=0, max=infinity, greedy=True, pattern=()):
        return type(self)(pattern, min, max, greedy)


repeat = Repeat()
maybe = repeat(max=1)
anything = anyone * repeat
something = anyone * repeat(min=1)
padding = anyone * repeat(greedy=False)


###############################################################################
# Match Case: groups
###############################################################################


class _Group(_Record):
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


class _Options(_Record):
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


either = Either()


class Exclude(Options):
    "Pattern specifying that none of options may match."


exclude = Exclude()


###############################################################################
# Match Case: names
###############################################################################


class Name(_Record):
    """Name objects simply wrap a `value` to be used as a name.

    >>> bool(match([1, 2, 3], [Name('head'), 2, 3]))
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

like_errors = (
    AttributeError,
    LookupError,
    NotImplementedError,
    TypeError,
    ValueError,
)


class Like(_Record):
    __slots__ = 'pattern', 'name'

    def __match__(self, matcher, value):
        """Apply `pattern` to `value` and store result in `matcher`.

        Given `pattern` is expected as `Like` instance and deconstructed by
        attribute into `pattern` and `name`.

        When `pattern` is text then it is used as a regular expression.

        When `name` is None then the result is not stored in `matcher.names`.

        Raises `Mismatch` if callable raises exception in `like_errors` or
        result is falsy.

        >>> bool(match('abcdef', like('abc.*')))
        True
        >>> bool(match(123, like(lambda num: num % 2 == 0)))
        False

        """
        pattern = self.pattern
        name = self.name

        if isinstance(pattern, (str, bytes)):
            if not isinstance(value, type(pattern)):
                raise Mismatch
            func = functools.partial(re.match, pattern)
        elif isinstance(pattern, re.Pattern):
            func = pattern.match
        else:
            func = pattern

        try:
            result = func(value)
        except like_errors:
            raise Mismatch from None

        if not result:
            raise Mismatch from None

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
# Match Case: records and explicit equality
###############################################################################


class RecordPattern:
    """Pattern matching selected attributes of an object.

    Positional patterns use the class's ``__match_args__`` names. Keyword
    patterns name attributes directly, matching Python class-pattern behavior.

    """

    __slots__ = 'cls', 'attributes', 'positional_count'

    def __init__(self, cls, patterns, attributes):
        if not isinstance(cls, type):
            raise TypeError('record type must be a class')

        match_args = getattr(cls, '__match_args__', ())
        if not isinstance(match_args, tuple) or not all(
            isinstance(name, str) for name in match_args
        ):
            raise TypeError('__match_args__ must be a tuple of strings')
        if len(patterns) > len(match_args):
            raise TypeError(
                '%s accepts %d positional record pattern%s (%d given)'
                % (
                    cls.__name__,
                    len(match_args),
                    '' if len(match_args) == 1 else 's',
                    len(patterns),
                )
            )

        pairs = list(zip(match_args, patterns))
        positional_names = {name for name, _ in pairs}
        duplicates = positional_names.intersection(attributes)
        if duplicates:
            name = sorted(duplicates)[0]
            raise TypeError('record attribute %r specified more than once' % name)
        pairs.extend(attributes.items())

        self.cls = cls
        self.attributes = tuple(pairs)
        self.positional_count = len(patterns)

    def __match__(self, matcher, value):
        if not isinstance(value, self.cls):
            raise Mismatch

        names = matcher.names
        names.push()
        try:
            for name, pattern in self.attributes:
                try:
                    attribute = getattr(value, name)
                except AttributeError:
                    raise Mismatch from None
                matcher.visit(attribute, pattern)
        except BaseException:
            names.undo()
            raise
        else:
            names.pull()

    def __repr__(self):
        args = [self.cls.__name__]
        for index, (name, pattern) in enumerate(self.attributes):
            token = pattern.__name__ if isinstance(pattern, type) else repr(pattern)
            if index < self.positional_count:
                args.append(token)
            else:
                args.append('%s=%s' % (name, token))
        return 'record(%s)' % ', '.join(args)


def record(cls, *patterns, **attributes):
    """Return a pattern matching an object's type and selected attributes."""
    return RecordPattern(cls, patterns, attributes)


class Equal:
    """Pattern forcing ordinary equality rather than structural matching."""

    __slots__ = ('value',)

    def __init__(self, value):
        self.value = value

    def __match__(self, matcher, value):
        try:
            matches = bool(value == self.value)
        except Exception:
            matches = False
        if not matches:
            raise Mismatch

    def __repr__(self):
        return 'equal(%r)' % (self.value,)


def equal(value):
    """Return a pattern matching `value` by ordinary equality."""
    return Equal(value)


###############################################################################
# Match Case: types
###############################################################################


def type_predicate(matcher, value, pattern):
    "Return True if `pattern` is an instance of `type`."
    return isinstance(pattern, type)


def type_action(matcher, value, pattern):
    """Match `value` as subclass or instance of `pattern`.

    >>> bool(match(1, int))
    True
    >>> bool(match(True, bool))
    True
    >>> bool(match(True, int))
    True
    >>> bool(match(bool, int))
    True
    >>> bool(match(0.0, int))
    False
    >>> bool(match(float, int))
    False

    """
    if isinstance(value, type) and issubclass(value, pattern):
        return value
    if isinstance(value, pattern):
        return value
    raise Mismatch


default_cases.append(Case('types', type_predicate, type_action))


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

    >>> bool(match(1, 1))
    True
    >>> bool(match('abc', 'abc'))
    True
    >>> bool(match(1, 1.0))
    True
    >>> bool(match(1, True))
    True

    """
    if value == pattern:
        return value
    raise Mismatch


default_cases.append(Case('literals', literal_predicate, literal_action))


###############################################################################
# Match Case: mappings
###############################################################################


def mapping_predicate(matcher, value, pattern):
    "Return True when both value and pattern are mappings."
    return isinstance(pattern, Mapping) and isinstance(value, Mapping)


def mapping_action(matcher, value, pattern):
    """Recursively match the keys present in a mapping pattern.

    Additional keys in the value are ignored. Use `equal(mapping)` to require
    ordinary mapping equality.

    """
    names = matcher.names
    names.push()
    try:
        for key, item_pattern in pattern.items():
            try:
                item = value[key]
            except KeyError:
                raise Mismatch from None
            matcher.visit(item, item_pattern)
    except BaseException:
        names.undo()
        raise
    else:
        names.pull()
    return value


default_cases.append(Case('mappings', mapping_predicate, mapping_action))


###############################################################################
# Match Case: equality
###############################################################################


def equality_predicate(matcher, value, pattern):
    "Return True if `value` equals `pattern`."
    try:
        return bool(value == pattern)
    except Exception:
        return False


def equality_action(matcher, value, pattern):
    """Match `value` as equal to `pattern`.

    >>> identity = lambda value: value
    >>> bool(match(identity, identity))
    True
    >>> bool(match('abc', 'abc'))
    True
    >>> bool(match(1, 1.0))
    True
    >>> bool(match(1, True))
    True

    """
    return value


default_cases.append(Case('equality', equality_predicate, equality_action))


###############################################################################
# Match Case: sequences
###############################################################################


def sequence_predicate(matcher, value, pattern):
    """Return True if `pattern` is instance of Sequence and `value` is instance of
    type of `pattern`.

    """
    return isinstance(pattern, Sequence) and isinstance(value, type(pattern))


def sequence_action(matcher, value, pattern):
    """Iteratively match items of `pattern` with `value` in sequence.

    Return tuple of results of matches.

    >>> bool(match([0, 'abc', {}], [int, str, dict]))
    True
    >>> bool(match((0, True, bool), (0.0, 1, int)))
    True
    >>> bool(match([], ()))
    False

    """
    if len(value) != len(pattern):
        raise Mismatch

    pairs = zip(value, pattern)
    return tuple(matcher.visit(item, iota) for item, iota in pairs)


default_cases.append(Case('sequences', sequence_predicate, sequence_action))


###############################################################################
# Native regular-expression backend for string and bytes sequence patterns.
###############################################################################


class _NativeUnsupported(Exception):
    pass


class _NativeFragment:
    __slots__ = 'source', 'nullable'

    def __init__(self, source, nullable):
        self.source = source
        self.nullable = nullable


class _NativePlan:
    __slots__ = 'regex', 'bindings'

    def __init__(self, regex, bindings):
        self.regex = regex
        self.bindings = tuple(bindings)

    def apply(self, matcher, value, *, full):
        result = self.regex.fullmatch(value) if full else self.regex.match(value)
        if result is None:
            raise Mismatch

        for key, group_name, binding_type in self.bindings:
            start, end = result.span(group_name)
            if start < 0:
                continue
            if binding_type == 'item':
                bound_value = value[start]
            else:
                bound_value = value[start:end]
            name_store(matcher.names, key, bound_value)
        return value[: result.end()]


class _NativeCompiler:
    """Translate the semantics-preserving text subset to Python `re`."""

    def __init__(self, kind):
        self.kind = kind
        self.bindings = []
        self.binding_groups = {}

    def token(self, value):
        return value if self.kind is str else value.encode('ascii')

    def join(self, values):
        return ('' if self.kind is str else b'').join(values)

    def group(self, source):
        return self.token('(?:') + source + self.token(')')

    def compile(self, pattern):
        fragment = self.compile_sequence(pattern)
        return _NativePlan(re.compile(fragment.source), self.bindings)

    def compile_sequence(self, pattern, *, allow_bindings=True, under_repeat=False):
        if isinstance(pattern, self.kind):
            return _NativeFragment(re.escape(pattern), not pattern)

        if isinstance(pattern, PatternMixin):
            return self.compile_atom(
                pattern,
                allow_bindings=allow_bindings,
                under_repeat=under_repeat,
            )

        if not isinstance(pattern, Sequence):
            return self.compile_atom(
                pattern,
                allow_bindings=allow_bindings,
                under_repeat=under_repeat,
            )

        fragments = [
            self.compile_atom(
                item,
                allow_bindings=allow_bindings,
                under_repeat=under_repeat,
            )
            for item in pattern
        ]
        return _NativeFragment(
            self.join(fragment.source for fragment in fragments),
            all(fragment.nullable for fragment in fragments),
        )

    def compile_atom(self, pattern, *, allow_bindings, under_repeat):
        if isinstance(pattern, Anyone):
            return _NativeFragment(self.token('(?s:.)'), False)

        if isinstance(pattern, Repeat):
            repeated = self.compile_sequence(
                pattern.pattern,
                allow_bindings=allow_bindings,
                under_repeat=True,
            )
            if repeated.nullable:
                raise _NativeUnsupported
            quantifier = self.quantifier(pattern.min, pattern.max)
            if not pattern.greedy:
                quantifier += '?'
            source = self.group(repeated.source) + self.token(quantifier)
            return _NativeFragment(source, pattern.min == 0)

        if isinstance(pattern, Group):
            grouped = self.compile_sequence(
                pattern.pattern,
                allow_bindings=allow_bindings,
                under_repeat=under_repeat,
            )
            if pattern.name is None:
                return _NativeFragment(self.group(grouped.source), grouped.nullable)
            if not allow_bindings or under_repeat or pattern.name in self.binding_groups:
                raise _NativeUnsupported
            group_name = self.new_group(pattern.name, 'slice')
            source = (
                self.token('(?P<%s>' % group_name)
                + grouped.source
                + self.token(')')
            )
            return _NativeFragment(source, grouped.nullable)

        if isinstance(pattern, Either):
            options = [
                self.compile_sequence(option, allow_bindings=False)
                for option in pattern.options
            ]
            if not options:
                return _NativeFragment(self.token('(?!)'), False)
            source = self.token('(?:') + self.token('|').join(
                option.source for option in options
            ) + self.token(')')
            return _NativeFragment(source, any(option.nullable for option in options))

        if isinstance(pattern, Exclude):
            options = [
                self.compile_sequence(option, allow_bindings=False)
                for option in pattern.options
            ]
            if not options:
                return _NativeFragment(self.token('(?s:.)'), False)
            alternatives = self.token('|').join(option.source for option in options)
            assertion = self.token('(?!(?:') + alternatives + self.token('))')
            return _NativeFragment(assertion + self.token('(?s:.)'), False)

        if isinstance(pattern, Name):
            if not allow_bindings:
                raise _NativeUnsupported
            previous = self.binding_groups.get(pattern.value)
            if previous is not None:
                group_name, binding_type = previous
                if binding_type != 'item':
                    raise _NativeUnsupported
                return _NativeFragment(
                    self.token('(?P=%s)' % group_name),
                    False,
                )
            if under_repeat:
                raise _NativeUnsupported
            group_name = self.new_group(pattern.value, 'item')
            source = self.token('(?P<%s>(?s:.))' % group_name)
            return _NativeFragment(source, False)

        if isinstance(pattern, Equal):
            pattern = pattern.value

        if isinstance(pattern, type):
            if self.kind is str and pattern in (str, object):
                return _NativeFragment(self.token('(?s:.)'), False)
            if self.kind is bytes and pattern in (int, object):
                return _NativeFragment(self.token('(?s:.)'), False)
            raise _NativeUnsupported

        if self.kind is str and isinstance(pattern, str) and len(pattern) == 1:
            return _NativeFragment(re.escape(pattern), False)

        if self.kind is bytes and isinstance(pattern, int) and 0 <= pattern <= 255:
            return _NativeFragment(re.escape(bytes((pattern,))), False)

        raise _NativeUnsupported

    def new_group(self, key, binding_type):
        try:
            hash(key)
        except TypeError:
            raise _NativeUnsupported from None
        group_name = '_pm_%d' % len(self.bindings)
        self.bindings.append((key, group_name, binding_type))
        self.binding_groups[key] = (group_name, binding_type)
        return group_name

    @staticmethod
    def quantifier(minimum, maximum):
        if not isinstance(minimum, int) or minimum < 0:
            raise _NativeUnsupported
        if maximum != infinity and (
            not isinstance(maximum, int) or maximum < minimum
        ):
            raise _NativeUnsupported
        if minimum == 0 and maximum == infinity:
            return '*'
        if minimum == 1 and maximum == infinity:
            return '+'
        if minimum == 0 and maximum == 1:
            return '?'
        if maximum == infinity:
            return '{%d,}' % minimum
        if minimum == maximum:
            return '{%d}' % minimum
        return '{%d,%d}' % (minimum, maximum)


def _compile_native_uncached(pattern, kind):
    try:
        return _NativeCompiler(kind).compile(pattern)
    except (_NativeUnsupported, re.error, OverflowError):
        return None


@functools.lru_cache(maxsize=128)
def _compile_native_cached(pattern, kind):
    return _compile_native_uncached(pattern, kind)


_native_identity_cache = {}


def _compile_native(pattern, kind):
    try:
        return _compile_native_cached(pattern, kind)
    except TypeError:
        # Most compound patterns contain legacy unhashable record objects.
        # Cache those by identity while retaining the pattern itself so an id
        # cannot be reused for a different live object.
        key = id(pattern), kind
        cached = _native_identity_cache.get(key)
        if cached is not None and cached[0] is pattern:
            return cached[1]
        result = _compile_native_uncached(pattern, kind)
        _native_identity_cache[key] = pattern, result
        if len(_native_identity_cache) > 128:
            del _native_identity_cache[next(iter(_native_identity_cache))]
        return result


###############################################################################
# Successful matches and context-local binding history.
###############################################################################


class Match(Mapping):
    """Immutable bindings produced by a successful match.

    Successful matches are always truthy, including matches with no bindings.
    Bindings support both mapping and attribute access.

    >>> result = Match({'foo': 1})
    >>> result.foo
    1
    >>> result['foo']
    1
    >>> bool(Match())
    True

    """

    __slots__ = ('_bindings',)

    def __init__(self, bindings=()):
        self._bindings = MappingProxyType(dict(bindings))

    def __getattr__(self, attr):
        try:
            return self._bindings[attr]
        except KeyError:
            raise AttributeError(attr) from None

    def __getitem__(self, key):
        return self._bindings[key]

    def __iter__(self):
        return iter(self._bindings)

    def __len__(self):
        return len(self._bindings)

    def __bool__(self):
        return True

    def __eq__(self, that):
        if isinstance(that, Mapping):
            return dict(self) == dict(that)
        return NotImplemented

    def __repr__(self):
        return '%s(%r)' % (type(self).__name__, dict(self._bindings))


class _BoundScope(ContextDecorator):
    """Restore a Bounder's history when a dynamic scope exits."""

    def __init__(self, bounder):
        self.bounder = bounder
        self.tokens = []

    def __enter__(self):
        token = self.bounder._state.set(self.bounder._state.get())
        self.tokens.append(token)
        return self.bounder

    def __exit__(self, *exc):
        self.bounder._state.reset(self.tokens.pop())
        return False

    def _recreate_cm(self):
        return type(self)(self.bounder)

    def __call__(self, func):
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def inner(*args, **kwargs):
                with self._recreate_cm():
                    return await func(*args, **kwargs)

            return inner
        return super().__call__(func)


class Bounder:
    """Bounded, context-local history of successful `Match` objects.

    >>> history = Bounder([{'foo': 0}], limit=10)
    >>> history.foo
    0
    >>> history.push({'bar': 1})
    Match({'bar': 1})
    >>> history.pop()
    Match({'bar': 1})
    >>> history.foo
    0

    """

    def __init__(self, matches=(), *, limit=10):
        if limit is not None and (not isinstance(limit, int) or limit < 1):
            raise ValueError('limit must be a positive integer or None')
        self.limit = limit
        initial = tuple(
            item if isinstance(item, Match) else Match(item) for item in matches
        )
        if limit is not None:
            initial = initial[-limit:]
        self._state = ContextVar('patternmatching_bound', default=initial)

    def _current(self):
        try:
            return self._state.get()[-1]
        except IndexError:
            raise LookupError('no successful match is bound') from None

    def __getattr__(self, attr):
        try:
            return getattr(self._current(), attr)
        except (LookupError, AttributeError):
            raise AttributeError(attr) from None

    def __getitem__(self, key):
        try:
            return self._current()[key]
        except LookupError:
            raise KeyError(key) from None

    def __eq__(self, that):
        try:
            return self._current() == that
        except LookupError:
            return False

    def __ne__(self, that):
        return not self == that

    def __iter__(self):
        try:
            return iter(self._current())
        except LookupError:
            return iter(())

    def __len__(self):
        return len(self._state.get())

    def push(self, match):
        """Push a successful match, discarding the oldest at the limit."""
        if not isinstance(match, Match):
            match = Match(match)
        matches = self._state.get() + (match,)
        if self.limit is not None:
            matches = matches[-self.limit :]
        self._state.set(matches)
        return match

    def pop(self):
        """Pop and return the most recent match."""
        matches = self._state.get()
        if not matches:
            raise IndexError('pop from empty Bounder')
        self._state.set(matches[:-1])
        return matches[-1]

    def reset(self):
        """Clear all matches in the current execution context."""
        self._state.set(())

    def scope(self):
        """Return a context manager/decorator that restores prior history."""
        return _BoundScope(self)

    def __repr__(self):
        return '%s(%r, limit=%r)' % (
            type(self).__name__,
            list(self._state.get()),
            self.limit,
        )


###############################################################################
# Stack of mappings.
###############################################################################


class MapStack(Mapping):
    def __init__(self, maps=()):
        self._maps = list(maps) or [{}]

    def push(self):
        self._maps.append({})

    def pull(self):
        _maps = self._maps
        mapping = _maps.pop()
        accumulator = _maps[-1]
        accumulator.update(mapping)

    def undo(self):
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
        return self._maps[-1].pop(key, default)

    def __iter__(self):
        keys = {}
        for mapping in self._maps:
            keys.update((key, None) for key in mapping)
        return iter(keys)

    def __len__(self):
        return len(dict.fromkeys(key for mapping in self._maps for key in mapping))

    def __repr__(self):
        return '%s(%r)' % (type(self).__name__, self._maps)

    def get(self, key, default=None):
        return self[key] if key in self else default

    def __contains__(self, key):
        return any(key in mapping for mapping in reversed(self._maps))

    def __bool__(self):
        return any(self._maps)

    def copy(self):
        return dict(self)

    def reset(self):
        del self._maps[1:]
        self._maps[0].clear()


###############################################################################
# Matcher objects put it all together.
###############################################################################


class Matcher:
    """Container for match function state with list of pattern cases.

    >>> matcher = Matcher()
    >>> bool(matcher.match(None, None))
    True
    >>> bool(matcher.match(0, int))
    True
    >>> match = matcher.match
    >>> bool(match([1, 2, 3], [1, bind.middle, 3]))
    True
    >>> matcher.bound.middle
    2
    >>> bound = matcher.bound
    >>> bool(match([(1, 2, 3), 4, 5], [bind.any, 4, bind.tail]))
    True
    >>> bound.tail
    5

    """

    def __init__(self, cases=None, *, bound_limit=10, native=True):
        self.cases = default_cases if cases is None else cases
        self.bound = Bounder(limit=bound_limit)
        self.native = native and cases is None
        self._names = ContextVar('patternmatching_names', default=None)

    @property
    def names(self):
        names = self._names.get()
        if names is None:
            raise RuntimeError('no match is currently in progress')
        return names

    def match(self, value, pattern):
        """Match from the beginning and return `Match` or `None`."""
        return self._run(value, pattern, full=False)

    def fullmatch(self, value, pattern):
        """Match an entire generic sequence and return `Match` or `None`."""
        return self._run(value, pattern, full=True)

    def _run(self, value, pattern, *, full):
        names = MapStack()
        token = self._names.set(names)
        try:
            native_plan = None
            native_candidate = (
                self.native
                and isinstance(value, (str, bytes))
                and isinstance(pattern, APattern)
                and not isinstance(pattern, Anyone)
            )
            if native_candidate:
                kind = str if isinstance(value, str) else bytes
                native_plan = _compile_native(pattern, kind)

            if native_plan is not None:
                native_plan.apply(self, value, full=full)
            elif full and isinstance(pattern, APattern) and not isinstance(
                pattern, Anyone
            ):
                pattern._match(self, value, full=True)
            else:
                self.visit(value, pattern)
        except Mismatch:
            return None
        else:
            result = Match(names.copy())
            self.bound.push(result)
            return result
        finally:
            self._names.reset(token)

    def visit(self, value, pattern):
        for _, predicate, action in self.cases:
            if predicate(self, value, pattern):
                return action(self, value, pattern)
        raise Mismatch


matcher = Matcher()
match = matcher.match
fullmatch = matcher.fullmatch
bound = matcher.bound


###############################################################################
# Pattern Matching
###############################################################################

# fmt: off
__all__ = [
    'Matcher', 'Mismatch', 'Match', 'match', 'fullmatch',
    'Name', 'Binder', 'bind', 'Bounder', 'bound',
    'Like', 'like', 'like_errors',
    'RecordPattern', 'record', 'Equal', 'equal',
    'literal_types',
    'Anyone', 'anyone',
    'Pattern', 'Exclude', 'exclude', 'Either', 'either', 'Group', 'group',
    'Repeat', 'repeat', 'maybe', 'anything', 'something', 'padding',
]
# fmt: on

__title__ = 'patternmatching'
__version__ = '4.0.0'
__build__ = 0x040000
__author__ = 'Grant Jenks'
__license__ = 'Apache 2.0'
__copyright__ = '2015-2026, Grant Jenks'
