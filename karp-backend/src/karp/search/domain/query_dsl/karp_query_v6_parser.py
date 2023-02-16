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
from tatsu.parsing import leftrec, nomemo, isname  # noqa: F401
from tatsu.infos import ParserConfig
from tatsu.util import re, generic_main  # noqa: F401


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
            namechars="",
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
            namechars="",
            parseinfo=False,
            keywords=KEYWORDS,
            start="start",
        )
        config = config.replace(**settings)
        super().__init__(config=config)

    @tatsumasu()
    def _start_(self):
        self._expression_()
        self._check_eof()

    @tatsumasu()
    def _expression_(self):
        with self._choice():
            with self._option():
                self._logical_expression_()
            with self._option():
                self._query_expression_()
            self._error(
                "expecting one of: "
                "<and> <contains> <endswith> <equals>"
                "<exists> <freergxp> <freetext> <gt>"
                "<gte> <logical_expression> <lt> <lte>"
                "<missing> <not> <or> <query_expression>"
                "<regexp> <startswith>"
            )

    @tatsumasu()
    def _query_expression_(self):
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
                "expecting one of: "
                "'contains' 'endswith' 'equals' 'exists'"
                "'freergxp' 'gt' 'gte' 'lt' 'lte'"
                "'missing' 'regexp' 'startswith'"
                "<freetext> <freetext_any>"
                "<freetext_string>"
            )

    @tatsumasu()
    def _logical_expression_(self):
        with self._choice():
            with self._option():
                self._and_()
            with self._option():
                self._or_()
            with self._option():
                self._not_()
            self._error("expecting one of: " "'and' 'not' 'or'")

    @tatsumasu("And")
    def _and_(self):
        self._token("and")
        self.name_last_node("op")
        self._token("(")
        self._expression_()
        self.add_last_node_to_name("exps")

        def block2():
            self._token("||")
            self._expression_()
            self.add_last_node_to_name("exps")

            self._define([], ["exps"])

        self._closure(block2)
        self._token(")")

        self._define(["op"], ["exps"])

    @tatsumasu("Contains")
    def _contains_(self):
        self._token("contains")
        self.name_last_node("op")
        self._token("|")
        self._string_()
        self.name_last_node("field")
        self._token("|")
        self._string_()
        self.name_last_node("arg")

        self._define(["arg", "field", "op"], [])

    @tatsumasu("Endswith")
    def _endswith_(self):
        self._token("endswith")
        self.name_last_node("op")
        self._token("|")
        self._string_()
        self.name_last_node("field")
        self._token("|")
        self._string_()
        self.name_last_node("arg")

        self._define(["arg", "field", "op"], [])

    @tatsumasu("Equals")
    def _equals_(self):
        self._token("equals")
        self.name_last_node("op")
        self._token("|")
        self._string_()
        self.name_last_node("field")
        self._token("|")
        self._argument_()
        self.name_last_node("arg")

        self._define(["arg", "field", "op"], [])

    @tatsumasu("Exists")
    def _exists_(self):
        self._token("exists")
        self.name_last_node("op")
        self._token("|")
        self._string_()
        self.name_last_node("field")

        self._define(["field", "op"], [])

    @tatsumasu("Freergxp")
    def _freergxp_(self):
        self._token("freergxp")
        self.name_last_node("op")
        self._token("|")
        self._string_()
        self.name_last_node("arg")

        self._define(["arg", "op"], [])

    @tatsumasu()
    def _freetext_(self):
        with self._choice():
            with self._option():
                self._freetext_any_()
            with self._option():
                self._freetext_string_()
            self._error(
                "expecting one of: " "'freetext' <freetext_any>" "<freetext_string>"
            )

    @tatsumasu("FreetextAnyButString")
    def _freetext_any_(self):
        self._token("freetext")
        self.name_last_node("op")
        self._token("|")
        self._any_but_string_()
        self.name_last_node("arg")

        self._define(["arg", "op"], [])

    @tatsumasu("FreetextString")
    def _freetext_string_(self):
        self._token("freetext")
        self.name_last_node("op")
        self._token("|")
        self._string_()
        self.name_last_node("arg")

        self._define(["arg", "op"], [])

    @tatsumasu("Gt")
    def _gt_(self):
        self._token("gt")
        self.name_last_node("op")
        self._token("|")
        self._string_()
        self.name_last_node("field")
        self._token("|")
        self._argument_()
        self.name_last_node("arg")

        self._define(["arg", "field", "op"], [])

    @tatsumasu("Gte")
    def _gte_(self):
        self._token("gte")
        self.name_last_node("op")
        self._token("|")
        self._string_()
        self.name_last_node("field")
        self._token("|")
        self._argument_()
        self.name_last_node("arg")

        self._define(["arg", "field", "op"], [])

    @tatsumasu("Lt")
    def _lt_(self):
        self._token("lt")
        self.name_last_node("op")
        self._token("|")
        self._string_()
        self.name_last_node("field")
        self._token("|")
        self._argument_()
        self.name_last_node("arg")

        self._define(["arg", "field", "op"], [])

    @tatsumasu("Lte")
    def _lte_(self):
        self._token("lte")
        self.name_last_node("op")
        self._token("|")
        self._string_()
        self.name_last_node("field")
        self._token("|")
        self._argument_()
        self.name_last_node("arg")

        self._define(["arg", "field", "op"], [])

    @tatsumasu("Missing")
    def _missing_(self):
        self._token("missing")
        self.name_last_node("op")
        self._token("|")
        self._string_()
        self.name_last_node("field")

        self._define(["field", "op"], [])

    @tatsumasu("Not")
    def _not_(self):
        self._token("not")
        self.name_last_node("op")
        self._token("(")
        self._expression_()
        self.add_last_node_to_name("exps")

        def block2():
            self._token("||")
            self._expression_()
            self.add_last_node_to_name("exps")

            self._define([], ["exps"])

        self._closure(block2)
        self._token(")")

        self._define(["op"], ["exps"])

    @tatsumasu("Or")
    def _or_(self):
        self._token("or")
        self.name_last_node("op")
        self._token("(")
        self._expression_()
        self.add_last_node_to_name("exps")

        def block2():
            self._token("||")
            self._expression_()
            self.add_last_node_to_name("exps")

            self._define([], ["exps"])

        self._closure(block2)
        self._token(")")

        self._define(["op"], ["exps"])

    @tatsumasu("Regexp")
    def _regexp_(self):
        self._token("regexp")
        self.name_last_node("op")
        self._token("|")
        self._string_()
        self.name_last_node("field")
        self._token("|")
        self._string_()
        self.name_last_node("arg")

        self._define(["arg", "field", "op"], [])

    @tatsumasu("Startswith")
    def _startswith_(self):
        self._token("startswith")
        self.name_last_node("op")
        self._token("|")
        self._string_()
        self.name_last_node("field")
        self._token("|")
        self._string_()
        self.name_last_node("arg")

        self._define(["arg", "field", "op"], [])

    @tatsumasu()
    def _argument_(self):
        with self._choice():
            with self._option():
                self._integer_()
            with self._option():
                self._string_()
            self._error("expecting one of: " "<integer> <string> [^|()]+ \\d+")

    @tatsumasu()
    def _any_but_string_(self):
        self._integer_()

    @tatsumasu()
    def _string_(self):
        self._pattern("[^|()]+")

    @tatsumasu("int")
    def _integer_(self):
        self._pattern("\\d+")


class KarpQueryV6Semantics:
    def start(self, ast):
        return ast

    def expression(self, ast):
        return ast

    def query_expression(self, ast):
        return ast

    def logical_expression(self, ast):
        return ast

    def and_(self, ast):
        return ast

    def contains(self, ast):
        return ast

    def endswith(self, ast):
        return ast

    def equals(self, ast):
        return ast

    def exists(self, ast):
        return ast

    def freergxp(self, ast):
        return ast

    def freetext(self, ast):
        return ast

    def freetext_any(self, ast):
        return ast

    def freetext_string(self, ast):
        return ast

    def gt(self, ast):
        return ast

    def gte(self, ast):
        return ast

    def lt(self, ast):
        return ast

    def lte(self, ast):
        return ast

    def missing(self, ast):
        return ast

    def not_(self, ast):
        return ast

    def or_(self, ast):
        return ast

    def regexp(self, ast):
        return ast

    def startswith(self, ast):
        return ast

    def argument(self, ast):
        return ast

    def any_but_string(self, ast):
        return ast

    def string(self, ast):
        return ast

    def integer(self, ast):
        return ast


def main(filename, **kwargs):
    if not filename or filename == "-":
        text = sys.stdin.read()
    else:
        with open(filename) as f:
            text = f.read()
    parser = KarpQueryV6Parser()
    return parser.parse(text, filename=filename, **kwargs)


if __name__ == "__main__":
    import json
    from tatsu.util import asjson

    ast = generic_main(main, KarpQueryV6Parser, name="KarpQueryV6")
    data = asjson(ast)
    print(json.dumps(data, indent=2))
