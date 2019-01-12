Python Pattern Matching
=======================

Python, I love you. But I'd like you to change. It's not you, it's me. Really.
See, you don't have pattern matching. But, that's not the root of it. Macros
are the root of it. You don't have macros but that's OK. Right now, I want
pattern matching. I know you offer me ``if``/``elif``/``else`` statements but I
need more. I'm going to abuse your functions. Guido, et al, I hope you can
forgive me. This will only hurt a little.

Python Pattern Matching is an Apache2 licensed Python module for pattern
matching like that found in functional programming languages. Most projects
that address Python pattern matching focus on syntax and simple cases. Operator
overloading is often used to change the semantics of operators to support
pattern matching. In other cases, function decorators are used to implement
multiple dispatch, sometimes known as function overloading. Each of these
syntaxes, operators, and decorators, is really more of a detail in the
application of pattern matching.

A lot of people have tried to make this work before. Somehow it didn't take. I
should probably call this yet-another-python-pattern-matching-module but
"yappmm" doesn't roll off the tongue. Other people have tried overloading
operators and changing codecs. This module started as a codec hack but those are
hard because they need an ecosystem of emacs-modes, vim-modes and the like to
really be convenient.

Python Pattern Matching focuses instead on the semantics of pattern matching in
Python. The dynamic duck-typing behavior in Python is distinct from the tagged
unions found in functional programming languages. Rather than trying to emulate
the behavior of functional pattern matching, this project attempts to implement
pattern matching that looks and feels native to Python. In doing so the
traditional function call is used as syntax. There are no import hooks, no
codecs, no AST transforms.

.. todo::

   Python ``match`` function example.

Finally, pythonic pattern matching! If you've experienced the feature before in
"functional" languages like Erlang, Haskell, Clojure, F#, OCaml, etc. then you
can guess at the semantics.

.. todo::

   Show the same code without ``patternmatching``.


Features
--------

- Pure-Python
- Fully Documented
- 100% Test Coverage
- Developed on Python 2.7
- Tested on CPython 2.6, 2.7, 3.2, 3.3, 3.4 and PyPy 2.5+, PyPy3 2.4+

Quickstart
----------

Installing PyPatt is simple with `pip <http://www.pip-installer.org/>`_::

  $ pip install pypatt

You can access documentation in the interpreter with Python's built-in help
function::

  >>> from pypatt import match, bind, bound, like
  >>> help(match)

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


Alternatives
------------

- https://github.com/lihaoyi/macropy
  - module import, but similar design
- https://github.com/Suor/patterns
  - decorator with funky syntax
  - Shared at Python Brazil 2013
- https://github.com/mariusae/match
  - http://monkey.org/~marius/pattern-matching-in-python.html
  - operator overloading
- http://blog.chadselph.com/adding-functional-style-pattern-matching-to-python.html
  - multi-methods
- http://svn.colorstudy.com/home/ianb/recipes/patmatch.py
  - multi-methods
- http://www.artima.com/weblogs/viewpost.jsp?thread=101605
  - the original multi-methods
- http://speak.codebunk.com/post/77084204957/pattern-matching-in-python
  - multi-methods supporting callables
- http://www.aclevername.com/projects/splarnektity/
  - not sure how it works but the syntax leaves a lot to be desired
- https://github.com/martinblech/pyfpm
  - multi-dispatch with string parsing
- https://github.com/jldupont/pyfnc
  - multi-dispatch
- http://www.pyret.org/
  - It's own language
- https://pypi.python.org/pypi/PEAK-Rules
  - generic multi-dispatch style for business rules
- http://home.in.tum.de/~bayerj/patternmatch.py
  - Pattern-object idea (no binding)
- https://github.com/admk/patmat
  - multi-dispatch style

Other Languages
---------------

- https://msdn.microsoft.com/en-us/library/dd547125.aspx F#
- https://doc.rust-lang.org/book/patterns.html Rust
- https://www.haskell.org/tutorial/patterns.html Haskell
- http://erlang.org/doc/reference_manual/expressions.html#pattern Erlang
- https://ocaml.org/learn/tutorials/data_types_and_matching.html Ocaml

Development
-----------

- Run ``tox``

Reference and Indices
---------------------

.. toctree::
   :maxdepth: 1

   funcs
   macro

* `PyPatt - Python Pattern Matching Documentation`_
* `PyPatt at PyPI`_
* `PyPatt at GitHub`_
* `PyPatt Issue Tracker`_
* :ref:`search`
* :ref:`genindex`

.. _`PyPatt - Python Pattern Matching Documentation`: http://www.grantjenks.com/docs/pypatt-python-pattern-matching/
.. _`PyPatt at PyPI`: https://pypi.python.org/pypi/pypatt/
.. _`PyPatt at GitHub`: https://github.com/grantjenks/pypatt_python_pattern_matching/
.. _`PyPatt Issue Tracker`: https://github.com/grantjenks/pypatt_python_pattern_matching/issues/

PyPatt License
--------------

.. include:: ../LICENSE

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

Project Links
-------------

- `PatternMatching: Python Pattern Matching @ GrantJenks.com`_
- `PatternMatching @ PyPI`_
- `PatternMatching @ Github`_
- `Issue Tracker`_

.. _`PatternMatching: Python Pattern Matching @ GrantJenks.com`: http://www.grantjenks.com/docs/patternmatching/
.. _`PatternMatching @ PyPI`: https://pypi.python.org/pypi/patternmatching
.. _`PatternMatching @ Github`: https://github.com/grantjenks/python-pattern-matching
.. _`Issue Tracker`: https://github.com/grantjenks/python-pattern-matching/issues

Python Pattern Matching License
-------------------------------

Copyright 2016 Grant Jenks

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
