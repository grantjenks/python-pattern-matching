Python Pattern Matching Reference
=================================

.. todo::

   autodoc api


Future Work
-----------

* Rather than adding `when` clause, just use `and`
  match(value, (bind.first, bind.second)) and bound.first < bound.second
* Should ``anyof(*patterns)`` be added?
  * "match(value, anyof('foo', 'bar'))"
  * Should the short-form of this just override any.__call__?
* Should ``allof(*patterns)`` be added?
  * "match(value, allof((0, _, _), (_, _, 1)))"
  * "match(value, (allof(anyof('grant', 'shannon'), bind.name), bind.name))"
* todo: bind.many

.. code-block:: python
   :linenos:

   class Many(object):
       def __init__(self, name, count=slice(None), values=(Anything,)):
           self.count = count
           self.values = values
           self.name = name
       def __getitem__(self, index):
           """Index may be any of:
           name
           twople ~ (name, slice)
           threeple ~ (name, slice, value-spec)
           """
           # todo

   many = Many()

* Many should have special significance in _sequence_rule which permits
  binding to multiple values.
* To be really powerful, this should support backtracking in the style of
  regular expressions.
* Maybe the third argument to slice could be True / False to indicate greedy
  or non-greedy matching.
* If second argument is a tuple, does that work like a character class and
  match any of the stated objects? How then to match a tuple? Put it in
  another tuple!
* This is close to supporting the full power of regular languages. If it were
  possible to `or` expressions (as done with `(A|B)`) then it would be
  feature-complete.
  Actually, that's possible with:

.. code-block:: python

   bind.many(1, (0, 1), 'zeroorone')

* But could you put a `bind.many` within a `bind.many` like:

.. code-block:: python

   bind.many(1, (bind.many(:, int), bind.many(:, float)), 'intsorfloats')

* And does that recurse? So you could have bind.many nested three times over?
  That sounds pretty difficult to achieve. How does naming of the nested
  nested groups sound? Lol, Python's regex package has this same difficulty.
  It's hard to imagine why anyone would create such complex data structure
  queries and want to express them in this way.

* Why not instead map patterns to letters and do traditional regex-matching?

* Support ellipsis-like syntax to match anything in the rest of the list or
  tuple.

* Match ``set`` expression?

* Add "when" clause like match(expr, when(predicate))

* Add ``or``/``and`` pattern-matching

* Match ``dict`` expression?

* Match regex?

* API for matching: __match__ and Matcher object for state
* Method of binding values to names
* Algorithm for patterns (generic regex)
* New match rule for "types"

* Add __match__ predicate and refactor cases.
* I wonder, can Pattern cases be refactored? Maybe "visit" should allow case
  action generators? isinstance(result, types.GeneratorType)
* Add Start and End to patterns.
* Add Set predicate and action?
  def set_predicate(matcher, value, pattern):
      return isinstance(pattern, Set)

  def set_action(matcher, value, pattern):
      value_sequence = tuple(value)
      for permutation in itertools.permutations(pattern):
          try:
              matcher.names.push()
              matcher.visit(value_sequence, permutation)
              matcher.names.pull()
              return
          except Mismatch:
              matcher.names.undo()
      else:
          raise Mismatch
* Add Mapping predicate and action?
* Improve docstrings with examples.

Tutorial
--------

.. todo::

   Examples.

import operator
from collections import Sequence

def make_operators(attrs):
    "Add operators to attributes dictionary."
    def method(function):
        return lambda self, that: BinaryOperator(self, function, that)
    def rmethod(function):
        return lambda self, that: BinaryOperator(that, function, self)
    for term in ['add', 'sub', 'mul', 'div']:
        function = getattr(operator, term)
        attrs['__%s__' % term] = method(function)
        attrs['__r%s__' % term] = rmethod(function)

class MetaTypeOperators(type):
    "Metaclass to add operators to type of types."
    def __new__(cls, name, base, attrs):
        make_operators(attrs)
        return super(MetaTypeOperators, cls).__new__(cls, name, base, attrs)

class MetaOperators(type):
    "Metaclass to add operators to types."
    __metaclass__ = MetaTypeOperators
    def __new__(cls, name, base, attrs):
        make_operators(attrs)
        return super(MetaOperators, cls).__new__(cls, name, base, attrs)
    def __repr__(self):
        return self.__name__

class Record(object):
    __metaclass__ = MetaOperators
    __slots__ = ()
    def __init__(self, *args):
        assert len(self.__slots__) == len(args)
        for field, value in zip(self.__slots__, args):
            setattr(self, field, value)
    def __getitem__(self, index):
        return getattr(self, self.__slots__[index])
    def __len__(self):
        return len(self.__slots__)
    def __eq__(self, that):
        if not isinstance(that, type(self)):
            return NotImplemented
        return all(item == iota for item, iota in zip(self, that))
    def __repr__(self):
        args = ', '.join(repr(item) for item in self)
        return '%s(%s)' % (type(self).__name__, args)
    # pickle support
    def __getstate__(self):
        return tuple(self)
    def __setstate__(self, state):
        self.__init__(*state)

Sequence.register(Record)

class BinaryOperator(Record):
    __slots__ = 'left', 'operator', 'right'

class Constant(Record):
    __slots__ = 'value',

class Variable(Record):
    __slots__ = 'name',

class Term(Record):
    __slots__ = 'value',
    def __match__(self, matcher, value):
        return matcher.visit(value, self.value)

zero = Constant(0)
one = Constant(1)
x = Variable('x')

from patternmatching import *

assert match(zero + one, Constant + Constant)
assert match(zero * Variable, zero * anyone)

alpha = Term(bind.alpha)

assert match(zero + zero, alpha + alpha)

TODO
----

- Should this module just be a function like:

::

    def bind(object, expression):
        """Attempt to bind object to expression.
        Expression may contain `bind.name`-style attributes which will bind the
        `name` in the callers context.
        """
        pass # todo

  What if just returned a mapping with the bindings and something
  like bind.result was available to capture the latest expression.
  For nested calls, bind.results could be a stack. Then the `like` function
  call could just return a Like object which `bind` recognized specially.
  Alternately `bind.results` could work using `with` statement to create
  the nested scope.

::

    if bind(r'<a href="(.*)">', text):
        match = bind.result
        print match.groups(1)
    elif bind([bind.name, 0], [5, 0]):
        pass

  Change signature to `bind(object, pattern)` and make a Pattern object. If
  the second argument is not a pattern object, then it is made into one
  (if necessary). Pattern objects should support `__contains__`.

  `bind` could also be a decorator in the style of oh-so-many multi-dispatch
  style pattern matchers.

  To bind anything, use bind.any or bind.__ as a place-filler that does not
  actually bind to values.

- Add like(...) function-call-like thing and support the following:
  like(type(obj)) check isinstance
  like('string') checks regex
  like(... callable ...) applies callable, binds truthy
- Also make `like` composable with `and` and `or`
- Add `when` support somehow and somewhere
- Add __ (two dunders) for place-holder
- Add match(..., fall_through=False) to prevent fall_through
- Use bind.name rather than quote(name)
- Improve debug-ability: write source to temporary file and modify code object
  accordingly. Change co_filename and co_firstlineno to temporary file?
- Support/test Python 2.6, Python 3 and PyPy 2 / 3
- Good paper worth referencing on patterns in Thorn:
  http://hirzels.com/martin/papers/dls12-thorn-patterns.pdf
- Support ellipsis-like syntax to match anything in the rest of the list or
  tuple. Consider using ``quote(*args)`` to mean zero or more elements. Elements
  are bound to args:

::

    match [1, 2, 3, 4]:
        like [1, 2, quote(*args)]:
            print 'args == [3, 4]'

- Match ``set`` expression. Only allow one ``quote`` variable. If present the
  quoted variable must come last.

::

    with match({3, 1, 4, 2}):
        with {1, 2, 4, quote(value)}:
            print 'value == 3'
        with {3, 4, quote(*args)}:
            print 'args = {1, 2}'

- Add "when" clause like:

::

    with match(list_item):
        with like([first, second], first < second):
            print 'ascending'
        with like([first, second], first > second):
            print 'descending'

- Add ``or``/``and`` pattern-matching like:

::

    with match(value):
        with [alpha] or [alpha, beta]:
            pass
        with [1, _, _] and [_, _, 2]:
            pass

- Match ``dict`` expression?
- Match regexp?

Future?
-------

- Provide more generic macro-expansion facilities. Consider if this module
  could instead be written as the following:

::

    def assign(var, value, _globals, _locals):
        exec '{var} = value'.format(var) in _globals, _locals

    @patternmatching.macro
    def match(expr, statements):
        """with match(expr): ... expansion
        with match(value / 5):
            ... statements ...
        ->
        patternmatching.store['temp0'] = value / 5
        try:
            ... statements ...
        except patternmatching.PatternmatchingBreak:
            pass
        """
        symbol[temp] = expand[expr]
        try:
            expand[statements]
        except patternmatching.PatternMatchingBreak:
            pass

    @patternmatching.macro
    def like(expr, statements):
        """with like(expr): ... expansion
        with like(3 + value):
            ... statements ...
        ->
        patternmatching.store['temp1'] = patternmatching.bind(expr, patternmatching.store['temp0'], globals(), locals())
        if patternmatching.store['temp1']:
            for var in patternmatching.store['temp1'][1]:
                assign(var, patternmatching.store['temp1'][1][var], globals(), locals())
            ... statements ...
            raise patternmatching.PatternmatchingBreak
        """
        symbol[result] = patternmatching.bind(expr, symbol[match.temp], globals(), locals())
        if symbol[result]:
            for var in symbol[result][1]:
                assign(var, symbol[result][1][var], globals(), locals())
            expand[statements]
            raise patternmatching.PatternmatchingBreak

    @patternmatching.expand(match, like)
    def test():
        with match('hello' + ' world'):
            with like(1):
                print 'fail'
            with like(False):
                print 'fail'
            with like('hello world'):
                print 'succeed'
            with like(_):
                print 'fail'

I'm not convinced this is better. But it's interesting. I think you could do
nearly this in ``macropy`` if you were willing to organize your code for the
import hook to work.
