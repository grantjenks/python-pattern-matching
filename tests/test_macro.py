from __future__ import print_function

import pypatt
from pypatt import _cpython2

def only_cpython2(func):
    def do_nothing():
        pass
    return func if _cpython2 else do_nothing

if _cpython2:
    @pypatt.transform
    def match_basic(value):
        other_value = 20

        with match(value):
            with True:
                return 'True'
            with 10:
                return '10'
            with 'abc':
                return 'abc'
            with [False, 0]:
                return '[False, 0]'
            with ('blah', True, 10):
                return 'triple'
            with (0, [1, (2, [3, (4,)])]):
                return 'nested'
            with other_value:
                return '20'
            with quote(result):
                return result

@only_cpython2
def test_basic():
    values = (
        (True, 'True'),
        (10, '10'),
        ('abc', 'abc'),
        ([False, 0], '[False, 0]'),
        (('blah', True, 10), 'triple'),
        ((0, [1, (2, [3, (4,)])]), 'nested'),
        (20, '20'),
        (12345, 12345),
    )
    for value, result in values:
        assert match_basic(value) == result

if _cpython2:
    @pypatt.transform
    def match_many(value):
        with match(value % 2):
            with 0:
                with match(value):
                    with 2:
                        return '2'
                    with 4:
                        return '4'
                    with quote(_):
                        return '?'
            with 1:
                with match(value):
                    with 1:
                        return '1'
                    with 3:
                        return '3'
                    with quote(_):
                        return '$'

@only_cpython2
def test_many():
    values = (
        (0, '?'),
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '$'),
    )
    for value, result in values:
        assert match_many(value) == result

def match_method(value):
    # todo: decorate class method
    pass

def match_as(value):
    # todo: use with match(expr) _as name_: syntax
    pass

def match_bind(value):
    # todo: test binding the same variable
    pass

@only_cpython2
def test_roundtrip():
    from pypatt import uncompile, recompile
    from types import FunctionType, CodeType
    import os

    print('Importing everything in the medicine cabinet:')
    for filename in os.listdir(os.path.dirname(os.__file__)):
        name, ext = os.path.splitext(filename)
        if ext != '.py' or name == 'antigravity':
            continue
        try:
            __import__(name)
        except ImportError:
            pass
    print('Done importing. We apologize for the noise above.')

    print('Round-tripping functions to source code and back:')
    success = 0
    failed = 0
    unsupported = 0
    errors = 0

    import gc
    allfuncs = [obj for obj in gc.get_objects() if type(obj) is FunctionType]

    for func in allfuncs:
        code = func.func_code
        if type(code) is not CodeType:
            continue # PyPy builtin-code

        try:
            recode = recompile(*uncompile(code))
            if code == recode:
                success += 1
            else:
                import dis
                print('<FAILED>', func.func_name)
                print('<BEFORE>')
                dis.dis(code)
                print('<AFTER>')
                dis.dis(recode)
                print('</FAILED>')
                failed += 1
        except RuntimeError:
            unsupported += 1
        except IOError:
            errors += 1

        message = (
            '\r{0} successful roundtrip,'
            ' {1} failed roundtrip,'
            ' {2} unsupported,'
            ' {3} nosource'
        ).format(success, failed, unsupported, errors)

        print(message, end='')

    print('')

    if errors > 0:
        raise Exception

if __name__ == '__main__':
    import nose
    nose.runmodule()
