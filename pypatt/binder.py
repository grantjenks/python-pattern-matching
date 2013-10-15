"""
# Binder

* Only 'True'/'False' match booleans.
* '_' matches anything even if already defined in locals or globals.
"""

import ast
import inspect

from ast import List as astList
from ast import Num as astNum
from ast import Name as astName
from ast import Str as astStr
from ast import Tuple as astTuple

from itertools import izip_longest
from collections import OrderedDict

from pprint import pprint

class CollectNames(ast.NodeVisitor):
    def __init__(self, globs, locs):
        self.names = []
        self.globs = globs
        self.locs = locs
    def visit_Name(self, node):
        if (node.id == '_'
            or (node.id not in self.globs
                and node.id not in self.locs
                and node.id not in ('True', 'False'))):
            self.names.append(node.id)

class MismatchException(Exception):
    pass

def __patt_bind(value, lexpr, globs, locs):
    tree = ast.parse(lexpr, '', 'eval')
    body = tree.body

    collector = CollectNames(globs, locs)
    collector.visit(body)
    names = collector.names

    bound = OrderedDict()

    def helper(node, value):
        if isinstance(node, astList):
            if isinstance(value, list):
                items = izip_longest(node.elts, value, fillvalue=None)
                for item in items:
                    helper(item[0], item[1])
            else:
                raise MismatchException
        elif isinstance(node, astTuple):
            if isinstance(value, tuple):
                items = izip_longest(node.elts, value, fillvalue=None)
                for item in items:
                    helper(item[0], item[1])
            else:
                raise MismatchException
        elif isinstance(node, astNum):
            if isinstance(value, (int, float, long)):
                if node.n != value:
                    raise MismatchException
            else:
                raise MismatchException
        elif isinstance(node, astStr):
            if isinstance(value, str):
                if node.s != value:
                    raise MismatchException
            else:
                raise MismatchException
        elif isinstance(node, astName) and node.id == '_':
            bound[node.id] = value
        elif isinstance(node, astName) and node.id in locs:
            if locs[node.id] != value:
                raise MismatchException
        elif isinstance(node, astName) and node.id in globs:
            if globs[node.id] != value:
                raise MismatchException
        elif isinstance(node, astName) and node.id in ('True', 'False'):
            if isinstance(value, bool):
                if node.id != str(value):
                    raise MismatchException
            else:
                raise MismatchException
        elif isinstance(node, astName):
            bound[node.id] = value
        else:
            raise Exception('illegal list expression')

    try:
        helper(body, value)
        # print 'names', names
        # print 'bound', bound
        return (tuple(names), tuple(bound[name] for name in names))
    except MismatchException:
        return None

bind = __patt_bind
