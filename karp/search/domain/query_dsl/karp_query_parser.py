#!/usr/bin/env python

# CAVEAT UTILITOR
#
# This file was automatically generated by TatSu.
#
#    https://pypi.python.org/pypi/tatsu/
#
# Any changes you make to it will be overwritten the next time
# the file is generated.

from __future__ import annotations

import sys

from tatsu.buffering import Buffer
from tatsu.parsing import Parser
from tatsu.parsing import tatsumasu
from tatsu.parsing import leftrec, nomemo, isname # noqa
from tatsu.infos import ParserConfig
from tatsu.util import re, generic_main  # noqa


KEYWORDS = {}  # type: ignore


class KarpQueryBuffer(Buffer):
    def __init__(self, text, /, config: ParserConfig = None, **settings):
        config = ParserConfig.new(
            config,
            owner=self,
            whitespace=None,
            nameguard=None,
            comments_re=None,
            eol_comments_re=None,
            ignorecase=False,
            namechars='',
            parseinfo=False,
        )
        config = config.replace(**settings)
        super().__init__(text, config=config)


class KarpQueryParser(Parser):
    def __init__(self, /, config: ParserConfig = None, **settings):
        config = ParserConfig.new(
            config,
            owner=self,
            whitespace=None,
            nameguard=None,
            comments_re=None,
            eol_comments_re=None,
            ignorecase=False,
            namechars='',
            parseinfo=False,
            keywords=KEYWORDS,
            start='start',
        )
        config = config.replace(**settings)
        super().__init__(config=config)

    @tatsumasu()
    def _start_(self):  # noqa
        self._expression_()
        self._check_eof()

    @tatsumasu()
    def _expression_(self):  # noqa
        with self._choice():
            with self._option():
                self._logical_expression_()
            with self._option():
                self._query_expression_()
            with self._option():
                self._sub_query_()
            self._error(
                'expecting one of: '
                '<and> <binary_query_expression>'
                '<identifier> <logical_expression> <not>'
                '<or> <query_expression> <sub_query>'
                '<unary_query_expression>'
            )

    @tatsumasu()
    def _query_expression_(self):  # noqa
        with self._choice():
            with self._option():
                self._unary_query_expression_()
            with self._option():
                self._binary_query_expression_()
            self._error(
                'expecting one of: '
                '<any_arg_expr> <binary_query_expression>'
                '<field_query> <freetext> <text_arg_expr>'
                '<unary_query_expression>'
            )

    @tatsumasu()
    def _unary_query_expression_(self):  # noqa
        with self._choice():
            with self._option():
                self._field_query_()
            with self._option():
                self._freetext_()
            self._error(
                'expecting one of: '
                "'exists' 'freetext' 'missing'"
                '<field_query>'
            )

    @tatsumasu('FieldQuery')
    def _field_query_(self):  # noqa
        with self._group():
            with self._choice():
                with self._option():
                    self._token('exists')
                with self._option():
                    self._token('missing')
                self._error(
                    'expecting one of: '
                    "'exists' 'missing'"
                )
        self.name_last_node('op')
        self._token('|')
        self._identifier_()
        self.name_last_node('field')

        self._define(
            ['field', 'op'],
            []
        )

    @tatsumasu()
    def _binary_query_expression_(self):  # noqa
        with self._choice():
            with self._option():
                self._text_arg_expr_()
            with self._option():
                self._any_arg_expr_()
            self._error(
                'expecting one of: '
                '<any_arg_expr> <any_arg_op>'
                '<text_arg_expr> <text_value_op>'
            )

    @tatsumasu('TextArgExpression')
    def _text_arg_expr_(self):  # noqa
        self._text_value_op_()
        self.name_last_node('op')
        self._token('|')
        self._identifier_()
        self.name_last_node('field')
        self._token('|')
        self._string_value_()
        self.name_last_node('arg')

        self._define(
            ['arg', 'field', 'op'],
            []
        )

    @tatsumasu()
    def _text_value_op_(self):  # noqa
        with self._choice():
            with self._option():
                self._token('contains')
            with self._option():
                self._token('endswith')
            with self._option():
                self._token('regexp')
            with self._option():
                self._token('startswith')
            self._error(
                'expecting one of: '
                "'contains' 'endswith' 'regexp'"
                "'startswith'"
            )

    @tatsumasu('AnyArgExpression')
    def _any_arg_expr_(self):  # noqa
        self._any_arg_op_()
        self.name_last_node('op')
        self._token('|')
        self._identifier_()
        self.name_last_node('field')
        self._token('|')
        self._any_value_()
        self.name_last_node('arg')

        self._define(
            ['arg', 'field', 'op'],
            []
        )

    @tatsumasu()
    def _any_arg_op_(self):  # noqa
        with self._choice():
            with self._option():
                self._token('equals')
            with self._option():
                self._token('gt')
            with self._option():
                self._token('gte')
            with self._option():
                self._token('lt')
            with self._option():
                self._token('lte')
            self._error(
                'expecting one of: '
                "'equals' 'gt' 'gte' 'lt' 'lte'"
            )

    @tatsumasu()
    def _logical_expression_(self):  # noqa
        with self._choice():
            with self._option():
                self._and_()
            with self._option():
                self._or_()
            with self._option():
                self._not_()
            self._error(
                'expecting one of: '
                "'and' 'not' 'or'"
            )

    @tatsumasu('SubQuery')
    def _sub_query_(self):  # noqa
        self._identifier_()
        self.name_last_node('field')
        self._token('(')
        self._expression_()
        self.name_last_node('exp')
        self._token(')')

        self._define(
            ['exp', 'field'],
            []
        )

    @tatsumasu('And')
    def _and_(self):  # noqa
        self._token('and')
        self._token('(')

        def sep1():
            self._token('||')

        def block1():
            self._expression_()
        self._gather(block1, sep1)
        self.name_last_node('@')
        self._token(')')

    @tatsumasu('Freetext')
    def _freetext_(self):  # noqa
        self._token('freetext')
        self._token('|')
        self._string_value_()
        self.name_last_node('arg')

        self._define(
            ['arg'],
            []
        )

    @tatsumasu('Not')
    def _not_(self):  # noqa
        self._token('not')
        self._token('(')

        def sep1():
            self._token('||')

        def block1():
            self._expression_()
        self._positive_gather(block1, sep1)
        self.name_last_node('@')
        self._token(')')

    @tatsumasu('Or')
    def _or_(self):  # noqa
        self._token('or')
        self._token('(')

        def sep1():
            self._token('||')

        def block1():
            self._expression_()
        self._gather(block1, sep1)
        self.name_last_node('@')
        self._token(')')

    @tatsumasu()
    def _any_value_(self):  # noqa
        with self._choice():
            with self._option():
                self._integer_value_()
            with self._option():
                self._string_value_()
            self._error(
                'expecting one of: '
                '<integer_value> <quoted_string_value>'
                '<string_value> <unquoted_string_value>'
                '\\d+$'
            )

    @tatsumasu('StringValue')
    def _string_value_(self):  # noqa
        with self._choice():
            with self._option():
                self._unquoted_string_value_()
            with self._option():
                self._quoted_string_value_()
            self._error(
                'expecting one of: '
                '\'"\' <quoted_string_value>'
                '<unquoted_string_value> [^|)("]+'
            )

    @tatsumasu()
    def _unquoted_string_value_(self):  # noqa
        self._pattern('[^|)("]+')
        self.name_last_node('@')

    @tatsumasu('QuotedStringValue')
    def _quoted_string_value_(self):  # noqa
        self._token('"')

        def block1():
            with self._choice():
                with self._option():
                    self._pattern('(?s)\\s+')
                with self._option():
                    self._token('\\"')
                with self._option():
                    self._pattern('[^"]')
                self._error(
                    'expecting one of: '
                    '\'\\\\"\' (?s)\\s+ [^"]'
                )
        self._closure(block1)
        self.name_last_node('@')
        self._token('"')

    @tatsumasu('int')
    def _integer_value_(self):  # noqa
        self._pattern('\\d+$')

    @tatsumasu('Identifier')
    def _identifier_(self):  # noqa
        self._pattern('[^|)(]+')


class KarpQuerySemantics:
    def start(self, ast):  # noqa
        return ast

    def expression(self, ast):  # noqa
        return ast

    def query_expression(self, ast):  # noqa
        return ast

    def unary_query_expression(self, ast):  # noqa
        return ast

    def field_query(self, ast):  # noqa
        return ast

    def binary_query_expression(self, ast):  # noqa
        return ast

    def text_arg_expr(self, ast):  # noqa
        return ast

    def text_value_op(self, ast):  # noqa
        return ast

    def any_arg_expr(self, ast):  # noqa
        return ast

    def any_arg_op(self, ast):  # noqa
        return ast

    def logical_expression(self, ast):  # noqa
        return ast

    def sub_query(self, ast):  # noqa
        return ast

    def and_(self, ast):  # noqa
        return ast

    def freetext(self, ast):  # noqa
        return ast

    def not_(self, ast):  # noqa
        return ast

    def or_(self, ast):  # noqa
        return ast

    def any_value(self, ast):  # noqa
        return ast

    def string_value(self, ast):  # noqa
        return ast

    def unquoted_string_value(self, ast):  # noqa
        return ast

    def quoted_string_value(self, ast):  # noqa
        return ast

    def integer_value(self, ast):  # noqa
        return ast

    def identifier(self, ast):  # noqa
        return ast


def main(filename, **kwargs):
    if not filename or filename == '-':
        text = sys.stdin.read()
    else:
        with open(filename) as f:
            text = f.read()
    parser = KarpQueryParser()
    return parser.parse(
        text,
        filename=filename,
        **kwargs
    )


if __name__ == '__main__':
    import json
    from tatsu.util import asjson

    ast = generic_main(main, KarpQueryParser, name='KarpQuery')
    data = asjson(ast)
    print(json.dumps(data, indent=2))

