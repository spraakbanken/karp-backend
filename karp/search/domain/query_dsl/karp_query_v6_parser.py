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


class KarpQueryV6Buffer(Buffer):
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


class KarpQueryV6Parser(Parser):
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
            self._error(
                'expecting one of: '
                '<and> <contains> <endswith> <equals>'
                '<exists> <freergxp> <freetext> <gt>'
                '<gte> <logical_expression> <lt> <lte>'
                '<missing> <not> <or> <query_expression>'
                '<regexp> <startswith>'
            )

    @tatsumasu()
    def _query_expression_(self):  # noqa
        with self._choice():
            with self._option():
                self._contains_()
            with self._option():
                self._endswith_()
            with self._option():
                self._equals_()
            with self._option():
                self._exists_()
            with self._option():
                self._freergxp_()
            with self._option():
                self._freetext_()
            with self._option():
                self._gt_()
            with self._option():
                self._gte_()
            with self._option():
                self._lt_()
            with self._option():
                self._lte_()
            with self._option():
                self._missing_()
            with self._option():
                self._regexp_()
            with self._option():
                self._startswith_()
            self._error(
                'expecting one of: '
                "'contains' 'endswith' 'equals' 'exists'"
                "'freergxp' 'freetext' 'gt' 'gte' 'lt'"
                "'lte' 'missing' 'regexp' 'startswith'"
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

    @tatsumasu('And')
    def _and_(self):  # noqa
        self._token('and')
        self._token('(')

        def sep1():
            self._token('||')

        def block1():
            self._expression_()
        self._positive_gather(block1, sep1)
        self.name_last_node('@')
        self._token(')')

    @tatsumasu('Contains')
    def _contains_(self):  # noqa
        self._token('contains')
        self._token('|')
        self._identifier_()
        self.name_last_node('field')
        self._token('|')
        self._string_value_()
        self.name_last_node('arg')

        self._define(
            ['arg', 'field'],
            []
        )

    @tatsumasu('Endswith')
    def _endswith_(self):  # noqa
        self._token('endswith')
        self._token('|')
        self._identifier_()
        self.name_last_node('field')
        self._token('|')
        self._string_value_()
        self.name_last_node('arg')

        self._define(
            ['arg', 'field'],
            []
        )

    @tatsumasu('Equals')
    def _equals_(self):  # noqa
        self._token('equals')
        self._token('|')
        self._identifier_()
        self.name_last_node('field')
        self._token('|')
        self._any_value_()
        self.name_last_node('arg')

        self._define(
            ['arg', 'field'],
            []
        )

    @tatsumasu('Exists')
    def _exists_(self):  # noqa
        self._token('exists')
        self._token('|')
        self._identifier_()
        self.name_last_node('field')

        self._define(
            ['field'],
            []
        )

    @tatsumasu('Freergxp')
    def _freergxp_(self):  # noqa
        self._token('freergxp')
        self._token('|')
        self._string_value_()
        self.name_last_node('arg')

        self._define(
            ['arg'],
            []
        )

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

    @tatsumasu('Gt')
    def _gt_(self):  # noqa
        self._token('gt')
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

    @tatsumasu('Gte')
    def _gte_(self):  # noqa
        self._token('gte')
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

    @tatsumasu('Lt')
    def _lt_(self):  # noqa
        self._token('lt')
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

    @tatsumasu('Lte')
    def _lte_(self):  # noqa
        self._token('lte')
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

    @tatsumasu('Missing')
    def _missing_(self):  # noqa
        self._token('missing')
        self._token('|')
        self._identifier_()
        self.name_last_node('field')

        self._define(
            ['field'],
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
        self._positive_gather(block1, sep1)
        self.name_last_node('@')
        self._token(')')

    @tatsumasu('Regexp')
    def _regexp_(self):  # noqa
        self._token('regexp')
        self._token('|')
        self._identifier_()
        self.name_last_node('field')
        self._token('|')
        self._string_value_()
        self.name_last_node('arg')

        self._define(
            ['arg', 'field'],
            []
        )

    @tatsumasu('Startswith')
    def _startswith_(self):  # noqa
        self._token('startswith')
        self._token('|')
        self._identifier_()
        self.name_last_node('field')
        self._token('|')
        self._string_value_()
        self.name_last_node('arg')

        self._define(
            ['arg', 'field'],
            []
        )

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
                '\\d+'
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
        self._pattern('\\d+')

    @tatsumasu()
    def _identifier_(self):  # noqa
        self._pattern('[^|)(]+')


class KarpQueryV6Semantics:
    def start(self, ast):  # noqa
        return ast

    def expression(self, ast):  # noqa
        return ast

    def query_expression(self, ast):  # noqa
        return ast

    def logical_expression(self, ast):  # noqa
        return ast

    def and_(self, ast):  # noqa
        return ast

    def contains(self, ast):  # noqa
        return ast

    def endswith(self, ast):  # noqa
        return ast

    def equals(self, ast):  # noqa
        return ast

    def exists(self, ast):  # noqa
        return ast

    def freergxp(self, ast):  # noqa
        return ast

    def freetext(self, ast):  # noqa
        return ast

    def gt(self, ast):  # noqa
        return ast

    def gte(self, ast):  # noqa
        return ast

    def lt(self, ast):  # noqa
        return ast

    def lte(self, ast):  # noqa
        return ast

    def missing(self, ast):  # noqa
        return ast

    def not_(self, ast):  # noqa
        return ast

    def or_(self, ast):  # noqa
        return ast

    def regexp(self, ast):  # noqa
        return ast

    def startswith(self, ast):  # noqa
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
    parser = KarpQueryV6Parser()
    return parser.parse(
        text,
        filename=filename,
        **kwargs
    )


if __name__ == '__main__':
    import json
    from tatsu.util import asjson

    ast = generic_main(main, KarpQueryV6Parser, name='KarpQueryV6')
    data = asjson(ast)
    print(json.dumps(data, indent=2))

