from typing import Union
from .errors import ParseError, SyntaxError
from .token import Token
from .node import Node
from .basic_ast import Ast


class op:
    AND         = 'AND'
    NOT         = 'NOT'
    OR          = 'OR'
    AND_OR      = [AND, OR]
    LOGICAL     = [AND, OR, NOT]
    FREETEXT    = 'FREETEXT'
    FREERGXP    = 'FREERGXP'
    EXISTS      = 'EXISTS'
    MISSING     = 'MISSING'
    UNARY_OPS   = [FREETEXT, FREERGXP, EXISTS, MISSING]
    EQUALS      = 'EQUALS'
    GT          = 'GT'
    GTE         = 'GTE'
    LT          = 'LT'
    LTE         = 'LTE'
    RANGE_OPS   = [GT, GTE, LT, LTE]
    CONTAINS    = 'CONTAINS'
    STARTSWITH  = 'STARTSWITH'
    ENDSWITH    = 'ENDSWITH'
    REGEXP      = 'REGEXP'
    BINARY_OPS  = [EQUALS, GT, GTE, LT, LTE, CONTAINS, STARTSWITH, ENDSWITH, REGEXP]
    REGEX_OPS   = [CONTAINS, STARTSWITH, ENDSWITH, REGEXP]
    INT         = 'INT'
    FLOAT       = 'FLOAT'
    STRING      = 'STRING'
    ARG         = [INT, FLOAT, STRING]
    SEP = '||'


def is_a(x: Union[Node, Token], type_) -> bool:
    if isinstance(type_, list):
        return x.type in type_
    else:
        return x.type == type_


def arg_token_any(s) -> Token:
    try:
        v = int(s)
        return Token(op.INT, v)
    except ValueError:
        pass
    try:
        v = float(s)
        return Token(op.FLOAT, v)
    except ValueError:
        pass

    return Token(op.STRING, s)


def arg_token_string(s) -> Token:
    return Token(op.STRING, s)


class KarpTNGLexer():
    SEPARATOR_1    = '||'
    SEPARATOR_2    = '|'
    logical = {
        'and': op.AND,
        'not': op.NOT,
        'or': op.OR,
    }
    ops = {
        'freetext': op.FREETEXT,
        'freergxp': op.FREERGXP,
        'equals': op.EQUALS,
        'exists': op.EXISTS,
        'missing': op.MISSING,
        'contains': op.CONTAINS,
        'startswith': op.STARTSWITH,
        'endswith': op.ENDSWITH,
        'regexp': op.REGEXP,
        'gt': op.GT,
        'gte': op.GTE,
        'lt': op.LT,
        'lte': op.LTE,
    }
    arg1 = {
        'freetext': arg_token_any,
        'freergxp': arg_token_string,
        'equals': arg_token_string,
        'exists': arg_token_string,
        'missing': arg_token_string,
        'contains': arg_token_string,
        'startswith': arg_token_string,
        'endswith': arg_token_string,
        'regexp': arg_token_string,
        'gt': arg_token_string,
        'gte': arg_token_string,
        'lt': arg_token_string,
        'lte': arg_token_string,
    }
    arg2 = {
        'equals': arg_token_any,
        'contains': arg_token_string,
        'startswith': arg_token_string,
        'endswith': arg_token_string,
        'regexp': arg_token_string,
        'gt': arg_token_any,
        'gte': arg_token_any,
        'lt': arg_token_any,
        'lte': arg_token_any,
    }

    def _tokenize_level_2(self, s: str):
        print('Tokenizing {s}'.format(s=s))
        exprs = s.split(self.SEPARATOR_2)

        if exprs[0] in self.ops:
            yield Token(self.ops[exprs[0]])
            yield self.arg1[exprs[0]](exprs[1])
            arg_2 = self.arg2.get(exprs[0])
            if arg_2:
                if len(exprs) > 2:
                    yield arg_2(exprs[2])
                else:
                    raise SyntaxError(
                        "Too few arguments to '{op}' in '{s}'".format(
                            op=exprs[0],
                            s=s
                        )
                    )
            else:
                if len(exprs) > 2:
                    raise SyntaxError(
                        "Too many arguments to '{op}' in '{s}'".format(
                            op=exprs[0],
                            s=s
                        )
                    )

    def _tokenize(self, s: str):
        exprs = s.split(self.SEPARATOR_1)
        if len(exprs) == 1:
            yield from self._tokenize_level_2(s)
            yield Token(op.SEP)
        else:
            for expr in exprs:
                if expr in ['and','not','or']:
                    yield Token(self.logical[expr])
                else:
                    yield from self._tokenize_level_2(expr)

                yield Token(op.SEP)


    def tokenize(self, s: str):
        print('Tokenizing {s}'.format(s=s))
        yield from self._tokenize(s)


def create_node(tok: Token):
    return Node(tok.type, tok.value)


class KarpTNGParser:
    def parse(self, tokens):
        #root = Node('ROOT')
        root = None
        curr = None
        logical = None
        stack = []
        for tok in tokens:
            if is_a(tok, op.ARG):
                curr.add_child(
                    Node(tok.type, tok.value)
                )
            elif is_a(tok, op.SEP):
                if curr:
                    if stack:
                        n1 = stack.pop()
                        n1.add_child(curr)
                        if is_a(n1, op.NOT):
                            if stack:
                                n2 = stack.pop()
                                n2.add_child(n1)
                                stack.append(n2)
                            else:
                                stack.append(n1)
                        else:
                            stack.append(n1)
                    else:
                        stack.append(curr)
                    curr = None


            elif is_a(tok, op.AND_OR):
                stack.append(create_node(tok))
            elif is_a(tok, op.NOT):
                stack.append(create_node(tok))
            else:
                if curr:
                    raise RuntimeError('')
                curr = create_node(tok)

        root = None
        for node in reversed(stack):
            if root:
                # if is_a(root, op.AND_OR) and is_a(node, op.AND_OR):

                node.add_child(root)
            root = node
        return root


_lexer = KarpTNGLexer()
_parser = KarpTNGParser()


def parse(s: str) -> Ast:
    if not s:
        return Ast()
    return Ast(_parser.parse(_lexer.tokenize(s)))
