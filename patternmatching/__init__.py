"""Python Pattern Matching

Python pattern matching library.

"""

from .funcs import *

__all__ = [
    'Matcher', 'match',
    'Name', 'Binder', 'bind', 'Bounder', 'bound',
    'Like', 'like', 'like_errors',
    'literal_types',
    'Anyone', 'anyone',
    'Pattern', 'Exclude', 'exclude', 'Either', 'either', 'Group', 'group',
    'Repeat', 'repeat', 'maybe', 'anything', 'something', 'padding',
]

from sys import hexversion
from platform import python_implementation as py_impl

CPY2 = (py_impl() == 'CPython' and 0x02060000 <= hexversion < 0x02080000)

if CPY2:
    from .macro import *
    __all__.extend([
        'CPY2', 'PatternMatchingBreak', 'recompile', 'store', 'transform',
        'trybind', 'uncompile',
    ])

__title__ = 'PatternMatching'
__version__ = '2.0.0'
__build__ = 0x020000
__author__ = 'Grant Jenks'
__license__ = 'Apache 2.0'
__copyright__ = 'Copyright 2015-2016 Grant Jenks'
