from nose.tools import raises

import random
from collections import namedtuple
from pypatt.experimental import match, like, bind, bound

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
    elif match(value, bytes('beta')):
        return 'case-9'
    elif match(value, tuple):
        return 'case-10'
    elif match(value, [bind.first, bind.second, bind.third]):
        return 'case-11'
    elif match(value, like('^abc..abc$')):
        return 'case-12'
    elif match(value, like(lambda val: val % 17 == 0)):
        return 'case-13'
    elif match(value, Point(0, 0, 0, 0)):
        return 'case-14'
    elif match(value, (1, 2, 3, 4)):
        return 'case-15'
    elif match(value, [1, 2, 3, 4]):
        return 'case-16'
    elif match(value, (0, [1, (2, [3, (4, [5])])])):
        return 'case-17'
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
        bytes('beta'),
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

    cases = ['case-' + str(num + 1) for num in range(len(values))]

    results = zip(values, cases)

    random.seed(0)

    for _ in range(1000):
        random.shuffle(results)
        for value, result in results:
            assert match_basic(value) == result

@raises(AttributeError)
def test_bind_result():
    if match(0, bind.result):
        return 'zero'
    else:
        return 'nonzero'

def test_bind_any():
    assert match([0, 1, 2], [bind.any, bind.any, bind.any])

def test_bind_repeated():
    assert match((0, 0, 1, 1), (bind.zero, bind.zero, bind.one, bind.one))
    assert not match((0, 1), (bind.value, bind.value))

def test_bound():
    match(5, bind.value)
    assert bound.value == 5

if __name__ == '__main__':
    import nose
    nose.runmodule()
