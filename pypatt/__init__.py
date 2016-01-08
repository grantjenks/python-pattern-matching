"""# PyPatt - Python Pattern Matching

"""

from sys import hexversion as _hexversion
from platform import python_implementation as _python_implementation

_cpython = (_python_implementation() == 'CPython')
_cpython2 = (_cpython and 0x02060000 <= _hexversion < 0x02080000)

if _cpython2:
    from .macro import store, transform, uncompile, recompile, PyPattBreak, trybind

from .funcs import match, bind, bound, like

__title__ = 'PyPatt'
__version__ = '1.3.1'
__build__ = 0x010301
__author__ = 'Grant Jenks'
__license__ = 'Apache 2.0'
__copyright__ = 'Copyright 2015-2016 Grant Jenks'
