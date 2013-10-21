# coding: pypatt

# Test Basic Functionality

import nose

values = [
    1,
    [True, 2, 3, 4],
    [(4, 5), 'hello', 6],
    [6, 7],
]

answers = [
    'one',
    (2, 3),
    (4, 5),
    [6, 7],
    'correct',
    'correct'
]

def make_matches():
    for value in values:
        match value:
            like 1:
                yield 'one'
            like [True, var1, var2, 4]:
                yield var1, var2
            like [(pos, name), 'hello', 6]:
                yield pos, name
            like _:
                yield _
                match [1, True, '3', 4]:
                    like [1, False, '3', val]:
                        yield 'wrong'
                    like _:
                        yield 'correct'
    match [1, True, '3', 4]:
        like [1, False, '3', val]:
            yield 'wrong'
        like _:
            yield 'correct'

def test_basic():
    for value, answer in zip(make_matches(), answers):
        assert value == answer

if __name__ == '__main__':
    nose.run()
