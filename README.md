# PyPatt - Python Pattern Matching

```python
import pypatt

pypatt.transform
def test_demo():
    values = [[1, 2, 3], ('a', 'b', 'c'), 'hello world',
        False, [4, 5, 6], (1, ['a', True, (0, )], 3)]

    for value in values:
        with match(value):
            with 'hello world':
                print 'Match strings!'
            with False:
                print 'Match booleans!'
            with [1, 2, 3]:
                print 'Match lists!'
            with ('a', 'b', 'c'):
                print 'Match tuples!'
            with [4, 5, quote(temp)]:
                print 'Bind variables! temp =', temp
            with (1, ['a', True, quote(result)], 3):
                print 'Supports nesting! result =', result
```

* Only `True` and `False` match booleans (no type coercion).
* Bind variable names using the `quote` call.
* Supports `as name` in `with match` like: `with match(expression) as name:`


## Testing

* Requires Python 2.7
* Run `nosetests`

# TODO

* Support Ellipsis like syntax to match anything in the rest of this list or
  tuple. Maybe instead use `quote(*args)` to mean zero or more elements.
  Elements are bound to args.

```python
    match [1, 2, 3, 4]:
        like [1, 2, quote(*args)]:
            print 'args == [3, 4]'
```

* Match `set` expression. Only allow one `quote` variable. If present the
  `quote`d variable must come last.

```python
    with match({3, 1, 4, 2}):
        with {1, 2, 4, quote(value)}:
            print 'value == 3'
        with {3, 4, quote(*args)}:
            print 'args = {1, 2}'
```

* Match `dict` expression?
* Support function calls or attribute lookup with `eval(...)`?
* Match regexp?
* Add "when" syntax like:
* Type-pattern: int(var)
* F#-like `or` / `and` pattern

```python
    with match(list_item):
        with [first, second], when(first < second):
            print 'ascending'
        with [first, second], when(first > second):
            print 'descending'
```

* Simple code substitution. Define function for namespace with statements

@pypatt.macro('first', 'tail')
def and(first, tail):
    if eval(expand(first)):
       return true
    else:
       return eval(expand(tail))

@pypatt.macrosub(and)
def test():
    return and(False, 1 / 0)
