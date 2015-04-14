"""# PyPatt

"""

from sys import hexversion as _hexversion
from platform import python_implementation as _python_implementation

_cpython = (_python_implementation() == 'CPython')
_cpython2 = (_cpython and 0x02060000 <= _hexversion < 0x02080000)

if _cpython2:
    from .macro import store, transform, uncompile, recompile, PyPattBreak, trybind

from .funcs import match, bind, bound, like

__title__ = 'pypatt'
__version__ = '0.2.0'
__build__ = 0x000200
__author__ = 'Grant Jenks'
__license__ = 'Apache 2.0'
__copyright__ = 'Copyright 2015 Grant Jenks'
