# PyPatt

Python Pattern Matching.

```python
def test_demo():
    values = [[1, 2, 3], ('a', 'b', 'c'), 'hello world',
        False, [4, 5, 6], (1, ['a', True, (0, )], 3)]

    for value in values:
        match value:
            like 'hello world':
                print 'Match strings!'
            like False:
                print 'Match booleans!'
            like [1, 2, 3]:
                print 'Match lists!'
            like ('a', 'b', 'c'):
                print 'Match tuples!'
            like [4, 5, temp]:
                print 'Bind variables! temp =', temp
            like (1, ['a', True, result], 3):
                print 'Supports nesting! result =', result
```

Introduces two new keywords to the Python programming language:

* match_stmt = match <expr>:
* like_stmt = like <expr>:

Limitations abound. But as a proof-of-concept, it has promise.

* See https://github.com/dropbox/pyxl for the codec inspiration.

# Notes

* Make sure "import pypatt" is in your site.py file. (This will require that
  pypatt be on your pythonpath.)
* Make sure "# coding: pypatt" is the first line in your Python file.
* Only 'True'/'False' match booleans (no type coercion).
* '_' matches anything even if already defined in locals or globals and binds
  to the last matched item. For example:

```python
    _ = 'test'
    match value:
        like [_, _]:
            print 'match'
```

  will match all lists of length 2 and '_' will be bound to the
  item in value[1].
* Beware of matching variables in a loop like:

```python
    for value in xrange(5):
        match value:
            like 1:
                print 'saw 1'
            like value:
                print 'saw', value
                # Be sure to delete the bound variable otherwise,
                # the first iteration will bind 'value' to 0 and
                # the third iteration will not match 'value'.
                del value
```

* 'exec' is used to insert bound variables into the local scope. In Python
  2.* 'exec' may not be used with nested functions.

# Testing

* Requires 'nose'

## Passing

* Python 2.7 (r27:82525, Jul  4 2010, 09:01:59) [MSC v.1500 32 bit (Intel)] on win32

# TODO

* Add "as" syntax:

```python
    match list(generator) as items:
        like [1, 2, 3, 4]:
            print items
```

* Use Ellipsis to mean ... match anything in the rest of this list or tuple.

```python
    match [1, 2, 3, 4]:
        like [1, 2, Ellipsis]:
            print 'Ellipsis matched 3, 4.'
```

* Support value as iterable?

```python
    match iter([1, 2, 3, 4]):
        like [1, 2, Ellipsis, tail]:
            return tail # This is the iterator pointing at 3
```

* Emacs mode based on Python which recognizes the 'match' and 'like' keywords.
* Match dict expression (require bound keys, allow Ellipsis)
* Support Attribute lookup e.g. "TypeName.Attr"
* Support function calls
* Add "when" syntax like:

```python
    match list_item:
        like [first, second] when first < second:
            print 'ascending'
        like [first, second] when first > second:
            print 'descending'
```

## Add Codec Tools

* As a module:

```python
python -m codectools --codec pypatt --exec program.py
```

Includes pypatt codec before exec'ing program.py. So that the codec doesn't have to be put in the site.py file during development.

* As a codec:

```python
# coding: codectools
# usecodecs: pyxl pypatt
```

This will run the code first through the pyxl codec and then through the pypatt codec.

# More Notes

# Simple Code Substitution

## SortedList.py

from pypatt import macro

@astree
def fix_idx():
    if idx < 0:
        idx += _len
    if idx < 0:
        idx = 0
    if idx > _len:
        idx = _len

## SortedListWithKey.py

from pypatt import expand
from .sortedlist import fix_idx

@usesmacros
def blah_blah(arg):

    @expand
    def fix_idx(): pass

# Complex Code Substitution

## SortedListWithKey.py

### count

        total = 0
        len_keys = len(_keys)
        len_sublist = len(_keys[pos])

        while True:
            if _keys[pos][idx] != key:
                return total
            if _lists[pos][idx] == val:
                total += 1
            idx += 1
            if idx == len_sublist:
                pos += 1
                if pos == len_keys:
                    return total
                len_sublist = len(_keys[pos])
                idx = 0

### remove

        len_keys = len(_keys)
        len_sublist = len(_keys[pos])

        while True:
            if _keys[pos][idx] != key:
                raise ValueError('{0} not in list'.format(repr(val)))
            if _lists[pos][idx] == val:
                self._delete(pos, idx)
                return
            idx += 1
            if idx == len_sublist:
                pos += 1
                if pos == len_keys:
                    raise ValueError('{0} not in list'.format(repr(val)))
                len_sublist = len(_keys[pos])
                idx = 0

### pattern

@macro
def lists_search(*args):
    len_keys = len(_keys)
    len_sublist = len(_keys[pos])
    __setup__

    while True:
        if _keys[pos][idx] != key:
            __key_mismatch__
        if _lists[pos][idx] == val:
            __val_match__
        idx += 1
        if idx == len_sublist:
            pos += 1
            if pos == len_keys:
                __eol__
            len_sublist = len(_keys[pos])
            idx = 0

#### count:

with __q as __setup__:
    total = 0

with __q as __key_mismatch__:
    return total

with __q as __val_match__:
    total += 1

with __q as __eol__:
    return total

lists_search(__setup__, __key_mismatch__, __val_match__, __eol__)

#### alternative syntax for remove:

from pypatt import usesmacros, expand
from .sortedlist import lists_search

@usesmacros
def remove(*args):
    ...
    @expand
    def lists_search():
        with stmts as __setup__:
            pass

        with stmts as __key_mismatch__:
            raise ValueError('{0} not in list'.format(repr(val)))

        with stmts as __val_match__:
            self._delete(pos, idx)
            return

        with stmts as __eol__:
            raise ValueError('{0} not in list'.format(repr(val)))

# Complex Code Patterns

## match statement

class MatchException(Exception):
    pass

@astree
def match(ast_expr):
    ls = locals()
    temp = eval(ast_expr)
    try:
        for ast_patt in ast_patts:
            result = bind(temp, ast_patt)
            if result:
                for name in result:
                    ls[name] = result[name]
                raise MatchException
    except MatchException:
        pass


@usesmacros
def search_file():
    for line in fptr:
        @expand
        def match(line):
            with expr as ast_patts.item:
                "hello"
                with stmts:
                    pass
            with expr as ast_patts.item:
                [1, 2, 3, temp]

@pypatt
def search_list(items):
    for item in items:
        if _match(item):
            with 'hello':
                print 'hi'
            with [1, 2, 3]:
                print 'saw list'
            with [_q(a), _q(b)]:
                print 'saw two items:', a, b

def search_list(items):
    for item in items:
        try:
            _pypatt_temp0 = item
            _pypatt_asts0 = ast_parse('hello')
            _pypatt_vars0 = _pypatt_bind(_pypatt_temp0, _pypatt_asts0)
            if _pypatt_vars0:
                print 'hi'
                raise _pypatt_break
            _pypatt_asts1 = ast_parse([1, 2, 3])
            _pypatt_vars1 = _pypatt_bind(_pypatt_temp0, _pypatt_asts1)
            if _pypatt_vars1:
                print 'saw list'
                raise _pyatt_break
            _pypatt_asts2 = ast_parse([_q(a), _q(b)])
            _pypatt_vars2 = _pypatt_bind(_pypatt_temp0, _pypatt_asts2)
            if _pypatt_vars2:
                a = _pypatt_vars2['a']
                b = _pypatt_vars2['b']
                print 'saw two items', a, b
                del a
                del b
                raise _pypatt_break
        except _pypatt_break:
            pass

# Some Lessons

* should quote binding variables like _q(a)
* exec is not as useful as necessary
  * should explicitly set variables in ast transform
* pypatt function can simply do ast transform
