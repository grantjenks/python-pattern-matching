"""
# Codec

## Before

match <match_expr> as name:
    like <like_expr1>:
        <like_body1>

## After

__patt_temp = <match_expr>
try:
    __patt_expr = lambda: <like_expr1>
    __patt_vars = bind(__patt_temp, __patt_expr, globals(), locals())
    if __patt_vars:
        if len(__patt_vars[0]) == 1:
            eval('{0} = __patt_vars[1][0]'.format(__patt_vars[0][0]))
        elif len(__patt_vars[0]) > 1:
            eval('{0} = __patt_vars[1]'.format(', '.join(__patt_vars[0])))
        <like_body1>
        raise BreakException
...
except BreakException:
    pass
except:
    raise
"""

import logging

# Change WARNING to DEBUG for a trace.

logging.basicConfig(level=logging.WARNING)

import tokenize
import codecs, encodings

try:
    import cStringIO as StringIO
except:
    logging.info('cStringIO not found')
    import StringIO

from encodings import utf_8

def tokstr(value):
    return list(tokenize.generate_tokens(StringIO.StringIO(value).readline))[:-1]

def translate(readline):
    logging.debug('START TRANSLATE')

    uniq = 0

    def match():
        return next(tup[2] for tup in reversed(stack) if tup[0] == 'match')

    def like():
        return 1 + match()

    try:
        tokens = list(tokenize.generate_tokens(readline))

        logging.debug('START TOKENS')
        for token in tokens:
            logging.debug(token)
        logging.debug('END TOKENS')

        # index maintains our position in the tokens list. Eventually this
        # should just consume on-demand from the generator.

        index = 0

        # stack maintains the indentation level

        stack = [('skip', '')]

        # pypatt custom imports

        for tok in tokstr('from pypatt import __patt_BreakException, __patt_bind\n'): yield tok

        while index < len(tokens):
            toknum, tokval, _, _, _ = tokens[index]

            if toknum == tokenize.NAME and tokval == 'match':

                # Consume the expression up to the colon.

                expr = []
                while True:
                    index += 1
                    if index >= len(tokens):
                        break
                    tup = tokens[index]
                    if tup[0] == tokenize.OP and tup[1] == ':':
                        break
                    else:
                        expr.append(tup)

                assert tokens[index][1] == ':'
                assert tokens[index + 1][0] == tokenize.NEWLINE
                assert tokens[index + 2][0] == tokenize.INDENT

                for tok in tokstr('__patt_temp{0} ='.format(uniq)): yield tok
                for tup in expr: yield tup
                yield tokenize.NEWLINE, '\n'

                for tok in tokstr('try:'): yield tok
                yield tokenize.NEWLINE, '\n'

                index += 2
                stack.append(('match', tokens[index][1], uniq))
                yield tokenize.INDENT, tokens[index][1]
                uniq += 1

            elif toknum == tokenize.NAME and tokval == 'like':

                # Consume the expression up to the colon.

                expr = []
                while True:
                    index += 1
                    if index >= len(tokens):
                        break
                    tup = tokens[index]
                    if tup[0] == tokenize.OP and tup[1] == ':':
                        break
                    else:
                        expr.append(tup)

                assert tokens[index][1] == ':'
                assert tokens[index + 1][0] == tokenize.NEWLINE
                assert tokens[index + 2][0] == tokenize.INDENT
    
                # Insert the binder call.

                for tok in tokstr('__patt_vars{0} = __patt_bind'.format(like())): yield tok
                yield tokenize.OP, '('
                yield tokenize.NAME, '__patt_temp{0}'.format(match())
                yield tokenize.OP, ','
                yield tokenize.STRING, '"""' + ' '.join(tup[1] for tup in expr) + '"""'
                yield tokenize.OP, ','
                for tok in tokstr('globals(), locals()'): yield tok
                yield tokenize.OP, ')'
                yield tokenize.NEWLINE, '\n'
    
                # Check whether we were able to bind the expression.
    
                for tok in tokstr('if __patt_vars{0} :\n'.format(like())): yield tok
    
                # Record the indent and eat the token.
    
                index += 2
                stack.append(('like', tokens[index][1]))
                yield tokenize.INDENT, tokens[index][1]
    
                # Use exec to introduce locals as necessary from a successful
                # binder call.

                for tok in tokstr("if len(__patt_vars{0}[0]) == 1: exec('{{0}} = __patt_vars{0}[1][0]'.format(__patt_vars{0}[0][0]))\n".format(like())): yield tok
                for tok in tokstr("if len(__patt_vars{0}[0]) > 1: exec('{{0}} = __patt_vars{0}[1]'.format(', '.join(__patt_vars{0}[0])))\n".format(like())): yield tok

            elif toknum == tokenize.INDENT:

                logging.debug('Processing INDENT. Stack:')
                for temp in stack:
                    logging.debug(temp)

                yield toknum, tokval
                stack.append(('skip', tokval))

            elif toknum == tokenize.DEDENT:

                # Indentation after 'match' and 'like' statements requires
                # inserting coding at the end of the '__body__'. The DEDENT
                # token shows us where based on the 'kind'.

                logging.debug('Processing DEDENT. Stack:')
                for temp in stack:
                    logging.debug(temp)

                kind, level = stack.pop()[:2]

                if kind == 'match':
                    yield tokenize.DEDENT, ''
                    for tok in tokstr('except __patt_BreakException:\n'): yield tok
                    yield tokenize.INDENT, level + '    '
                    for tok in tokstr('pass\n'): yield tok
                    yield tokenize.DEDENT, ''
                    for tok in tokstr('except:\n'): yield tok
                    yield tokenize.INDENT, level + '    '
                    for tok in tokstr('raise\n'): yield tok
                    yield tokenize.DEDENT, ''
                elif kind == 'like':
                    for tok in tokstr('raise __patt_BreakException\n'): yield tok
                    yield tokenize.DEDENT, ''
                else:
                    assert kind == 'skip'
                    yield tokenize.DEDENT, ''
            else:

                yield toknum, tokval

            index += 1
    except Exception as exc:
        import sys, traceback
        print traceback.format_exc()
        print sys.exc_info()[0]

class StreamReader(utf_8.StreamReader):
    def __init__(self, *args, **kwargs):
        codecs.StreamReader.__init__(self, *args, **kwargs)
        data = tokenize.untokenize(translate(self.stream.readline))
        logging.debug('START RESULT')
        logging.debug(data)
        logging.debug('END RESULT')
        self.stream = StringIO.StringIO(data)

def processor(coding):
    if coding != 'pypatt':
        return None

    logging.debug('CODING: PYPATT')

    utf8 = encodings.search_function('utf8')

    return codecs.CodecInfo(
        name = 'pypatt',
        encode = utf8.encode,
        decode = utf8.decode,
        incrementalencoder = utf8.incrementalencoder,
        incrementaldecoder = utf8.incrementaldecoder,
        streamreader = StreamReader,
        streamwriter = utf8.streamwriter)

codecs.register(processor)

if __name__ == '__main__':
    import fileinput
    print tokenize.untokenize(
        translate(iter(fileinput.input()).next))
