from typing import Optional, Callable, TypeVar, List, Dict

from karp.util import convert as util_convert

from karp import query_dsl, resourcemgr

from . import errors


T = TypeVar("T", bool, int, str, List[str])


def arg_get(
    args: Dict,
    arg_name: str,
    convert: Optional[Callable[[str], T]] = None,
    default: Optional[T] = None,
) -> Optional[T]:
    arg = args.get(arg_name, None)
    if arg is None:
        return default
    if convert is None:
        return arg
    return convert(arg)


class Query:
    from_ = 0
    size = 25
    split_results = False
    lexicon_stats = True
    include_fields = None
    exclude_fields = None
    fields = []
    format = None
    format_query = None
    q: Optional[str] = None
    resources = []
    sort: List[str] = []

    def __init__(self):
        # Load field_translations here?
        pass

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
        self.sort_dict: Dict[str, List[str]] = {}
        if not self.sort:
            if len(self.resources) == 1:
                self.sort = resourcemgr.get_resource(self.resources[0]).default_sort()
            else:
                for resource_id in self.resources:
                    self.sort_dict[resource_id] = resourcemgr.get_resource(
                        resource_id
                    ).default_sort()
        self.ast = query_dsl.parse(self.q)
        self._update_ast()

    def _update_ast(self):
        if self.ast.is_empty():
            return

        field_translations = {}
        for resource in self.resources:
            ft = resourcemgr.get_field_translations(resource)
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

    def __repr__(self) -> str:
        return """
            {}(
                q={}
                resources={}
                include_fields={}
                exclude_fields={}
                fields={}
                sort={}
                from={}, size={},
                split_results={}, lexicon_stats={},
                format={}
                format_query={}
            )""".format(
            self._self_name(),
            self.q,
            self.resources,
            self.include_fields,
            self.exclude_fields,
            self.fields,
            self.sort,
            self.from_,
            self.size,
            self.split_results,
            self.lexicon_stats,
            self.format,
            self.format_query,
        )

    def _self_name(self) -> str:
        return "Query"


class SearchInterface:
    def build_query(self, args, resource_str: str) -> Query:
        query = Query()
        query.parse_arguments(args, resource_str)
        return query

    def search_with_query(self, query: Query):
        raise NotImplementedError()

    def search_ids(self, args, resource_id: str, entry_ids: str):
        raise NotImplementedError()

    def statistics(self, resource_id: str, field: str):
        raise NotImplementedError()


# class KarpSearch(SearchInterface):
#     def __init__(self):
#         self.impl = SearchInterface()

#     def init(self, impl: SearchInterface):
#         self.impl = impl

#     def build_query(self, args, resource_str: str) -> Query:
#         return self.impl.build_query(args, resource_str)

#     def search_with_query(self, query: Query):
#         return self.impl.search_with_query(query)

#     def search_ids(self, args, resource_id: str, entry_ids: str):
#         return self.impl.search_ids(args, resource_id, entry_ids)

#     def statistics(self, resource_id: str, field: str):
#         return self.impl.statistics(resource_id, field)
