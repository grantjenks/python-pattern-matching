# coding: pypatt

"""
# Test Basic Functionality

## Output

<code>
one
2 3
4 5
[6, 7]
correct
correct
</code>
"""

values = [
    1,
    [True, 2, 3, 4],
    [(4, 5), 'hello', 6],
    [6, 7],
]

for value in values:
    match value:
        like 1:
            print 'one'
        like [True, var1, var2, 4]:
            print var1, var2
        like [(pos, name), 'hello', 6]:
            print pos, name
        like _:
            print _
            match [1, True, '3', 4]:
                like [1, False, '3', val]:
                    print 'wrong'
                like _:
                    print 'correct'

match [1, True, '3', 4]:
    like [1, False, '3', val]:
        print 'wrong'
    like _:
        print 'correct'
