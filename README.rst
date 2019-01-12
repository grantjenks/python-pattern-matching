Python Pattern Matching
=======================

Python, I love you. But I'd like you to change. It's not you, it's me. Really.
See, you don't have pattern matching. But, that's not the root of it. Macros
are the root of it. You don't have macros but that's OK. Right now, I want
pattern matching. I know you offer me ``if``/``elif``/``else`` statements but I
need more. I'm going to abuse your functions. Guido, et al, I hope you can
forgive me. This will only hurt a little.

`Python Pattern Matching`_ is an Apache2 licensed Python module for `pattern
matching`_ like that found in functional programming languages. Most projects
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
- Developed on Python 3.7
- Tested on CPython 3.4, 3.5, 3.6, 3.7 and PyPy3

.. todo::

   - Fully Documented
   - 100% test coverage
   - Hours of stress testing

   .. image:: https://api.travis-ci.org/grantjenks/python-pattern-matching.svg?branch=master
      :target: http://www.grantjenks.com/docs/patternmatching/

   .. image:: https://ci.appveyor.com/api/projects/status/github/grantjenks/python-pattern-matching?branch=master&svg=true
      :target: http://www.grantjenks.com/docs/patternmatching/


Quickstart
----------

Installing `Python Pattern Matching`_ is simple with `pip
<http://www.pip-installer.org/>`_::

    $ pip install patternmatching

You can access documentation in the interpreter with Python's built-in `help`
function. The `help` works on modules, classes, and functions in `pattern
matching`_.

.. code-block:: python

    >>> from pypatt import match, bind, bound, like
    >>> help(match)


Alternative Packages
--------------------

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


Developer Guide
---------------

* `Python Pattern Matching Tutorial`_
* `Python Pattern Matching Reference`_
* `Python Pattern Matching Search`_
* `Python Pattern Matching Index`_

.. _`Python Pattern Matching Tutorial`: http://www.grantjenks.com/docs/patternmatching/tutorial.html
.. _`Python Pattern Matching Reference`: http://www.grantjenks.com/docs/patternmatching/reference.html
.. _`Python Pattern Matching Search`: http://www.grantjenks.com/docs/patternmatching/search.html
.. _`Python Pattern Matching Index`: http://www.grantjenks.com/docs/patternmatching/genindex.html


Project Links
-------------

* `Python Pattern Matching`_
* `Python Pattern Matching at PyPI`_
* `Python Pattern Matching at GitHub`_
* `Python Pattern Matching Issue Tracker`_

.. _`Python Pattern Matching`: http://www.grantjenks.com/docs/patternmatching/
.. _`Python Pattern Matching at PyPI`: https://pypi.python.org/pypi/patternmatching/
.. _`Python Pattern Matching at GitHub`: https://github.com/grantjenks/python-pattern-matching
.. _`Python Pattern Matching Issue Tracker`: https://github.com/grantjenks/python-pattern-matching/issues


Python Pattern Matching License
-------------------------------

Copyright 2015-2019, Grant Jenks

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License.  You may obtain a copy of the
License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied.  See the License for the
specific language governing permissions and limitations under the License.

.. _`pattern matching`: http://www.grantjenks.com/docs/patternmatching/
