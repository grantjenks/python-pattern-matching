# Test Basic Functionality

import pypatt

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

@pypatt.transform
def make_matches():
    for value in values:
        with match(value):
            with 1:
                yield 'one'
            with [True, var1, var2, 4]:
                yield var1, var2
            with [(pos, name), 'hello', 6]:
                yield pos, name
            with _:
                yield _
                with match([1, True, '3', 4]):
                    with [1, False, '3', val]:
                        yield 'wrong'
                    with _:
                        yield 'correct'
    with match([1, True, '3', 4]):
        with [1, False, '3', val]:
            yield 'wrong'
        with _:
            yield 'correct'

def test_basic():
    for value, answer in zip(make_matches(), answers):
        assert value == answer

class Logger(object):
    @pypatt.transform(match='foo_match')
    def log(self, message):
        with foo_match(type(message)) as tipe:

            with int:
                message += 1
                print 'saw int', message

            with _:
                message += '!'
                print 'saw msg', message

def test_indent():
    logger = Logger()
    logger.log(5)
    logger.log('help!')

if __name__ == '__main__':
    test_basic()
    test_indent()
