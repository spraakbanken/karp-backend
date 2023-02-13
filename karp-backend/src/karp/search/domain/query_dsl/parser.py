from typing import Optional, Union

from .basic_ast import Ast
from .errors import ParseError, SyntaxError
from .node import Node, create_binary_node, create_unary_node
from .token import Token


class op:
    AND = "AND"  # noqa: E221
    NOT = "NOT"  # noqa: E221
    OR = "OR"  # noqa: E221
    AND_OR = [AND, OR]  # noqa: E221
    LOGICAL = [AND, OR, NOT]  # noqa: E221
    ARG_AND = "ARG_AND"  # noqa: E221
    ARG_OR = "ARG_OR"  # noqa: E221
    ARG_NOT = "ARG_NOT"  # noqa: E221
    ARG_LOGICAL = [ARG_AND, ARG_OR, ARG_NOT]  # noqa: E221
    FREETEXT = "FREETEXT"  # noqa: E221
    FREERGXP = "FREERGXP"  # noqa: E221
    EXISTS = "EXISTS"  # noqa: E221
    MISSING = "MISSING"  # noqa: E221
    UNARY_OPS = [FREETEXT, FREERGXP, EXISTS, MISSING]  # noqa: E221
    EQUALS = "EQUALS"  # noqa: E221
    GT = "GT"  # noqa: E221
    GTE = "GTE"  # noqa: E221
    LT = "LT"  # noqa: E221
    LTE = "LTE"  # noqa: E221
    RANGE_OPS = [GT, GTE, LT, LTE]  # noqa: E221
    CONTAINS = "CONTAINS"  # noqa: E221
    STARTSWITH = "STARTSWITH"  # noqa: E221
    ENDSWITH = "ENDSWITH"  # noqa: E221
    REGEXP = "REGEXP"  # noqa: E221
    BINARY_OPS = [
        EQUALS,
        GT,
        GTE,
        LT,
        LTE,
        CONTAINS,
        STARTSWITH,
        ENDSWITH,
        REGEXP,
    ]  # noqa: E221
    REGEX_OPS = [CONTAINS, STARTSWITH, ENDSWITH, REGEXP]  # noqa: E221
    OPS = [  # noqa: E221
        CONTAINS,
        ENDSWITH,
        EQUALS,
        EXISTS,
        FREERGXP,
        FREETEXT,
        GT,
        GTE,
        LT,
        LTE,
        MISSING,
        REGEXP,
        STARTSWITH,
    ]
    INT = "INT"  # noqa: E221
    FLOAT = "FLOAT"  # noqa: E221
    STRING = "STRING"  # noqa: E221
    ARGS = [INT, FLOAT, STRING]  # noqa: E221
    SEP = "||"  # noqa: E221


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


class KarpTNGLexer:
    SEPARATOR_1 = "||"  # noqa: E221
    SEPARATOR_2 = "|"  # noqa: E221
    logical = {
        "and": op.AND,
        "not": op.NOT,
        "or": op.OR,
    }
    arg_logical = {
        "and": op.ARG_AND,
        "or": op.ARG_OR,
        "not": op.ARG_NOT,
    }
    ops = {
        "freetext": op.FREETEXT,
        "freergxp": op.FREERGXP,
        "equals": op.EQUALS,
        "exists": op.EXISTS,
        "missing": op.MISSING,
        "contains": op.CONTAINS,
        "startswith": op.STARTSWITH,
        "endswith": op.ENDSWITH,
        "regexp": op.REGEXP,
        "gt": op.GT,
        "gte": op.GTE,
        "lt": op.LT,
        "lte": op.LTE,
    }
    arg1 = {
        "freetext": arg_token_any,
        "freergxp": arg_token_string,
        "equals": arg_token_string,
        "exists": arg_token_string,
        "missing": arg_token_string,
        "contains": arg_token_string,
        "startswith": arg_token_string,
        "endswith": arg_token_string,
        "regexp": arg_token_string,
        "gt": arg_token_string,
        "gte": arg_token_string,
        "lt": arg_token_string,
        "lte": arg_token_string,
    }
    arg2 = {
        "equals": arg_token_any,
        "contains": arg_token_string,
        "startswith": arg_token_string,
        "endswith": arg_token_string,
        "regexp": arg_token_string,
        "gt": arg_token_any,
        "gte": arg_token_any,
        "lt": arg_token_any,
        "lte": arg_token_any,
    }

    def tokenize(self, s: str):
        print("Tokenizing {s}".format(s=s))
        exprs = s.split(self.SEPARATOR_1)
        arg_types = []
        for expr in exprs:
            logical_type = self.logical.get(expr)
            if logical_type:
                yield Token(logical_type)
            else:
                print("Tokenizing {expr}".format(expr=expr))
                sub_exprs = expr.split(self.SEPARATOR_2)

                if sub_exprs[0] in self.ops:
                    yield Token(self.ops[sub_exprs[0]])
                    arg_1 = self.arg1[sub_exprs[0]]
                    arg_2 = self.arg2.get(sub_exprs[0])
                    if len(sub_exprs) > 1:
                        yield arg_1(sub_exprs[1])
                        arg_1 = None
                        if len(sub_exprs) > 2:
                            if arg_2:
                                yield arg_2(sub_exprs[2])
                                arg_2 = None
                            else:
                                raise SyntaxError(
                                    "Too many arguments to '{op}' in '{expr}'".format(
                                        op=sub_exprs[0], expr=expr
                                    )
                                )
                    if arg_2:
                        arg_types.append(arg_2)
                    if arg_1:
                        arg_types.append(arg_1)
                else:
                    if sub_exprs[0] in self.arg_logical:
                        yield Token(self.arg_logical[sub_exprs[0]])
                        arg_exprs = sub_exprs[1:]
                    else:
                        arg_exprs = sub_exprs
                    arg = arg_types.pop()
                    if not arg:
                        raise ParseError("No arg type is set")
                    for arg_expr in arg_exprs:
                        yield arg(arg_expr)

            yield Token(op.SEP)


def create_node(tok: Token):
    if is_a(tok, op.UNARY_OPS) or is_a(tok, op.NOT):
        return create_unary_node(tok.type, tok.value)
    elif is_a(tok, op.BINARY_OPS):
        return create_binary_node(tok.type, tok.value)
    elif is_a(tok, op.ARGS):
        return Node(tok.type, 0, tok.value)
    elif is_a(tok, op.LOGICAL) or is_a(tok, op.ARG_LOGICAL):
        return Node(tok.type, None, tok.value)
    else:
        return None


class KarpTNGParser:
    def parse(self, tokens):
        curr = None
        stack = []
        for tok in tokens:
            print("Token({}, {})".format(tok.type, tok.value))
            if is_a(tok, op.ARGS):
                n = create_node(tok)
                if curr:
                    curr.add_child(n)
                elif stack:
                    stack[-1].add_child(n)
            elif is_a(tok, op.SEP):
                if curr:
                    if is_a(curr, op.OPS) and curr.n_children() < curr.arity:
                        stack.append(curr)
                    elif is_a(curr, op.ARG_LOGICAL):
                        n = stack.pop()
                        if is_a(n, op.OPS):
                            n.add_child(curr)
                            stack.append(n)
                        else:
                            raise ParseError(
                                "No OP to add ARG_LOGICAL '{curr}'".format(curr=curr)
                            )
                    elif stack:
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
            elif is_a(tok, op.LOGICAL):
                stack.append(create_node(tok))
            else:
                if curr:
                    raise RuntimeError("")
                curr = create_node(tok)
            print("curr = {curr}".format(curr=curr))
            print("stack = {stack}".format(stack=stack))

        root = None
        for node in reversed(stack):
            if root:
                # if is_a(root, op.AND_OR) and is_a(node, op.AND_OR):

                node.add_child(root)
            root = node
        return root


_lexer = KarpTNGLexer()
_parser = KarpTNGParser()


def parse(s: Optional[str]) -> Ast:
    if not s:
        return Ast()
    return Ast(_parser.parse(_lexer.tokenize(s)))
