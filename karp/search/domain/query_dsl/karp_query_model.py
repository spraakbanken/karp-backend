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

from dataclasses import dataclass
from typing import Any

from tatsu.objectmodel import Node
from tatsu.semantics import ModelBuilderSemantics


@dataclass(eq=False)
class ModelBase(Node):
    pass


class KarpQueryModelBuilderSemantics(ModelBuilderSemantics):
    def __init__(self, context=None, types=None):
        types = [t for t in globals().values() if type(t) is type and issubclass(t, ModelBase)] + (types or [])
        super().__init__(context=context, types=types)


@dataclass(eq=False)
class SubQuery(ModelBase):
    exp: Any = None
    field: Any = None


@dataclass(eq=False)
class And(ModelBase):
    pass


@dataclass(eq=False)
class Contains(ModelBase):
    arg: Any = None
    field: Any = None


@dataclass(eq=False)
class Endswith(ModelBase):
    arg: Any = None
    field: Any = None


@dataclass(eq=False)
class Equals(ModelBase):
    arg: Any = None
    field: Any = None


@dataclass(eq=False)
class Exists(ModelBase):
    field: Any = None


@dataclass(eq=False)
class Freergxp(ModelBase):
    arg: Any = None


@dataclass(eq=False)
class Freetext(ModelBase):
    arg: Any = None


@dataclass(eq=False)
class Gt(ModelBase):
    arg: Any = None
    field: Any = None
    op: Any = None


@dataclass(eq=False)
class Gte(ModelBase):
    arg: Any = None
    field: Any = None
    op: Any = None


@dataclass(eq=False)
class Lt(ModelBase):
    arg: Any = None
    field: Any = None
    op: Any = None


@dataclass(eq=False)
class Lte(ModelBase):
    arg: Any = None
    field: Any = None
    op: Any = None


@dataclass(eq=False)
class Missing(ModelBase):
    field: Any = None


@dataclass(eq=False)
class Not(ModelBase):
    pass


@dataclass(eq=False)
class Or(ModelBase):
    pass


@dataclass(eq=False)
class Regexp(ModelBase):
    arg: Any = None
    field: Any = None


@dataclass(eq=False)
class Startswith(ModelBase):
    arg: Any = None
    field: Any = None


@dataclass(eq=False)
class StringValue(ModelBase):
    pass


@dataclass(eq=False)
class QuotedStringValue(ModelBase):
    pass


@dataclass(eq=False)
class Identifier(ModelBase):
    pass
