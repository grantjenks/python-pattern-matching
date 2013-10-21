# coding: pypatt

# Test Binding the Same Variable

import nose

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

if __name__ == '__main__':
    nose.run()
