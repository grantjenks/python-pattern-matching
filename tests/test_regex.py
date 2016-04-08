"""Regular expression module tests.

A large number of these were ported from:
https://github.com/python/cpython/blob/master/Lib/test/re_tests.py

"""

import patternmatching.regex as re


def test_basic():
    assert re.match('', '') == {'_': ''}
    assert re.match('abc', 'abc') == {'_': 'abc'}
    assert re.match('abc', 'xbc') is None
    assert re.match('abc', 'axc') is None
    assert re.match('abc', 'abx') is None
    assert re.match('abc', 'xabc') is None
    assert re.match('abc', 'xabcy') is None
    assert re.match('abc', '') is None


def test_groups():
    assert re.match(re.group('a', 'foo'), 'a') == {'_': 'a', 'foo': 'a'}
    assert re.match(re.group('a', 'foo'), 'aa') == {'_': 'a', 'foo': 'a'}


def test_anyone():
    assert re.match('a' + re.anyone + 'c', 'abc') == {'_': 'abc'}
    assert re.match('a' + re.anyone * re.repeat + 'c', 'axyzc') == {'_': 'axyzc'}
    assert re.match('a' + re.anyone * re.repeat + 'c', 'axyzd') is None
    assert re.match('a' + re.anyone * re.repeat + 'c', 'ac') == {'_': 'ac'}
    assert re.match('a' + re.anyone * re.repeat(2, 3) + 'c', 'abbc') == {'_': 'abbc'}


def test_repeat():
    assert re.match('a' + 'b' * re.repeat + 'c', 'abc') == {'_': 'abc'}
    assert re.match('a' + 'b' * re.repeat + 'bc', 'abc') == {'_': 'abc'}
    assert re.match('a' + 'b' * re.repeat + 'bc', 'abbc') == {'_': 'abbc'}
    assert re.match('a' + 'b' * re.repeat + 'bc', 'abbbbc') == {'_': 'abbbbc'}


def test_some():
    some = re.repeat(min=1)

    assert re.match('a' + 'b' * some + 'bc', 'abbc') == {'_': 'abbc'}
    assert re.match('a' + 'b' * some + 'bc', 'abc') is None
    assert re.match('a' + 'b' * some + 'bc', 'abq') is None
    assert re.match('a' + 'b' * some + 'bc', 'abbbbc') == {'_': 'abbbbc'}


def test_maybe():
    assert re.match(re.maybe('a'), '') == {'_': ''}
    assert re.match(re.maybe('a'), 'a') == {'_': 'a'}
    assert re.match(re.maybe('a'), 'aa') == {'_': 'a'}
    assert re.match('a' + re.maybe('a'), 'aa') == {'_': 'aa'}
    assert re.match('a' + re.anyone + 'c' + re.maybe('d'), 'abc') == {'_': 'abc'}

"""
# TODO: Add these tests:

    ('ab?bc', 'abbc', SUCCEED, 'found', 'abbc'),
    ('ab?bc', 'abc', SUCCEED, 'found', 'abc'),
    ('ab?bc', 'abbbbc', FAIL),
    ('ab?c', 'abc', SUCCEED, 'found', 'abc'),

    ('a[bc]d', 'abc', FAIL),
    ('a[bc]d', 'abd', SUCCEED, 'found', 'abd'),

    ('a[^bc]d', 'aed', SUCCEED, 'found', 'aed'),
    ('a[^bc]d', 'abd', FAIL),

    ('ab|cd', 'abc', SUCCEED, 'found', 'ab'),
    ('ab|cd', 'abcd', SUCCEED, 'found', 'ab'),

    ('((a))', 'abc', SUCCEED, 'found+"-"+g1+"-"+g2', 'a-a-a'),
    ('(((((((((a)))))))))', 'a', SUCCEED, 'found', 'a'),
    ('(a)b(c)', 'abc', SUCCEED, 'found+"-"+g1+"-"+g2', 'abc-a-c'),

    ('a+b+c', 'aabbabc', SUCCEED, 'found', 'abc'),

    ('(a+|b)*', 'ab', SUCCEED, 'found+"-"+g1', 'ab-b'),
    ('(a+|b)+', 'ab', SUCCEED, 'found+"-"+g1', 'ab-b'),
    ('(a+|b)?', 'ab', SUCCEED, 'found+"-"+g1', 'a-a'),

    ('[^ab]*', 'cde', SUCCEED, 'found', 'cde'),

    ('a*', '', SUCCEED, 'found', ''),
    ('a|b|c|d|e', 'e', SUCCEED, 'found', 'e'),
    ('(a|b|c|d|e)f', 'ef', SUCCEED, 'found+"-"+g1', 'ef-e'),

    ('(ab|cd)e', 'abcde', SUCCEED, 'found+"-"+g1', 'cde-cd'),
    ('[abhgefdc]ij', 'hij', SUCCEED, 'found', 'hij'),
    ('(a|b)c*d', 'abcd', SUCCEED, 'found+"-"+g1', 'bcd-b'),
    ('(ab|ab*)bc', 'abc', SUCCEED, 'found+"-"+g1', 'abc-a'),
    ('a([bc]*)c*', 'abc', SUCCEED, 'found+"-"+g1', 'abc-bc'),
    ('a([bc]*)(c*d)', 'abcd', SUCCEED, 'found+"-"+g1+"-"+g2', 'abcd-bc-d'),
    ('a([bc]+)(c*d)', 'abcd', SUCCEED, 'found+"-"+g1+"-"+g2', 'abcd-bc-d'),
    ('a([bc]*)(c+d)', 'abcd', SUCCEED, 'found+"-"+g1+"-"+g2', 'abcd-b-cd'),
    ('a[bcd]*dcdcde', 'adcdcde', SUCCEED, 'found', 'adcdcde'),
    ('a[bcd]+dcdcde', 'adcdcde', FAIL),
    ('(ab|a)b*c', 'abc', SUCCEED, 'found+"-"+g1', 'abc-ab'),
    ('((a)(b)c)(d)', 'abcd', SUCCEED, 'g1+"-"+g2+"-"+g3+"-"+g4', 'abc-a-b-d'),
    ('multiple words of text', 'uh-uh', FAIL),
    ('multiple words', 'multiple words, yeah', SUCCEED, 'found', 'multiple words'),
    ('(.*)c(.*)', 'abcde', SUCCEED, 'found+"-"+g1+"-"+g2', 'abcde-ab-de'),
    ('[k]', 'ab', FAIL),
    ('a[-]?c', 'ac', SUCCEED, 'found', 'ac'),
    ('(a)(b)c|ab', 'ab', SUCCEED, 'found+"-"+g1+"-"+g2', 'ab-None-None'),
    ('(a)+x', 'aaax', SUCCEED, 'found+"-"+g1', 'aaax-a'),
    ('([ac])+x', 'aacx', SUCCEED, 'found+"-"+g1', 'aacx-c'),
    ('([^/]*/)*sub1/', 'd:msgs/tdir/sub1/trial/away.cpp', SUCCEED, 'found+"-"+g1', 'd:msgs/tdir/sub1/-tdir/'),
    ('([^N]*N)+', 'abNNxyzN', SUCCEED, 'found+"-"+g1', 'abNNxyzN-xyzN'),
    ('([^N]*N)+', 'abNNxyz', SUCCEED, 'found+"-"+g1', 'abNN-N'),
    ('([abc]*)x', 'abcx', SUCCEED, 'found+"-"+g1', 'abcx-abc'),
    ('([abc]*)x', 'abc', FAIL),
    ('([xyz]*)x', 'abcx', SUCCEED, 'found+"-"+g1', 'x-'),
    ('(a)+b|aac', 'aac', SUCCEED, 'found+"-"+g1', 'aac-None'),

    ('ab{1,}bc', 'abbbbc', SUCCEED, 'found', 'abbbbc'),
    ('ab{1,3}bc', 'abbbbc', SUCCEED, 'found', 'abbbbc'),
    ('ab{3,4}bc', 'abbbbc', SUCCEED, 'found', 'abbbbc'),
    ('ab{4,5}bc', 'abbbbc', FAIL),

    ('ab?bc', 'abbc', SUCCEED, 'found', 'abbc'),
    ('ab?bc', 'abc', SUCCEED, 'found', 'abc'),
    ('ab{0,1}bc', 'abc', SUCCEED, 'found', 'abc'),
    ('ab?bc', 'abbbbc', FAIL),
    ('ab?c', 'abc', SUCCEED, 'found', 'abc'),
    ('ab{0,1}c', 'abc', SUCCEED, 'found', 'abc'),

    ('a.+?c', 'abcabc', SUCCEED, 'found', 'abc'),
    ('(a+|b)*', 'ab', SUCCEED, 'found+"-"+g1', 'ab-b'),
    ('(a+|b){0,}', 'ab', SUCCEED, 'found+"-"+g1', 'ab-b'),
    ('(a+|b)+', 'ab', SUCCEED, 'found+"-"+g1', 'ab-b'),
    ('(a+|b){1,}', 'ab', SUCCEED, 'found+"-"+g1', 'ab-b'),
    ('(a+|b)?', 'ab', SUCCEED, 'found+"-"+g1', 'a-a'),
    ('(a+|b){0,1}', 'ab', SUCCEED, 'found+"-"+g1', 'a-a'),

    ('a*', '', SUCCEED, 'found', ''),
    ('([abc])*d', 'abbbcd', SUCCEED, 'found+"-"+g1', 'abbbcd-c'),
    ('([abc])*bcd', 'abcd', SUCCEED, 'found+"-"+g1', 'abcd-a'),
    ('[abhgefdc]ij', 'hij', SUCCEED, 'found', 'hij'),

"""
