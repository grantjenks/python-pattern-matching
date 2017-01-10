from nose.tools import raises

import random
from collections import namedtuple
from patternmatching import match, like, bind, bound, repeat, group, padding

Point = namedtuple('Point', 'x y z t')


def match_basic(value):
    if match(value, None):
        return 'case-1'
    elif match(value, True):
        return 'case-2'
    elif match(value, False):
        return 'case-3'
    elif match(value, -100):
        return 'case-4'
    elif match(value, 1.234):
        return 'case-5'
    elif match(value, 12345678901234567890):
        return 'case-6'
    elif match(value, complex(1, 2)):
        return 'case-7'
    elif match(value, str('alpha')):
        return 'case-8'
    elif match(value, bytes(b'beta')):
        return 'case-9'
    elif match(value, (1, 2, 3, 4)):
        return 'case-15'
    elif match(value, [bind.first, bind.second, bind.third]):
        return 'case-11'
    elif match(value, like('^abc..abc$')):
        return 'case-12'
    elif match(value, like(lambda val: val % 17 == 0)):
        return 'case-13'
    elif match(value, Point(0, 0, 0, 0)):
        return 'case-14'
    elif match(value, [1, 2, 3, 4]):
        return 'case-16'
    elif match(value, (0, [1, (2, [3, (4, [5])])])):
        return 'case-17'
    elif match(value, tuple):
        return 'case-10'
    elif match(value, like(lambda val: val % 19 == 0)):
        return 'case-18'
    elif match(value, object):
        return 'case-19'
    else:
        raise Exception('no match')


def test_basic():
    values = [
        None,
        True,
        False,
        -100,
        1.234,
        12345678901234567890,
        complex(1, 2),
        str('alpha'),
        bytes(b'beta'),
        Point,
        [5, 6, 7],
        'abc01abc',
        119,
        Point(0, 0, 0, 0),
        Point(1, 2, 3, 4),
        [1, 2, 3, 4],
        (0, [1, (2, [3, (4, [5])])]),
        114,
        list,
    ]

    cases = ['case-%s' % (num + 1) for num in range(len(values))]

    results = list(zip(values, cases))

    random.seed(0)

    for _ in range(1000):
        random.shuffle(results)
        for value, result in results:
            assert match_basic(value) == result


@raises(AttributeError)
def test_bind_result():
    if match(0, bind.push):
        return 'zero'
    else:
        return 'nonzero'


def test_bind_any():
    assert match([0, 1, 2], [bind.any, bind.any, bind.any])


def test_bind_repeated():
    assert match((0, 0, 1, 1), (bind.zero, bind.zero, bind.one, bind.one))
    assert not match((0, 1), (bind.value, bind.value))


def test_bound():
    assert match(5, bind.value)
    assert bound.value == 5


def test_bind_repeat():
    assert match([1, 1, 1, 2, 2, 3], 1 * repeat + bind.value * repeat + 3)
    assert bound.value == 2


def test_bind_repeat_alternate():
    pattern = bind.any * repeat + bind.any * group('value') + [2, 1] + bind.any
    assert match([0, 1, 2, 1, 2], pattern)
    assert bound.value == [1]


def test_bind_padding_name():
    pattern = padding + [bind.value, bind.other, bind.value, 3]
    assert match([1, 2, 1, 2, 1, 2, 3], pattern)
    assert bound.value == 2
    assert bound.other == 1


def test_bind_padding_like():
    def odd_num(value):
        return value % 2 and value
    pattern = padding + [like(odd_num, 'value'), like(odd_num, 'other'), like(odd_num, 'value'), 2]
    assert match([3, 5, 3, 5, 3, 5, 2], pattern)
    assert bound.value == 5
    assert bound.other == 3


if __name__ == '__main__':
    import nose
    nose.runmodule()
