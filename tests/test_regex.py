"""Regular expression module tests.

A large number of these were ported from:
https://github.com/python/cpython/blob/master/Lib/test/re_tests.py

"""

import patternmatching.regex as re


a_foo = 'a' * re.group(1)
abc_e = 'abc' * re.either
term = 'multiple words'
b_s = 'b' * re.repeat

def run(*args):
    args = list(args)
    result = args.pop()
    assert re.match(*args) == result

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
    run(term, term + ' of text', {'_': term})


def test_groups():
    run(a_foo, 'a', {'_': 'a', 1: 'a'})
    run(a_foo, 'aa', {'_': 'a', 1: 'a'})
    run(a_foo * re.group(2), 'a', {'_': 'a', 1: 'a', 2: 'a'})
    run(a_foo * re.group(2) * re.group(3), 'a',
       {'_': 'a', 1: 'a', 2: 'a', 3: 'a'})
    run(a_foo + 'b' + 'c' * re.group(2), 'abc',
        {'_': 'abc', 1: 'a', 2: 'c'})
    run(re.Group(abc_e, name=1) * re.repeat + 'd', 'abbbcd',
        {'_': 'abbbcd', 1: 'c'})
    run(re.Group(abc_e, name=1) * re.repeat + 'bcd', 'abcd',
        {'_': 'abcd', 1: 'a'})


def test_anyone():
    run('a' + re.anyone + 'c', 'abc', {'_': 'abc'})
    run('a' + re.anything + 'c', 'axyzc', {'_': 'axyzc'})
    run('a' + re.anything + 'c', 'axyzd', None)
    run('a' + re.anything + 'c', 'ac', {'_': 'ac'})
    run('a' + re.anyone * re.repeat(min=2, max=3) + 'c', 'abbc', {'_': 'abbc'})

def test_repeat():
    run('a' + b_s + 'c', 'abc', {'_': 'abc'})
    run('a' + b_s + 'bc', 'abc', {'_': 'abc'})
    run('a' + b_s + 'bc', 'abbc', {'_': 'abbc'})
    run('a' + b_s + 'bc', 'abbbbc', {'_': 'abbbbc'})
    run('a' * re.repeat, '', {'_': ''})
    run('a' * re.repeat, 'a', {'_': 'a'})
    run('a' * re.repeat, 'aaa', {'_': 'aaa'})
    run(re.start + 'a' * re.repeat(1) + 'b' + 'c' * re.repeat(1), 'aabbabc',
        {'_': 'aabbabc'})


def test_repeat_range():
    run('a' + 'b' * re.repeat(1,) + 'bc', 'abbbbc', {'_': 'abbbbc'})
    run('a' + 'b' * re.repeat(1,3) + 'bc', 'abbbbc', {'_': 'abbbbc'})
    run('a' + 'b' * re.repeat(3,4) + 'bc', 'abbbbc', {'_': 'abbbbc'})
    run('a' + 'b' * re.repeat(4,5) + 'bc', 'abbbbc', None)


def test_some():
    run('a' + 'b' * re.something + 'bc', 'abbc', {'_': 'abbc'})
    run('a' + 'b' * re.something + 'bc', 'abc', None)
    run('a' + 'b' * re.something + 'bc', 'abq', None)
    run('a' + 'b' * re.something + 'bc', 'abbbbc', {'_': 'abbbbc'})


def test_maybe():
    run('a' * re.maybe, '', {'_': ''})
    run('a' * re.maybe, 'a', {'_': 'a'})
    run('a' * re.maybe, 'aa', {'_': 'a'})
    run('a' + 'a' * re.maybe, 'aa', {'_': 'aa'})
    run('a' + re.anyone + 'c' + 'd' * re.maybe, 'abc', {'_': 'abc'})
    run('a' + 'b' * re.maybe + 'bc', 'abbc', {'_': 'abbc'})
    run('a' + 'b' * re.maybe + 'bc', 'abc', {'_': 'abc'})
    run('a' + 'b' * re.repeat(0, 1) + 'bc', 'abc', {'_': 'abc'})
    run('a' + 'b' * re.maybe + 'bc', 'abbbbc', None)
    run('a' + 'b' * re.maybe + 'c', 'abc', {'_': 'abc'})
    run('a' + 'b' * re.repeat(0, 1) + 'c', 'abc', {'_': 'abc'})


def test_either():
    run('a' + 'bc' * re.either + 'd', 'abc', None)
    run('a' + 'bc' * re.either + 'd', 'abd', {'_': 'abd'})
    run(('ab', 'cd') * re.either, 'abc', {'_': 'ab'})
    run(('ab', 'cd') * re.either, 'abcd', {'_': 'ab'})
    run(re.Either('a' * re.repeat(min=1), 'b') * re.repeat, 'ab', {'_': 'ab'})
    run(re.Either('a' * re.repeat(min=1), 'b') * re.repeat(min=1), 'ab',
        {'_': 'ab'})
    run(re.Either('a' * re.repeat(min=1), 'b') * re.maybe, 'ab', {'_': 'a'})
    run('abcde' * re.either, 'e', {'_': 'e'})
    run('abcde' * re.either + 'f', 'ef', {'_': 'ef'})
    run(re.start + re.Either('ab', 'cd') + 'e', 'abcde', {'_': 'abcde'})
    run('abhgefdc' * re.either + 'ij', 'hij', {'_': 'hij'})


def test_exclude():
    run('a' + 'bc' * re.exclude + 'd', 'aed', {'_': 'aed'})
    assert re.match('a' + 'bc' * re.exclude + 'd', 'abd') is None
    run('ab' * re.exclude * re.repeat, 'cde', {'_': 'cde'})


def test_misc():
    bc_e_r_g_1 = 'bc' * re.either * re.repeat * re.group(1)
    bc_e_r_1_g_1 = 'bc' * re.either * re.repeat(min=1) * re.group(1)

    run(re.start + 'ab' * re.either + 'c' * re.repeat + 'd', 'abcd',
        {'_': 'abcd'})
    run(('ab', 'a' + b_s) * re.either + 'bc', 'abc', {'_': 'abc'})
    run('a' + bc_e_r_g_1 + 'c' * re.repeat, 'abc', {'_': 'abc', 1: 'bc'})
    run('a' + bc_e_r_g_1 + ('c' * re.repeat + 'd') * re.group(2), 'abcd',
        {'_': 'abcd', 1: 'bc', 2: 'd'})
    run('a' + bc_e_r_1_g_1 + ('c' * re.repeat + 'd') * re.group(2), 'abcd',
        {'_': 'abcd', 1: 'bc', 2: 'd'})
    run('a' + bc_e_r_g_1 + ('c' * re.repeat(min=1) + 'd') * re.group(2),
        'abcd', {'_': 'abcd', 1: 'b', 2: 'cd'})
    run('a' + 'bcd' * re.either * re.repeat + 'dcdcde', 'adcdcde',
        {'_': 'adcdcde'})
    run('a' + 'bcd' * re.either * re.repeat(min=1) + 'dcdcde', 'adcdcde', None)
    run(('ab', 'a') * re.either + b_s + 'c', 'abc', {'_': 'abc'})
    run(re.Group(re.Group('a') + re.Group('b') + re.Group('c')) + re.Group('d'),
        'abcd', {'_': 'abcd'})
    run(re.anything * re.group(1) + 'c' + re.anything * re.group(2), 'abcde',
        {'_': 'abcde', 1: 'ab', 2: 'de'})
    run('k' * re.either, 'ab', None)
    run('a' + '-' * re.maybe + 'c', 'ac', {'_': 'ac'})
    run(re.Either(re.Group('a') + re.Group('b') + 'c', 'ab'), 'ab',
        {'_': 'ab'})
    run('a' * re.group * re.repeat(min=1) + 'x', 'aaax', {'_': 'aaax'})
    run('ac' * re.either * re.group(1) * re.repeat(min=1) + 'x', 'aacx',
        {'_': 'aacx', 1: 'c'})
    run(re.Group('/' * re.exclude * re.repeat + '/', 1) * re.repeat + 'sub1/',
        'd:msgs/tdir/sub1/trial/away.cpp',
        {'_': 'd:msgs/tdir/sub1/', 1: 'tdir/'})
    run(('N' * re.exclude * re.repeat + 'N') * re.group(1) * re.repeat(min=1),
        'abNNxyzN', {'_': 'abNNxyzN', 1: 'xyzN'})
    run(('N' * re.exclude * re.repeat + 'N') * re.group(1) * re.repeat(min=1),
        'abNNxyz', {'_': 'abNN', 1: 'N'})
    run(abc_e * re.repeat * re.group(1) + 'x', 'abcx', {'_': 'abcx', 1: 'abc'})
    run(abc_e * re.repeat * re.group(1) + 'x', 'abc', None)
    run(re.start + 'xyz' * re.either * re.repeat * re.group(1) + 'x', 'abcx',
        {'_': 'abcx', 1: ''})
    run(re.Either(re.Group('a') * re.repeat(min=1) + 'b', 'aac'), 'aac',
        {'_': 'aac'})


def test_not_greedy():
    run('a' + re.anyone * re.repeat(min=1, greedy=False) + 'c', 'abcabc',
        {'_': 'abc'})


def test_something():
    run(re.Either('a' * re.something, 'b') * re.repeat, 'ab', {'_': 'ab'})
    run(re.Either('a' * re.something, 'b') * re.repeat(0,), 'ab', {'_': 'ab'})
    run(re.Either('a' * re.something, 'b') * re.something, 'ab', {'_': 'ab'})
    run(re.Either('a' * re.something, 'b') * re.repeat(1,), 'ab', {'_': 'ab'})
    run(re.Either('a' * re.something, 'b') * re.maybe, 'ab', {'_': 'a'})
    run(re.Either('a' * re.something, 'b') * re.repeat(0, 1), 'ab', {'_': 'a'})
