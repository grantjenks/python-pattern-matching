# Python Pattern Matching

> **Composable patterns and regular expressions for Python objects.**

Python Pattern Matching is a small, pure-Python library for matching values,
destructuring records and collections, binding names, applying predicates, and
expressing regular-expression-style patterns over sequences of arbitrary
Python objects.

Patterns are ordinary runtime values. There are no import hooks, AST transforms,
or special syntax.

```console
pip install patternmatching
```

Python 3.10 through 3.14 are supported. The package includes type information.

## Sixty-second tour

`match()` returns an immutable `Match` containing bindings, or `None` when the
pattern does not match:

```python
from patternmatching import bind, match

result = match(
    {"event": "created", "user": {"name": "Ada", "id": 42}},
    {"event": "created", "user": {"name": bind.name}},
)

assert result is not None
assert result.name == "Ada"
assert result["name"] == "Ada"
```

A `Match` is always truthy, even when it has no bindings, so existing
`if match(value, pattern):` code remains natural. Failed matches return `None`.

The latest successful results are also retained in `bound` for the original
ambient-binding style:

```python
from patternmatching import bound

assert bound.name == "Ada"
```

## Core patterns

### Literals, types, and sequences

Literal patterns compare equal to values. A class pattern uses `isinstance`;
when the value is itself a class, `issubclass` is used. Lists and tuples match
recursively and require the same concrete sequence type and length.

```python
assert match(42, int)
assert match(bool, int)
assert match([1, "two", [3.0]], [int, str, [float]])
```

### Bindings

Any attribute of `bind` creates a named binding. Reusing a name turns it into
an equality constraint. `bind.any` matches one value without storing it.

```python
assert match(("left", "left"), (bind.side, bind.side))
assert bound.side == "left"

assert match([1, 2, 3], [bind.any, bind.middle, bind.any])
assert bound.middle == 2

assert match(("left", "right"), (bind.side, bind.side)) is None
```

Bindings with names that collide with mapping methods, such as `items`, remain
available through `result["items"]`.

### Mapping patterns

A bare mapping is a recursive subset pattern. Every pattern key must exist and
its value must match; extra keys in the input are allowed.

```python
payload = {
    "user": {"name": "Ada", "roles": ["admin", "author"]},
    "request_id": 42,
}

result = match(
    payload,
    {"user": {"name": bind.name, "roles": [str, bind.role]}},
)

assert result == {"name": "Ada", "role": "author"}
```

Use `equal(value)` when ordinary equality is intended instead of structural
matching:

```python
from patternmatching import equal

assert match(payload, equal(payload))
assert match(payload, equal({"request_id": 42})) is None
```

### Record patterns

`record()` matches an instance and selected attributes. Positional patterns use
the class's `__match_args__`; keyword patterns use `getattr`. Dataclasses define
`__match_args__` automatically, and regular classes can define it themselves.

```python
from dataclasses import dataclass
from patternmatching import record


@dataclass
class Point:
    x: int
    y: int


result = match(Point(2, 3), record(Point, bind.x, y=int))
assert result == {"x": 2}
```

Keyword-only matching works for arbitrary attribute objects, including classes
without `__match_args__`:

```python
class User:
    def __init__(self, name, active):
        self.name = name
        self.active = active


some_user = User("Ada", True)
assert match(some_user, record(User, name=bind.name, active=True))
```

Record and mapping bindings are transactional: a failed nested pattern does not
leak partial bindings into another alternative or result.

### Predicates and regular expressions

`like(pattern, name="match")` applies a callable to the value. A falsy result,
or a common attribute/lookup/type/value error, is a mismatch. A truthy result is
bound under `name`; pass `name=None` when no result is needed.

Strings, bytes, and compiled `re.Pattern` values use `re.match` semantics:

```python
from patternmatching import like

result = match("item-42", like(r"item-(\d+)"))
assert result.match.group(1) == "42"

assert match(b"item-42", like(rb"item-(\d+)"))
```

## Regular expressions for object sequences

The sequence helpers compose regex-like patterns with repetition, alternatives,
exclusion, capturing groups, greediness, and backtracking. They work on strings,
bytes, lists, tuples, and other indexable sequences.

```python
from patternmatching import group, padding, repeat

events = ["noise", "BEGIN", 1, 2, 3, "END", "tail"]
pattern = (
    padding
    + ["BEGIN"]
    + (int * repeat(min=1)) * group("values")
    + ["END"]
)

result = match(events, pattern)
assert result.values == [1, 2, 3]
```

`match()` starts at offset zero and may consume only a prefix, like `re.match`.
`fullmatch()` requires the entire generic sequence to be consumed:

```python
from patternmatching import fullmatch

pattern = "ab" * group("prefix")
assert match("abc", pattern) == {"prefix": "ab"}
assert fullmatch("abc", pattern) is None
assert fullmatch("ab", pattern) == {"prefix": "ab"}
```

### Sequence helper vocabulary

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

Multiplication binds more tightly than concatenation, so parentheses often make
intent clearer:

```python
pattern = ["("] + (int * repeat(min=1)) * group("items") + [")"]
```

### Native text and bytes acceleration

When a regex-like helper pattern is applied to `str` or `bytes`, the matcher
conservatively translates the complete supported pattern to Python's `re`
engine. Translation is cached. Supported patterns include literals, `anyone`,
repetition, non-binding alternatives and exclusions, captures, and simple
bindings/backreferences.

The optimization is all-or-nothing. If any part cannot be represented with the
same semantics—for example an arbitrary predicate—the library runs the generic
engine for the whole pattern. There is no mixed execution and no semantic
approximation. Custom matchers may disable translation with
`Matcher(native=False)`.

## Match results and ambient bindings

Every successful call returns a `Match` and pushes that same object onto the
matcher's `bound` history. The default history keeps the ten latest successes.

```python
from patternmatching import Matcher

matcher = Matcher(bound_limit=3)
result = matcher.match([1, 2], [bind.left, bind.right])

assert result == {"left": 1, "right": 2}
assert matcher.bound.right == 2
assert len(matcher.bound) == 1
```

`bound.pop()` removes the latest result and `bound.reset()` clears the current
context. `bound.scope()` restores the prior history on exit and works as both a
context manager and a sync or async function decorator:

```python
with bound.scope():
    assert match(42, bind.answer)
    assert bound.answer == 42


@bound.scope()
def parse(value):
    return match(value, bind.value)
```

Binding state is isolated with `contextvars`, so threads and asynchronous tasks
do not overwrite one another. Set `bound_limit=None` for unbounded history.

In v4, `bound.reset()` is deliberately only a clearing operation. Replace the
old `@bound.reset` decorator spelling with `@bound.scope()`.

## Custom patterns and matchers

Pattern objects can implement `__match__(matcher, value)`. Raise
`patternmatching.Mismatch` to reject the value or return normally to accept it:

```python
import patternmatching


class Between:
    def __init__(self, low, high):
        self.low = low
        self.high = high

    def __match__(self, matcher, value):
        if not self.low <= value <= self.high:
            raise patternmatching.Mismatch


assert match(7, Between(1, 10))
```

`Matcher` also accepts an ordered collection of matching cases for applications
that define an entire matching vocabulary. Native text acceleration is enabled
only for the default case set.

## Migrating from v3

- Successful `match()` calls now return `Match` instead of the matched value or
  internal action result. Failed calls still produce a falsy result (`None`).
- Use `fullmatch()` when a sequence helper must consume the entire input.
- `bound` keeps ten results by default and is context-local.
- Replace `@bound.reset` with `@bound.scope()`; `bound.reset()` now only clears.
- Bare mappings are recursive subset patterns. Wrap a mapping in `equal()` to
  request ordinary equality.
- Use `record()` for dataclasses, named tuples, and attribute-based objects.

## Development

Run the supported Python matrix with Nox and uv:

```console
uvx nox -s tests
```

The tests include doctests, v4 behavior and concurrency coverage, native/generic
differential tests, and object-pattern tests adapted from CPython's regular
expression tests.

## License

Python Pattern Matching is copyright 2015–2026 Grant Jenks and licensed under
the Apache License, Version 2.0.
