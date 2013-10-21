# coding: pypatt

# Test Binding the Same Variable

import nose

def make_match():
    match [1, 2, 3, 1, 4]:
        like [temp, 2, 3, 1, temp]:
            return 'fail'
        like [temp, 2, 3, temp, 4]:
            return 'pass'

def test_bind():
    assert make_match() == 'pass'

if __name__ == '__main__':
    nose.run()
