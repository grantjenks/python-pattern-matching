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
