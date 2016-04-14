"""Regular Expression Matching

# Todo

* Support "find" rather "match" with:
  `re.padding + ...`
* Support "$" or `end` with:
  ... + anyone * re.repeat * re.group('tail') and len(bound.tail) == 0
* Use uppercase variants / call as in-fix notation.
* Use lowercase variants / multiply as post-fix notation.

"""

from collections import namedtuple, Sequence

infinity = float('inf')


class Details(Sequence):
    def __eq__(self, that):
        return self._details == that._details

    def __ne__(self, that):
        return self._details != that._details

    def __hash__(self):
        return hash(self._details)


class Pattern(Details):
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


class Anyone(PatternMixin):
    # todo: move anyone to funcs.py
    def __repr__(self):
        return 'anyone'

    __str__ = __repr__

anyone = Anyone()


_Repeat = namedtuple('Repeat', 'pattern min max greedy')

class Repeat(PatternMixin):
    def __init__(self, pattern=(), min=0, max=infinity, greedy=True):
        self._details = _Repeat(pattern, min, max, greedy)

    def __call__(self, min=0, max=infinity, greedy=True, pattern=()):
        return type(self)(pattern, min, max, greedy)


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


repeat = Repeat()
maybe = repeat(max=1)
anything = anyone * repeat
something = anyone * repeat(min=1)
padding = anyone * repeat(greedy=False)


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
