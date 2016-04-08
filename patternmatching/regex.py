"""Regular Expression Matching

https://github.com/VerbalExpressions/JSVerbalExpressions/blob/master/VerbalExpressions.js
Boost regular expressions

. - anyone
r'^' - start
r'$' - end

"*" - zero_or_more (default greedy)
"+" - one_or_more (default greedy)
"?" - zero_or_one (default greedy)
"{m}" - exactly m copies
"{m,n}" - exactly range(m, n+1) copies
"{m,n}?" - exactly range(m, n+1) copies (not-greedy)
=>
repeat(pattern, min=0, max=None, greedy=True)

group(name=None)

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

[...] - subset
[^...] - exclude

| - either

Examples:

'http' + maybe('s') + '://' + exclude(' ') * repeat
either('0', maybe('-') + nonzero + digit * repeat)
'<' + whitespace * repeat + exclude(whitespace) * repeat(greedy=False) + repeat(whitespace) + '>'

"""

from collections import namedtuple
from functools import partial


class _AddMixin(object):
    def __add__(self, that):
        return Pattern([self]) + that
    def __radd__(self, that):
        return that + Pattern([self])


# todo: move anyone to funcs.py

class Anyone(_AddMixin):
    def __str__(self):
        return 'Anyone'
    def __repr__(self):
        return 'Anyone()'

anyone = Anyone()

_Repeat = namedtuple('Repeat', 'min max greedy pattern')

infinity = float('inf')

class Repeat(_AddMixin, _Repeat):
    def __call__(self, min=0, max=infinity, greedy=True, pattern=None):
        return type(self)(min=min, max=max, greedy=greedy, pattern=pattern)
    def __rmul__(self, that):
        if isinstance(that, Anyone):
            that = (that,)
        return self(self.min, self.max, self.greedy, that)

repeat = Repeat(0, infinity, True, None)
maybe = repeat(min=0, max=1)

# todo: add checks so that patterns are not None and not zero-length

_Group = namedtuple('Group', 'pattern name')

class Group(_AddMixin, _Group):
    # todo: Matching this should use `bind`
    pass

def group(pattern, name=None):
    return Group(pattern=pattern, name=name)

_Either = namedtuple('Either', 'options')

class Either(_AddMixin, _Either):
    pass

def either(*options):
    return Either(options)

_Exclude = namedtuple('Exclude', 'options')

class Exclude(_AddMixin, _Exclude):
    pass

def exclude(*options):
    return Exclude(options)


def match(pattern, sequence):
    if isinstance(pattern, (Repeat, Group, Either, Exclude, Anyone)):
        pattern = Pattern((pattern,))

    groups = {}

    for end in _match(pattern, sequence, groups=groups):
        groups['_'] = sequence[:end]
        return groups

def _match(pattern, sequence, index=0, offset=0, count=0, groups={}):
    len_pattern = len(pattern)
    len_sequence = len(sequence)

    if index == len_pattern:
        yield offset
        return

    if offset == len_sequence:
        return

    while True:
        item = pattern[index]

        if isinstance(item, Repeat):
            if count > item.max:
                return

            if item.greedy:
                for end in _match(item.pattern, sequence, 0, offset):
                    for stop in _match(pattern, sequence, index, end, count + 1):
                        yield stop

                if count >= item.min:
                    for stop in _match(pattern, sequence, index + 1, offset):
                        yield stop
            else:
                if count >= item.min:
                    for stop in _match(pattern, sequence, index + 1, offset):
                        yield stop

                for end in _match(item.pattern, sequence, 0, offset):
                    for stop in _match(pattern, sequence, index, end, count + 1):
                        yield stop

            return

        elif isinstance(item, Group):
            for end in _match(item.pattern, sequence, 0, offset):
                # todo: if item.name is None then don't store in groups
                groups[item.name] = sequence[offset:end]
                for stop in _match(pattern, sequence, index + 1, end):
                    yield stop

            return

        elif isinstance(item, Either):
            for option in item.options:
                for end in _match(option, sequence, 0, offset):
                    for stop in _match(pattern, sequence, index + 1, end):
                        yield stop

            return

        elif isinstance(item, Exclude):
            for option in item.options:
                for end in _match(option, sequence, 0, offset):
                    return

        elif isinstance(item, Anyone):
            pass

        else:
            # todo: could we use funcs.match rather than testing inequality?
            # todo: merge this with the `sequences` case in funcs.py
            if item != sequence[offset]:
                return

        index += 1
        offset += 1

        if index >= len_pattern or offset >= len_sequence:
            break

    if index == len_pattern:
        yield offset


class Pattern(tuple):
    def __add__(self, that):
        if isinstance(that, _AddMixin):
            that = (that,)
        elif not isinstance(that, Pattern):
            that = tuple(that)
        return Pattern(tuple.__add__(self, that))

    def __radd__(self, that):
        if isinstance(that, _AddMixin):
            that = (that,)
        elif not isinstance(that, Pattern):
            that = tuple(that)
        return Pattern(tuple.__add__(that, self))

    def match(self, that):
        # todo: how to support start and end?
        #     - default start=True and end=True
        #     - workaround: anything * repeat + ... + anything * repeat
        # todo: use re.match if possible

        pos = loc = 0


    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, tuple(self))

    __str__ = __repr__

anything = anyone * repeat
something = anyone * repeat(min=1, max=None)
