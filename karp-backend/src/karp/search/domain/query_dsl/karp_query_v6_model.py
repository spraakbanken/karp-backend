#!/usr/bin/env python  # noqa: D100

# CAVEAT UTILITOR
#
# This file was automatically generated by TatSu.
#
#    https://pypi.python.org/pypi/tatsu/
#
# Any changes you make to it will be overwritten the next time
# the file is generated.

from __future__ import annotations  # noqa: I001

from typing import Any
from dataclasses import dataclass

from tatsu.objectmodel import Node
from tatsu.semantics import ModelBuilderSemantics


@dataclass(eq=False)
class ModelBase(Node):  # noqa: D101
    pass


class KarpQueryV6ModelBuilderSemantics(ModelBuilderSemantics):  # noqa: D101
    def __init__(self, context=None, types=None):  # noqa: D107, ANN204, ANN001
        types = [
            t
            for t in globals().values()
            if type(t) is type and issubclass(t, ModelBase)
        ] + (types or [])
        super().__init__(context=context, types=types)


@dataclass(eq=False)
class And(ModelBase):  # noqa: D101
    exps: Any = None
    op: Any = None


@dataclass(eq=False)
class Contains(ModelBase):  # noqa: D101
    arg: Any = None
    field: Any = None
    op: Any = None


@dataclass(eq=False)
class Endswith(ModelBase):  # noqa: D101
    arg: Any = None
    field: Any = None
    op: Any = None


@dataclass(eq=False)
class Equals(ModelBase):  # noqa: D101
    arg: Any = None
    field: Any = None
    op: Any = None


@dataclass(eq=False)
class Exists(ModelBase):  # noqa: D101
    field: Any = None
    op: Any = None


@dataclass(eq=False)
class Freergxp(ModelBase):  # noqa: D101
    arg: Any = None
    op: Any = None


@dataclass(eq=False)
class FreetextAnyButString(ModelBase):  # noqa: D101
    arg: Any = None
    op: Any = None


@dataclass(eq=False)
class FreetextString(ModelBase):  # noqa: D101
    arg: Any = None
    op: Any = None


@dataclass(eq=False)
class Gt(ModelBase):  # noqa: D101
    arg: Any = None
    field: Any = None
    op: Any = None


@dataclass(eq=False)
class Gte(ModelBase):  # noqa: D101
    arg: Any = None
    field: Any = None
    op: Any = None


@dataclass(eq=False)
class Lt(ModelBase):  # noqa: D101
    arg: Any = None
    field: Any = None
    op: Any = None


@dataclass(eq=False)
class Lte(ModelBase):  # noqa: D101
    arg: Any = None
    field: Any = None
    op: Any = None


@dataclass(eq=False)
class Missing(ModelBase):  # noqa: D101
    field: Any = None
    op: Any = None


@dataclass(eq=False)
class Not(ModelBase):  # noqa: D101
    exps: Any = None
    op: Any = None


@dataclass(eq=False)
class Or(ModelBase):  # noqa: D101
    exps: Any = None
    op: Any = None


@dataclass(eq=False)
class Regexp(ModelBase):  # noqa: D101
    arg: Any = None
    field: Any = None
    op: Any = None


@dataclass(eq=False)
class Startswith(ModelBase):  # noqa: D101
    arg: Any = None
    field: Any = None
    op: Any = None
