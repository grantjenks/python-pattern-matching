import pypatt

values = [
    1,
    [True, 2, 3, 4.5e3],
    [(4, 5), 'hello', 6],
    [6, 7],
]

answers = [
    'one',
    (2, 3),
    (4, 5),
    [6, 7],
]

@pypatt.transform
def make_matches():
    for value in values:
        with match(value):
            with 1 as temp:
                yield 'one'
            with [True, quote(var1), quote(var2), 4.5e3]:
                yield var1, var2
            with [(quote(pos), quote(name)), 'hello', 6]:
                yield pos, name
            with quote(_):
                yield _

def test_basic():
    matches = list(make_matches())

    assert len(matches) == 4

    for value, answer in zip(matches, answers):
        assert value == answer

if __name__ == '__main__':
    test_basic()
