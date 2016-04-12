"""Regular Expression Matching

https://github.com/VerbalExpressions/JSVerbalExpressions/blob/master/VerbalExpressions.js
Boost regular expressions

\d - digit (allow negation for non-digit)
\s - whitespace, blank (allow negation for non-whitespace)
\w - letter [a-zA-Z0-9_] (allow negation for non-word character)
r'\t' - tab
' ' - space

.* - anything
.+ - something
r'(?:\r\n|\r|\n)' - newline, breakline
[1-9] - nonzero
[a-zA-Z0-9] - alnum
[a-zA-Z] - alpha
[a-z] - lower
[A-Z] - upper

Examples:

'http' + maybe('s') + '://' + exclude(' ') * repeat
either('0', maybe('-') + nonzero + digit * repeat)
'<' + whitespace * repeat + exclude(whitespace) * repeat(greedy=False) + repeat(whitespace) + '>'

# Todo

* Support "find" rather "match" with:
  `anyone * re.repeat(greedy=False) + ...`
* Support "$" or `end` with:
  ... + anyone * re.repeat * re.group('tail') and len(bound.tail) == 0
* Use uppercase variants / call as in-fix notation.
* Use lowercase variants / multiply as post-fix notation.
* Support optimizing using `re.match` when possible.

"""

from collections import namedtuple, Sequence
from functools import partial

infinity = float('inf')


class Pattern(Sequence):
    def __init__(self, iterable=()):
        is_tuple = isinstance(iterable, tuple)
        self._pattern = iterable if is_tuple else tuple(iterable)

    def __getitem__(self, index):
        return self._pattern[index]

    def __len__(self):
        return len(self._pattern)

    def __add__(self, that):
        if isinstance(that, tuple):
            pass
        elif isinstance(that, Sequence):
            that = tuple(that)
        else:
            that = (that,)
        return Pattern(self._pattern + that)

    def __radd__(self, that):
        if isinstance(that, tuple):
            pass
        elif isinstance(that, Sequence):
            that = tuple(that)
        else:
            that = (that,)
        return Pattern(that + self._pattern)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, tuple(self))

    __str__ = __repr__


class SequenceMixin(Sequence):
    def __getitem__(self, index):
        if index == 0:
            return self
        else:
            raise IndexError

    def __len__(self):
        return 1


class PatternMixin(SequenceMixin):
    def __add__(self, that):
        return Pattern(self) + that

    def __radd__(self, that):
        return that + Pattern(self)


class Anyone(PatternMixin):
    # todo: move anyone to funcs.py
    def __repr__(self):
        return 'anyone'

    __str__ = __repr__

anyone = Anyone()


class Repeat(PatternMixin):
    def __init__(self, pattern=(), min=0, max=infinity, greedy=True):
        self._pattern = pattern
        self._min = min
        self._max = max
        self._greedy = greedy

    @property
    def pattern(self):
        return self._pattern

    @property
    def min(self):
        return self._min

    @property
    def max(self):
        return self._max

    @property
    def greedy(self):
        return self._greedy

    def __call__(self, min=0, max=infinity, greedy=True, pattern=()):
        return type(self)(pattern=pattern, min=min, max=max, greedy=greedy)

    def __rmul__(self, that):
        if not isinstance(that, Sequence):
            that = (that,)
        return self(self._min, self._max, self._greedy, that)

    def __mul__(self, that):
        return that.__rmul__(self)

    def __repr__(self):
        type_name = type(self).__name__
        parts = (type_name, self._pattern, self._min, self._max, self._greedy)
        return '%s(%r, %r, %r, %r)' % parts

    __str__ = __repr__


class Group(PatternMixin):
    def __init__(self, pattern=(), name=''):
        self._pattern = pattern
        self._name = name

    @property
    def pattern(self):
        return self._pattern

    @property
    def name(self):
        return self._name

    def __call__(self, name='', pattern=()):
        return type(self)(pattern=pattern, name=name)

    def __rmul__(self, that):
        if not isinstance(that, Sequence):
            that = (that,)
        return self(self.name, that)

    def __mul__(self, that):
        return that.__rmul__(self)

    def __repr__(self):
        type_name = type(self).__name__
        parts = (type_name, self._pattern, self._name)
        return '%s(%r, %r)' % parts

    __str__ = __repr__

group = Group()


class Options(PatternMixin):
    def __init__(self, *options):
        self._options = options

    @property
    def options(self):
        return self._options

    def __call__(self, options=()):
        return type(self)(*options)

    def __rmul__(self, that):
        if not isinstance(that, Sequence):
            that = (that,)
        return self(that)

    def __mul__(self, that):
        return that.__rmul__(self)

    def __repr__(self):
        type_name = type(self).__name__
        return '%s(%r)' % (type_name, self._options)

    __str__ = __repr__


class Either(Options):
    pass

either = Either()


class Exclude(Options):
    pass

exclude = Exclude()


repeat = Repeat()
maybe = repeat(max=1)
anything = anyone * repeat
something = anyone * repeat(min=1)
start = anyone * repeat(greedy=False)
end = anyone * repeat * group('end')
NONE = object()

def match(pattern, sequence):
    groups = {}
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
                        prev = groups.pop(item.name, NONE)
                        groups[item.name] = sequence[offset:end]

                    for stop in visit(pattern, index + 1, end, 0):
                        yield stop

                    if item.name and prev is not NONE:
                        groups[item.name] = prev

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
                # todo: could we use funcs.match rather than testing inequality?
                # todo: merge this with the `sequences` case in funcs.py
                if offset >= len_sequence:
                    return
                elif isinstance(item, Anyone):
                    pass
                elif item == sequence[offset]:
                    pass
                else:
                    return

            index += 1
            offset += 1

            if index == len_pattern:
                yield offset
                return

    for end in visit(pattern, 0, 0, 0):
        groups['_'] = sequence[:end]
        return groups
