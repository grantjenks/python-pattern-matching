# Python Pattern Matching

> **Composable patterns and regular expressions for Python objects.**

Python Pattern Matching is a small, pure-Python library for matching values,
destructuring sequences, binding names, applying predicates, and expressing
regular-expression-style patterns over sequences of arbitrary Python objects.

Patterns are ordinary runtime values. There are no import hooks, codecs, AST
transforms, or special syntax.

```console
pip install patternmatching
```

## Sixty-second tour

Match literals, types, nested sequences, and predicates:

```python
from patternmatching import bind, bound, like, match

message = ["created", "/users/42", 201]

assert match(
    message,
    [
        "created",
        bind.path,
        like(lambda status: 200 <= status < 300, name=None),
    ],
)
assert bound.path == "/users/42"
```

A type used as a pattern matches its instances. A `like(...)` pattern applies
a callable, or a text regular expression, to the value.

Bindings are also equality constraints when reused:

```python
assert match(("left", "left"), (bind.side, bind.side))
assert bound.side == "left"

assert not match(("left", "right"), (bind.side, bind.side))
```

## Regular expressions for object sequences

The same object patterns compose into regex-like sequence patterns. Repetition,
alternatives, exclusion, capturing groups, greediness, and backtracking work on
strings, lists, tuples, and other indexable sequences.

```python
from patternmatching import bound, group, match, padding, repeat

events = ["noise", "BEGIN", 1, 2, 3, "END", "tail"]

pattern = (
    padding
    + ["BEGIN"]
    + (int * repeat(min=1)) * group("values")
    + ["END"]
)

assert match(events, pattern)
assert bound.values == [1, 2, 3]
```

Here `padding` is a non-greedy repetition of any object. The `int` pattern
matches integer objects, `repeat(min=1)` requires one or more, and `group(...)`
captures the matching slice.

Sequence patterns match from the beginning and may match a prefix, like
`re.match`. A successful pattern does not inherently require consuming the
entire sequence.

## Pattern vocabulary

### Literals and equality

Literal patterns compare equal to the value:

```python
assert match(1, 1)
assert match("hello", "hello")
```

Other objects also match by equality when no more specific rule applies.

### Types

A class pattern uses `isinstance`. When the value is itself a class,
`issubclass` is used:

```python
assert match(42, int)
assert match(bool, int)
```

### Sequences

Lists match list patterns, tuples match tuple patterns, and nested patterns are
visited recursively:

```python
assert match([1, "two", [3.0]], [int, str, [float]])
```

### Bindings

Any attribute of `bind` creates a named binding pattern. `bind.any` matches one
value without storing it:

```python
assert match([1, 2, 3], [bind.any, bind.middle, bind.any])
assert bound.middle == 2
```

Each successful call pushes its bindings onto `bound`. Attribute and mapping
access read the most recent result. `bound.pop()` discards it and
`bound.reset()` clears all results. `bound.reset` can also decorate a function
to scope the results it creates.

### Predicates and text regular expressions

`like(pattern, name="match")` applies a callable to the value. A falsy result,
or a common value/lookup/type error, is a mismatch. A truthy result is bound
under `name`; pass `name=None` when no result is needed.

When `pattern` is text, it is passed to `re.match`:

```python
assert match("item-42", like(r"item-(\d+)"))
assert bound.match.group(1) == "42"
```

### Custom patterns

Pattern objects can implement `__match__(matcher, value)`. Raise
`patternmatching.Mismatch` to reject the value, or return normally to accept it:

```python
import patternmatching


class Between:
    def __init__(self, low, high):
        self.low = low
        self.high = high

    def __match__(self, matcher, value):
        if not self.low <= value <= self.high:
            raise patternmatching.Mismatch


assert patternmatching.match(7, Between(1, 10))
```

The `Matcher` class also accepts an ordered collection of matching cases for
applications that need to define an entire matching vocabulary.

## Sequence pattern operators

- `anyone` matches one object.
- `anything` matches zero or more objects greedily.
- `something` matches one or more objects greedily.
- `padding` matches zero or more objects non-greedily.
- `pattern * repeat(min=0, max=inf, greedy=True)` repeats a pattern.
- `pattern * maybe` matches zero or one occurrence.
- `either(a, b, ...)` matches the first successful alternative.
- `exclude(a, b, ...)` consumes one object if none of its alternatives match.
- `pattern * group(name)` captures the matching slice.
- `left + right` concatenates sequence patterns.

Parentheses are useful because multiplication binds more tightly than
concatenation:

```python
pattern = ["("] + (int * repeat(min=1)) * group("items") + [")"]
```

## Development

Run the test suite with Nox and uv:

```console
uvx nox -s tests
```

The test suite includes doctests and a set of object-pattern tests adapted from
CPython's regular-expression tests.

## License

Python Pattern Matching is copyright 2015–2026 Grant Jenks and licensed under
the Apache License, Version 2.0.
