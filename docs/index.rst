PyPatt - Python Pattern Matching
================================

PyPatt is an Apache2 licensed Python module for pattern matching as found in
functional programming languages.

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
