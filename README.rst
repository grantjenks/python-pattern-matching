
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
