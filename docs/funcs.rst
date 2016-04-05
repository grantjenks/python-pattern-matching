Pattern Matching Functional Implementation
==========================================

.. todo::

   Discussion.

Reference
---------

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
