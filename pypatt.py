"""
# PyPatt - Python Pattern Matching

## Development

* `uncompile`, `recompile`, and `parse_snippet` based on
  http://code.activestate.com/recipes/578353-code-to-source-and-back/
  Written by Oren Tirosh. Dec 1, 2012. Shared with MIT License.
* An AST pretty-printer can be pretty useful. I had good luck
  with https://pypi.python.org/pypi/astunparse/
"""

import ast, inspect, re
from itertools import count, izip as zip
from functools import partial
from types import CodeType, FunctionType

import __future__
PyCF_MASK = sum(val for key, val in vars(__future__).items()
                if key.startswith('CO_FUTURE'))

def uncompile(cobj):
    if cobj.co_flags & inspect.CO_NESTED or cobj.co_freevars:
        raise RuntimeError('nested functions not supported')
    if cobj.co_name == '<lambda>':
        raise RuntimeError('lambda functions not supported')
    if cobj.co_filename == '<string>':
        raise RuntimeError('code without source file not supported')

    filename = inspect.getfile(cobj)
    lines, firstlineno = inspect.getsourcelines(cobj)
    source = ''.join(lines)

    # Find the mangled name (__X -> _ClassName__X) if present.

    privateprefix = None

    for name in cobj.co_names:
        match = re.match('^(_[A-Za-z0-9][A-Za-z0-9_]*)__.*$', name)
        if match:
            privateprefix = match.group(1)
            break

    flags = cobj.co_flags & PyCF_MASK

    return source, filename, 'exec', flags, firstlineno, privateprefix

def recompile(source, filename, mode, flags=0, lineno=1, prefix=None):

    if isinstance(source, ast.AST):
        root = source
    else:
        root = parse_snippet(source, filename, mode, flags, lineno)

    node = root.body[0]

    if not isinstance(node, ast.FunctionDef):
        raise RuntimeError('expected FunctionDef AST node')

    code = compile(root, filename, mode, flags, True)

    for cobj in code.co_consts:
        if not isinstance(cobj, CodeType):
            continue
        if cobj.co_name == node.name and cobj.co_firstlineno == node.lineno:
            break
    else:
        raise RuntimeError('function code not found')

    # Mangle private names if necessary.

    if prefix is not None:

        is_private = re.compile('^__.*(?<!__)$').match

        def fix_names(names):
            return tuple(
                prefix + name if is_private(name) else name for name in names
            )

        cobj = CodeType(
            cobj.co_argcount,
            cobj.co_nlocals,
            cobj.co_stacksize,
            cobj.co_flags,
            cobj.co_code,
            cobj.co_consts,
            fix_names(cobj.co_names),
            fix_names(cobj.co_varnames),
            cobj.co_filename,
            cobj.co_name,
            cobj.co_firstlineno,
            cobj.co_lnotab,
            cobj.co_freevars,
            cobj.co_cellvars
        )

    return cobj

def parse_snippet(source, filename, mode, flags, firstlineno):
    args = filename, mode, flags | ast.PyCF_ONLY_AST, True

    try:
        code = compile('\n' + source, *args)
    except IndentationError:
        code = compile('with 0:\n' + source, *args)
        code.body = code.body[0].body

    ast.increment_lineno(code, firstlineno - 2)

    return code

store = dict()

class PyPattBreak(Exception):
    pass

def bind(quote, expr, value, globs, locs):
    names = set(QuotedVarsVisitor(quote)(expr))
    bound = {}

    class Mismatch(Exception):
        pass

    def visitor(node, value):
        if isinstance(node, ast.List):
            if isinstance(value, list) and len(value) == len(node.elts):
                return list(visitor(lhs, rhs)
                            for lhs, rhs in zip(node.elts, value))
            else:
                raise Mismatch
        elif isinstance(node, ast.Tuple):
            if isinstance(value, tuple) and len(value) == len(node.elts):
                return tuple(visitor(lhs, rhs)
                             for lhs, rhs in zip(node.elts, value))
            else:
                raise Mismatch
        elif isinstance(node, ast.Num):
            if not isinstance(value, (int, float, long)):
                raise Mismatch
            if value != node.n:
                raise Mismatch
            return value
        elif isinstance(node, ast.Str):
            if not isinstance(value, (str, unicode)):
                raise Mismatch
            if value != node.s:
                raise Mismatch
            return value
        elif isinstance(node, ast.Name):
            if node.id in locs:
                if value != locs[node.id]:
                    raise Mismatch
            elif node.id in globs:
                if value != globs[node.id]:
                    raise Mismatch
            elif node.id in ('True', 'False'):
                if value != (node.id == 'True'):
                    raise Mismatch
            else:
                raise RuntimeError('unknown ast.Name')
            return value
        elif isinstance(node, ast.Call):
            name = is_call_quote(node, quote)
            if not name:
                raise RuntimeError('unknown ast.Call')
            if name in bound:
                if value != bound[name]:
                    raise Mismatch
            else:
                bound[name] = value
            return value
        else:
            raise RuntimeError('unknown ast.Node')

    try:
        result = visitor(expr, value)
        return (result, bound)
    except Mismatch:
        return False

def is_call_quote(node, quote):
    if not isinstance(node.func, ast.Name):
        return False
    if node.func.id != quote:
        return False
    if len(node.args) != 1:
        return False
    if not isinstance(node.args[0], ast.Name):
        return False
    if len(node.keywords):
        return False
    if node.starargs is not None:
        return False
    if node.kwargs is not None:
        return False
    return node.args[0].id

class QuotedVarsVisitor(ast.NodeVisitor):
    def __init__(self, quote):
        self.names = []
        self.quote = quote
    def visit_Call(self, node):
        name = is_call_quote(node, self.quote)
        if name:
            self.names.append(name)
        self.generic_visit(node)
    def __call__(self, node):
        self.visit(node)
        return self.names

def is_with_match(node, match):
    expr = node.context_expr
    if not isinstance(expr, ast.Call):
        return False
    if not isinstance(expr.func, ast.Name):
        return False
    if expr.func.id != match:
        return False
    if len(expr.args) != 1:
        return False
    if len(expr.keywords):
        return False
    if expr.starargs is not None:
        return False
    if expr.kwargs is not None:
        return False
    return expr.args[0]

class MatchTransformVisitor(ast.NodeTransformer):
    def __init__(self, match='match', quote='quote', module='pypatt'):
        self.count = count()
        self.module = module
        self.match = match
        self.quote = quote

    def temp_name(self):
        return 'pypatt_temp_' + str(next(self.count))

    def visit_With(self, node):
        expr = is_with_match(node, self.match)

        if expr is False:
            return self.generic_visit(node)

        if not all(isinstance(subnode, ast.With)
                   and is_with_match(subnode, self.match) is False
                   for subnode in node.body):
            msg = (
                'statements in `with {0}(...) ...` must all'
                ' be `with` statements'
            )
            raise RuntimeError(msg.format(self.match))

        stmt = ast.parse(
            'try:\n    pass\nexcept {module}.PyPattBreak:\n    pass'.format(
                module=self.module
            )
        ).body[0]
        del stmt.body[0]

        temp_match = self.temp_name()

        assign_expr = ast.Assign(
            targets=[ast.Name(id=temp_match, ctx=ast.Store())],
            value=expr
        )

        stmt.body.append(assign_expr)

        if node.optional_vars:
            stmt.body.append(ast.parse(
                '{name} = {temp_match}'.format(
                    name=node.optional_vars.id,
                    temp_match=temp_match,
                )
            ).body[0])

        for with_stmt in node.body:
            temp_ast = self.temp_name()
            temp_store = self.temp_name()
            with_expr = with_stmt.context_expr

            store[temp_store] = with_expr

            stmt.body.append(ast.parse(
                '{temp_ast} = {module}.store["{temp_store}"]'.format(
                    temp_ast=temp_ast,
                    module=self.module,
                    temp_store=temp_store
                )
            ).body[0])

            temp_vars = self.temp_name()

            stmt.body.append(ast.parse(
                ('{temp_vars} = {module}.bind("{quote}", '
                 '{temp_ast}, {temp_match}, globals(), locals())').format(
                     quote=self.quote,
                     temp_vars=temp_vars,
                     module=self.module,
                     temp_match=temp_match,
                     temp_ast=temp_ast
                 )
            ).body[0])

            if_stmt = ast.If(
                test=ast.Name(id=temp_vars, ctx=ast.Load()),
                body=[], orelse=[]
            )

            stmt.body.append(if_stmt)

            if with_stmt.optional_vars:
                if_stmt.body.append(ast.parse(
                    '{name} = {temp_vars}[0]'.format(
                        name=with_stmt.optional_vars.id,
                        temp_vars=temp_vars
                    )
                ).body[0])

            quoted_vars = QuotedVarsVisitor(self.quote)(with_expr)

            for var in quoted_vars:
                if_stmt.body.append(ast.parse(
                    '{var} = {temp_vars}[1]["{var}"]'.format(
                        var=var,
                        temp_vars=temp_vars
                    )
                ).body[0])

            if_stmt.body.extend(self.visit(temp) for temp in with_stmt.body)

            if_stmt.body.append(ast.parse(
                'raise {module}.PyPattBreak'.format(module=self.module)
            ).body[0])

        return stmt

def transform(func=None, visitor=MatchTransformVisitor, **kwargs):
    if func is None:
        return partial(transform, visitor=visitor, **kwargs)
    else:
        parts = list(uncompile(func.func_code))
        root = parse_snippet(*parts[:-1])
        root = visitor(**kwargs).visit(root)
        ast.fix_missing_locations(root)
        parts[0] = root
        func.func_code = recompile(*parts)
        return func
