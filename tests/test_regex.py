"""Regular expression module tests.

A large number of these were ported from:
https://github.com/python/cpython/blob/master/Lib/test/re_tests.py

"""

import patternmatching as pm

a_foo = 'a' * pm.group(1)
abc_e = 'abc' * pm.either
term = 'multiple words'
b_s = 'b' * pm.repeat

def test_pattern_add_tuple():
    pattern = pm.Pattern((1, 2, 3))
    pattern = pattern + (4, 5, 6)
    assert pattern == pm.Pattern((1, 2, 3, 4, 5, 6))

def test_pattern_radd_tuple():
    pattern = pm.Pattern((4, 5, 6))
    pattern = (1, 2, 3) + pattern
    assert pattern == pm.Pattern((1, 2, 3, 4, 5, 6))

def test_pattern_add_single():
    pattern = pm.Pattern((1, 2, 3))
    pattern = pattern + None
    assert pattern == pm.Pattern((1, 2, 3, None))

def test_pattern_radd_single():
    pattern = pm.Pattern((4, 5, 6))
    pattern = None + pattern
    assert pattern == pm.Pattern((None, 4, 5, 6))

def test_pattern_ne():
    assert pm.Pattern((1, 2, 3)) != pm.Pattern((4, 5, 6))

def test_pattern_hash():
    assert hash(pm.Pattern((1, 2, 3))) == hash((1, 2, 3))

def test_pattern_repr():
    assert repr(pm.Pattern((1, 2, 3))) == 'Pattern(1, 2, 3)'

def test_anyone_repr():
    assert repr(pm.anyone) == 'anyone'

def test_repeat_rmul_single():
    assert None * pm.repeat == pm.Repeat((None,), 0, pm.infinity, True)

def test_repeat_repr():
    assert repr(pm.repeat) == 'Repeat(pattern=(), min=0, max=inf, greedy=True)'

def test_either_rmul_single():
    assert None * pm.either == pm.Either(None)

def test_either_repr():
    assert repr(pm.either) == 'Either()'

@pm.bound.reset
def run(*args):
    pattern, value, result = args
    if result is None:
        assert not pm.match(value, pattern)
    else:
        assert pm.match(value, pattern)
        del result['_']
        assert pm.bound == result

def test_basic():
    run('', '', {'_': ''})
    run('abc', 'abc', {'_': 'abc'})
    run('abc', 'xbc', None)
    run('abc', 'axc', None)
    run('abc', 'abx', None)
    run('abc', 'xabc', None)
    run('abc', 'xabcy', None)
    run('abc', '', None)
    run(term + ' of text', 'uh-oh', None)


def test_groups():
    run(a_foo, 'a', {'_': 'a', 1: 'a'})
    run(a_foo, 'aa', {'_': 'a', 1: 'a'})
    run(a_foo * pm.group(2), 'a', {'_': 'a', 1: 'a', 2: 'a'})
    run(a_foo * pm.group(2) * pm.group(3), 'a',
       {'_': 'a', 1: 'a', 2: 'a', 3: 'a'})
    run(a_foo + 'b' + 'c' * pm.group(2), 'abc',
        {'_': 'abc', 1: 'a', 2: 'c'})
    run(pm.Group(abc_e, name=1) * pm.repeat + 'd', 'abbbcd',
        {'_': 'abbbcd', 1: 'c'})
    run(pm.Group(abc_e, name=1) * pm.repeat + 'bcd', 'abcd',
        {'_': 'abcd', 1: 'a'})


def test_anyone():
    run('a' + pm.anyone + 'c', 'abc', {'_': 'abc'})
    run('a' + pm.anything + 'c', 'axyzc', {'_': 'axyzc'})
    run('a' + pm.anything + 'c', 'axyzd', None)
    run('a' + pm.anything + 'c', 'ac', {'_': 'ac'})
    run('a' + pm.anyone * pm.repeat(min=2, max=3) + 'c', 'abbc', {'_': 'abbc'})

def test_repeat():
    run('a' + b_s + 'c', 'abc', {'_': 'abc'})
    run('a' + b_s + 'bc', 'abc', {'_': 'abc'})
    run('a' + b_s + 'bc', 'abbc', {'_': 'abbc'})
    run('a' + b_s + 'bc', 'abbbbc', {'_': 'abbbbc'})
    run('a' * pm.repeat, '', {'_': ''})
    run('a' * pm.repeat, 'a', {'_': 'a'})
    run('a' * pm.repeat, 'aaa', {'_': 'aaa'})
    run(pm.padding + 'a' * pm.repeat(1) + 'b' + 'c' * pm.repeat(1), 'aabbabc',
        {'_': 'aabbabc'})


def test_repeat_range():
    run('a' + 'b' * pm.repeat(1,) + 'bc', 'abbbbc', {'_': 'abbbbc'})
    run('a' + 'b' * pm.repeat(1,3) + 'bc', 'abbbbc', {'_': 'abbbbc'})
    run('a' + 'b' * pm.repeat(3,4) + 'bc', 'abbbbc', {'_': 'abbbbc'})
    run('a' + 'b' * pm.repeat(4,5) + 'bc', 'abbbbc', None)


def test_some():
    run('a' + 'b' * pm.something + 'bc', 'abbc', {'_': 'abbc'})
    run('a' + 'b' * pm.something + 'bc', 'abc', None)
    run('a' + 'b' * pm.something + 'bc', 'abq', None)
    run('a' + 'b' * pm.something + 'bc', 'abbbbc', {'_': 'abbbbc'})


def test_maybe():
    run('a' * pm.maybe, '', {'_': ''})
    run('a' * pm.maybe, 'a', {'_': 'a'})
    run('a' * pm.maybe, 'aa', {'_': 'a'})
    run('a' + 'a' * pm.maybe, 'aa', {'_': 'aa'})
    run('a' + pm.anyone + 'c' + 'd' * pm.maybe, 'abc', {'_': 'abc'})
    run('a' + 'b' * pm.maybe + 'bc', 'abbc', {'_': 'abbc'})
    run('a' + 'b' * pm.maybe + 'bc', 'abc', {'_': 'abc'})
    run('a' + 'b' * pm.repeat(0, 1) + 'bc', 'abc', {'_': 'abc'})
    run('a' + 'b' * pm.maybe + 'bc', 'abbbbc', None)
    run('a' + 'b' * pm.maybe + 'c', 'abc', {'_': 'abc'})
    run('a' + 'b' * pm.repeat(0, 1) + 'c', 'abc', {'_': 'abc'})


def test_either():
    run('a' + pm.either('bc') + 'd', 'abc', None)
    run('a' + 'bc' * pm.either + 'd', 'abd', {'_': 'abd'})
    run(('ab', 'cd') * pm.either, 'abc', {'_': 'ab'})
    run(('ab', 'cd') * pm.either, 'abcd', {'_': 'ab'})
    run(pm.Either('a' * pm.repeat(min=1), 'b') * pm.repeat, 'ab', {'_': 'ab'})
    run(pm.Either('a' * pm.repeat(min=1), 'b') * pm.repeat(min=1), 'ab',
        {'_': 'ab'})
    run(pm.Either('a' * pm.repeat(min=1), 'b') * pm.maybe, 'ab', {'_': 'a'})
    run('abcde' * pm.either, 'e', {'_': 'e'})
    run('abcde' * pm.either + 'f', 'ef', {'_': 'ef'})
    run(pm.padding + pm.Either('ab', 'cd') + 'e', 'abcde', {'_': 'abcde'})
    run('abhgefdc' * pm.either + 'ij', 'hij', {'_': 'hij'})


def test_exclude():
    run('a' + 'bc' * pm.exclude + 'd', 'aed', {'_': 'aed'})
    run('a' + 'bc' * pm.exclude + 'd', 'abd', None)
    run('ab' * pm.exclude * pm.repeat, 'cde', {'_': 'cde'})


def test_misc():
    bc_e_r_g_1 = 'bc' * pm.either * pm.repeat * pm.group(1)
    bc_e_r_1_g_1 = 'bc' * pm.either * pm.repeat(min=1) * pm.group(1)

    run(pm.padding + 'ab' * pm.either + 'c' * pm.repeat + 'd', 'abcd',
        {'_': 'abcd'})
    run(('ab', 'a' + b_s) * pm.either + 'bc', 'abc', {'_': 'abc'})
    run('a' + bc_e_r_g_1 + 'c' * pm.repeat, 'abc', {'_': 'abc', 1: 'bc'})
    run('a' + bc_e_r_g_1 + ('c' * pm.repeat + 'd') * pm.group(2), 'abcd',
        {'_': 'abcd', 1: 'bc', 2: 'd'})
    run('a' + bc_e_r_1_g_1 + ('c' * pm.repeat + 'd') * pm.group(2), 'abcd',
        {'_': 'abcd', 1: 'bc', 2: 'd'})
    run('a' + bc_e_r_g_1 + ('c' * pm.repeat(min=1) + 'd') * pm.group(2),
        'abcd', {'_': 'abcd', 1: 'b', 2: 'cd'})
    run('a' + 'bcd' * pm.either * pm.repeat + 'dcdcde', 'adcdcde',
        {'_': 'adcdcde'})
    run('a' + 'bcd' * pm.either * pm.repeat(min=1) + 'dcdcde', 'adcdcde', None)
    run(('ab', 'a') * pm.either + b_s + 'c', 'abc', {'_': 'abc'})
    run(pm.Group(pm.Group('a') + pm.Group('b') + pm.Group('c')) + pm.Group('d'),
        'abcd', {'_': 'abcd'})
    run(pm.anything * pm.group(1) + 'c' + pm.anything * pm.group(2), 'abcde',
        {'_': 'abcde', 1: 'ab', 2: 'de'})
    run('k' * pm.either, 'ab', None)
    run('a' + '-' * pm.maybe + 'c', 'ac', {'_': 'ac'})
    run(pm.Either(pm.Group('a') + pm.Group('b') + 'c', 'ab'), 'ab',
        {'_': 'ab'})
    run('a' * pm.group * pm.repeat(min=1) + 'x', 'aaax', {'_': 'aaax'})
    run('ac' * pm.either * pm.group(1) * pm.repeat(min=1) + 'x', 'aacx',
        {'_': 'aacx', 1: 'c'})
    run(pm.Group('/' * pm.exclude * pm.repeat + '/', 1) * pm.repeat + 'sub1/',
        'd:msgs/tdir/sub1/trial/away.cpp',
        {'_': 'd:msgs/tdir/sub1/', 1: 'tdir/'})
    run(('N' * pm.exclude * pm.repeat + 'N') * pm.group(1) * pm.repeat(min=1),
        'abNNxyzN', {'_': 'abNNxyzN', 1: 'xyzN'})
    run(('N' * pm.exclude * pm.repeat + 'N') * pm.group(1) * pm.repeat(min=1),
        'abNNxyz', {'_': 'abNN', 1: 'N'})
    run(abc_e * pm.repeat * pm.group(1) + 'x', 'abcx', {'_': 'abcx', 1: 'abc'})
    run(abc_e * pm.repeat * pm.group(1) + 'x', 'abc', None)
    run(pm.padding + 'xyz' * pm.either * pm.repeat * pm.group(1) + 'x', 'abcx',
        {'_': 'abcx', 1: ''})
    run(pm.Either(pm.Group('a') * pm.repeat(min=1) + 'b', 'aac'), 'aac',
        {'_': 'aac'})


def test_not_greedy():
    run('a' + pm.anyone * pm.repeat(min=1, greedy=False) + 'c', 'abcabc',
        {'_': 'abc'})


def test_something():
    run(pm.Either('a' * pm.something, 'b') * pm.repeat, 'ab', {'_': 'ab'})
    run(pm.Either('a' * pm.something, 'b') * pm.repeat(0,), 'ab', {'_': 'ab'})
    run(pm.Either('a' * pm.something, 'b') * pm.something, 'ab', {'_': 'ab'})
    run(pm.Either('a' * pm.something, 'b') * pm.repeat(1,), 'ab', {'_': 'ab'})
    run(pm.Either('a' * pm.something, 'b') * pm.maybe, 'ab', {'_': 'a'})
    run(pm.Either('a' * pm.something, 'b') * pm.repeat(0, 1), 'ab', {'_': 'a'})
