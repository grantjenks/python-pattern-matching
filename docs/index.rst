Python Pattern Matching
=======================

Python Pattern Matching is an Apache2 licensed Python module for pattern
matching like that found in functional programming languages. Most projects
that address Python pattern matching focus on syntax and simple cases. Operator
overloading is often used to change the semantics of operators to support
pattern matching. In other cases, function decorators are used to implement
multiple dispatch, sometimes known as function overloading. Each of these
syntaxes, operators and decorators, is really more of a detail in the
application of pattern matching.

Python Pattern Matching focuses instead on the semantics of pattern matching in
Python. The dynamic duck-typing behavior in Python is distinct from the tagged
unions found in functional programming languages. Rather than trying to emulate
the behavior of functional pattern matching, this project attempts to implement
pattern matching that looks and feels native to Python. In doing so the
traditional function call is used as syntax.

.. todo::

   Background and motivation.

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
