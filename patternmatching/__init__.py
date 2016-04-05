"""Python Pattern Matching

Python pattern matching library.

"""

from sys import hexversion as _hexversion
from platform import python_implementation as _python_implementation

_cpython2 = (_python_implementation() == 'CPython'
             and 0x02060000 <= _hexversion < 0x02080000)

if _cpython2:
    from .macro import (
        store, transform, uncompile, recompile, PatternMatchingBreak, trybind,
    )

from .funcs import match, bind, bound, like

__title__ = 'PatternMatching'
__version__ = '2.0.0'
__build__ = 0x020000
__author__ = 'Grant Jenks'
__license__ = 'Apache 2.0'
__copyright__ = 'Copyright 2015-2016 Grant Jenks'