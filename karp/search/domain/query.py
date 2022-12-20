import typing
from enum import Enum
from typing import Dict, List, Optional

import pydantic

from karp.search.domain import errors, query_dsl  # , resourcemgr

# from karp.domain import errors
from karp.util import convert as util_convert
from karp.utility.container import arg_get


class Format(str, Enum):
    json = "json"
    csv = "csv"
    xml = "xml"
    lmf = "lmf?"
    tsb = "tsb"


class Query(pydantic.BaseModel):
    fields: typing.List[str]
    resources: typing.List[str]
    sort: typing.List[str]
    from_: int = pydantic.Field(0, alias="from")
    size: int = 25
    split_results: bool = False
    lexicon_stats: bool = True
    include_fields: typing.Optional[typing.List[str]] = None
    exclude_fields: typing.Optional[typing.List[str]] = None
    format_: typing.Optional[Format] = pydantic.Field(None, alias="format")
    format_query: typing.Optional[Format] = None
    q: typing.Optional[str] = None
    ast: typing.Optional[query_dsl.Ast] = None
    sort_dict: typing.Optional[typing.Dict[str, typing.List[str]]] = pydantic.Field(
        default_factory=dict
    )

    @pydantic.validator(
        "resources", "include_fields", "exclude_fields", "sort", pre=True
    )
    @classmethod
    def split_str(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v

    @pydantic.validator("fields", "sort", pre=True, always=True)
    @classmethod
    def set_ts_now(cls, v):
        return v or []

    class Config:
        arbitrary_types_allowed = True

    def parse_arguments(self, args, resource_str: str):
        if resource_str is None:
            raise errors.IncompleteQuery("No resources are defined.")
        self.resources = resource_str.split(",")
        self.from_ = arg_get(args, "from", int, 0)
        self.size = arg_get(args, "size", int, 25)
        self.lexicon_stats = arg_get(args, "lexicon_stats", util_convert.str2bool, True)
        self.include_fields = arg_get(
            args, "include_fields", util_convert.str2list(",")
        )
        self.exclude_fields = arg_get(
            args, "exclude_fields", util_convert.str2list(",")
        )
        self.fields = []
        self.format = arg_get(args, "format")
        self.format_query = arg_get(args, "format_query")
        self.q = arg_get(args, "q") or ""
        self.sort: List[str] = arg_get(args, "sort", util_convert.str2list(",")) or []
        # self.sort_dict: Dict[str, List[str]] = {}
        #         if not self.sort:
        #             if len(self.resources) == 1:
        #                 self.sort = resourcemgr.get_resource(self.resources[0]).default_sort()
        #             else:
        #                 for resource_id in self.resources:
        #                     self.sort_dict[resource_id] = resourcemgr.get_resource(
        #                         resource_id
        #                     ).default_sort()
        self.ast = query_dsl.parse(self.q)
        self._update_ast()

    def _update_ast(self):
        if self.ast.is_empty():
            return

        field_translations = {}
        for resource in self.resources:
            # ft = resourcemgr.get_field_translations(resource)
            ft = {}
            if ft:
                for field, lst in ft.items():
                    if field in field_translations:
                        field_translations[field].update(lst)
                    else:
                        field_translations[field] = set(lst)

        def translate_node(node: query_dsl.Node):
            print("node = {node!r}".format(node=node))
            if query_dsl.is_a(
                node, [query_dsl.op.FREERGXP, query_dsl.op.FREETEXT, query_dsl.op.ARGS]
            ):
                return

            if query_dsl.is_a(node, query_dsl.op.LOGICAL):
                for child in node.children:
                    translate_node(child)
            elif query_dsl.is_a(node, query_dsl.op.OPS):
                print("|OPS| node.children = {}".format(node.children))
                field = node.children[0]
                if query_dsl.is_a(field, query_dsl.op.STRING):
                    if field.value in field_translations:
                        fields = query_dsl.Node(query_dsl.op.ARG_OR, None)
                        fields.add_child(field)
                        for _ft in field_translations[field.value]:
                            fields.add_child(
                                query_dsl.Node(query_dsl.op.STRING, 0, _ft)
                            )
                        node.children[0] = fields
                else:
                    translate_node(field)
            # elif query_dsl.is_a(node, query_dsl.op.ARG_LOGICAL):
            elif query_dsl.is_a(node, query_dsl.op.ARG_OR):
                print("|ARG_OR| node.children = {node.children}".format(node=node))

                for child in node.children:
                    if child.value in field_translations:
                        for _ft in field_translations[child.value]:
                            node.add_child(query_dsl.Node(query_dsl.op.STRING, 0, _ft))
            elif query_dsl.is_a(node, query_dsl.op.ARG_LOGICAL):  # ARG_OR handled above
                print("|ARG_AND| node.children = {node.children}".format(node=node))
                changes = []
                for i, child in enumerate(node.children):
                    if child.value in field_translations:
                        fields = query_dsl.Node(query_dsl.op.ARG_OR, None)
                        fields.add_child(child)
                        for _ft in field_translations[child.value]:
                            fields.add_child(
                                query_dsl.Node(query_dsl.op.STRING, 0, _ft)
                            )
                        changes.append((i, fields))
                print("|ARG_AND| changes = {changes}".format(changes=changes))
                for i, fields in changes:
                    node.children[i] = fields
                print("|ARG_AND| node.children = {node.children}".format(node=node))

        translate_node(self.ast.root)
        # TODO rewrite

    # def __repr__(self) -> str:
    #     return """
    #         {}(
    #             q={}
    #             resources={}
    #             include_fields={}
    #             exclude_fields={}
    #             fields={}
    #             sort={}
    #             from={}, size={},
    #             split_results={}, lexicon_stats={},
    #             format={}
    #             format_query={}
    #         )""".format(
    #         self._self_name(),
    #         self.q,
    #         self.resources,
    #         self.include_fields,
    #         self.exclude_fields,
    #         self.fields,
    #         self.sort,
    #         self.from_,
    #         self.size,
    #         self.split_results,
    #         self.lexicon_stats,
    #         self.format,
    #         self.format_query,
    #     )

    def _self_name(self) -> str:
        return "Query"
