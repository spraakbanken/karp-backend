# pyright: standard
import logging
import re
from dataclasses import dataclass
from itertools import groupby
from typing import Any, Iterable

import elasticsearch
import methodtools
from injector import inject

from karp.lex.infrastructure import ResourceRepository
from karp.main.errors import FieldDoesNotExist, IncompatibleResources, SortError

logger = logging.getLogger("karp")


@dataclass
class Field:
    """Information about a field in the index."""

    path: list[str]  # e.g. if the field name is "foo.bar" then this is ["foo", "bar"]
    type: str  # e.g. "text"

    extra: bool | None = False  # True for things like .raw fields

    @property
    def name(self) -> str:
        return ".".join(self.path)

    @property
    def parent(self) -> str | None:
        if self.path:
            return ".".join(self.path[:-1])
        return None

    @property
    def analyzed(self) -> bool:
        return self.type == "text"

    @property
    def sort_form(self) -> str | None:
        """Return which field should be used when we ask to sort on this field."""
        if self.type in [
            "boolean",
            "date",
            "double",
            "keyword",
            "long",
            "ip",
        ]:
            return self.name

        if self.analyzed:
            return self.name + ".sort"
        return None


# these fields are searchable using the keys as identifiers, prefixed by "@"
internal_fields = {
    "last_modified_by": Field(path=["_last_modified_by"], type="keyword"),
    "last_modified": Field(path=["_last_modified"], type="date"),
    "version": Field(path=["_entry_version"], type="integer"),
    "resource": Field(path=["_resource_id"], type="keyword"),
}


class EsMappingRepository:
    @inject
    def __init__(self, es: elasticsearch.Elasticsearch, resource_repo: ResourceRepository):
        self.es = es

        self.fields: dict[str, dict[str, Field]] = {}
        self.sortable_fields: dict[str, dict[str, Field]] = {}
        self.resource_repo = resource_repo

        aliases = self._get_all_aliases()
        self.aliases = dict(aliases)
        self.reverse_aliases = {index: alias for alias, index in aliases}
        self._update_field_mapping(aliases)

    def is_nested(self, resource_ids: list[str], field):
        """
        Checks if field is nested (collection: true and type: object)
        Raises exception if the field is configured differently in resources
        """

        def is_nested_single_resource(resource_id):
            fields = self.fields[resource_id]
            return field in fields and fields[field].type == "nested"

        # TODO this cannot be the clearest way to achieve checking if all elements in a list are the same...
        g = groupby([is_nested_single_resource(resource_id) for resource_id in resource_ids])
        is_nested = next(g)[0]
        # if there is a next value for interator, not all values are the same
        if next(g, False):
            raise IncompatibleResources(field=field)
        return is_nested

    def get_nest_levels(self, resource_id: str, field):
        """
        Given a dot-separated path ("apa.bepa.cepa") it will check if any of the fields in the path is
        nested and return those, path included, otherwise return [].

        Example: if both "apa" and "apa.bepa" are nested, it will return ["apa", "apa.bepa"]
        """
        nest_levels = []
        subfield = None
        parts = field.split(".")[0:-1]
        for part in parts:
            subfield = ".".join([subfield, part]) if subfield else part
            if self.is_nested([resource_id], subfield):
                nest_levels.append(subfield)
        return nest_levels

    def get_non_nested_children(self, resources, field_path) -> Iterable[str]:
        """
        Return each field under field_path that is not a nested. Check every given resource
        and make sure that the fields are the same.
        """
        res = {resource: [] for resource in resources}
        for resource in resources:
            for name in self.fields[resource]:
                # find fields that are children of field_path but not children of other nesteds
                if name.startswith(field_path + ".") and name != field_path:
                    nest_levels = self.get_nest_levels(resource, name)
                    skip = False
                    for nested in nest_levels:
                        if nested == field_path or field_path.startswith(nested):
                            # ignore prefixes
                            continue
                        if name.startswith(nested) or name == nested:
                            skip = True
                    if not skip:
                        res[resource].append(name)
        if not all(x == res[resources[0]] for x in res.values()):
            raise IncompatibleResources(field="N/A, turn off highlighting for query to succeed.")
        return res[resources[0]]

    def get_field(self, resource_ids, field_name):
        if field_name == "@id":
            return Field(path=["_id"], type="keyword")
        if field_name[0] == "@":
            return internal_fields[field_name[1:]]

        # check that field_name is defined with the same type in all given resources
        # assume that resource_ids exist
        fields = [self.fields[resource_id].get(field_name) for resource_id in resource_ids]
        if None in fields:
            # the field does not exist in at least one of the selected resources
            raise FieldDoesNotExist(
                resource_ids=[
                    resource_id for resource_id, field in zip(resource_ids, fields, strict=False) if not field
                ],
                field=field_name,
            )
        if fields.count(fields[0]) != len(fields):
            raise IncompatibleResources(field=field_name)
        return fields[0]

    def _update_field_mapping(self, aliases: list[tuple[str, str]]):
        """
        Create a field mapping based on the mappings of elasticsearch.
        """

        mapping: dict[str, dict[str, dict[str, dict[str, dict]]]] = self.es.indices.get_mapping().body
        for alias, index in aliases:
            if "mappings" in mapping[index] and "properties" in mapping[index]["mappings"]:
                self.fields[alias] = self._get_fields_from_mapping(mapping[index]["mappings"]["properties"])
                self.sortable_fields[alias] = {}
                for field in self.fields[alias].values():
                    if field.sort_form in self.fields[alias]:
                        sort_form = self.fields[alias][field.sort_form]
                        self.sortable_fields[alias][field.name] = sort_form

    @staticmethod
    def _get_fields_from_mapping(
        properties: dict[str, dict[str, dict[str, Any]]],
        path: list[str] | None = None,
        extra: bool | None = False,
    ) -> dict[str, Field]:
        if path is None:
            path = []
        fields = {}

        for prop_name, prop_value in properties.items():
            prop_path = path + [prop_name]
            if "properties" in prop_value and "type" not in prop_value:
                field_type = "object"
            else:
                field_type = str(prop_value["type"])
            field = Field(path=prop_path, type=field_type, extra=extra)
            fields[field.name] = field

            # Add all recursive fields too
            res1 = EsMappingRepository._get_fields_from_mapping(prop_value.get("properties", {}), prop_path)
            res2 = EsMappingRepository._get_fields_from_mapping(prop_value.get("fields", {}), prop_path, True)
            fields.update(res1)
            fields.update(res2)

        return fields

    def _get_index_mappings(self, index: str | None = None) -> dict[str, dict[str, dict[str, dict[str, dict]]]]:
        return self.es.indices.get_mapping(index=index).body

    def _get_all_aliases(self) -> list[tuple[str, str]]:
        """
        :return: a list of tuples (alias_name, index_name)
        """
        result = self.es.cat.aliases(h="alias,index")
        logger.debug(f"{result}")
        index_names = []
        for index_name in result.split("\n")[:-1]:
            logger.debug(f"index_name = {index_name}")
            if index_name[0] != ".":
                if match := re.search(r"([^ ]*) +(.*)", index_name):
                    groups = match.groups()
                    alias = groups[0]
                    index = groups[1]
                    index_names.append((alias, index))
        return index_names

    def get_fields_as_tree(self, resource_ids: list[str], path: str) -> dict[str, Any]:
        """
        Create a dict that represents all fields on path as a tree
        sort of:
        field1.field2, field1.field3 ->
        field1 {
            field2: ...
            field3: ...
        }
        """
        tree = {}
        for resource_id in resource_ids:
            for field_name, field_def in self.fields[resource_id].items():
                # only include fields in the given path
                if field_name.startswith(path[-1]):
                    parts = field_name.split(".")
                    current = tree

                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {"def": field_def, "children": {}}
                        current = current[part]["children"]

                    if parts[-1] in ["raw", "sort"]:
                        continue

                    # check that the types are the same for leafs
                    if parts[-1] not in current:
                        current[parts[-1]] = {"def": field_def, "children": {}}
                    else:
                        node = current[parts[-1]]
                        if node["def"] != field_def or node["children"]:
                            raise ValueError(f"Type of {field_name} is inconclusive for resources: {resource_ids}")
        return tree

    @methodtools.lru_cache(maxsize=None)
    def _load_sort(self, resource_id: str) -> list[str] | None:
        resource = self.resource_repo.by_resource_id(resource_id)
        # TODO ResourceConfig model allows for sort or id to be None also sort to be list[str] and this
        # code does not account for that, set dict-values to Any for now
        sort = resource.config.sort or resource.config.id
        if sort is None:
            return None
        elif not isinstance(sort, list):
            return [sort]
        else:
            return sort

    def get_default_sort(self, resources: list[str]) -> list[str] | None:
        """
        Returns the default sort field for the resources. Throws an error
        if the resources have different sort fields, or if those sort  fields
        have different types (i.e. if _raw must be added)
        """

        def _translate_unless_none(resource):
            maybe_sort_fields = self._load_sort(resource)
            return maybe_sort_fields and [
                self._translate_sort_field(resource, sort_field) for sort_field in maybe_sort_fields
            ]

        g = groupby(map(_translate_unless_none, resources))
        sort_field = next(g)[0]
        if next(g, False):
            raise SortError(resource_ids=resources)
        return sort_field

    def translate_sort_fields(
        self, resources: list[str], sort_values: list[str]
    ) -> list[str | dict[str, dict[str, str]]]:
        """Translate sort field to ES sort fields.

        Arguments:
            resources: the resources to use
            sort_values: {list[str]} -- values to sort by

        Returns
            list[str] -- values that ES can sort by.
        """
        translated_sort_fields: list[str | dict[str, dict[str, str]]] = []
        for sort_value in sort_values:
            sort_order = None
            if "|" in sort_value:
                sort_value, sort_order = sort_value.split("|", 1)

            field_context = {}
            if "." in sort_value:
                # check if parent is nested (it could be nesting on another level, but we don't support it yet)
                path, _ = sort_value.rsplit(".", 1)
                if self.is_nested(resources, path):
                    field_context["nested"] = {"path": path}

            if sort_order:
                field_context["order"] = sort_order

            for resource_id in resources:
                field = self._translate_sort_field(resource_id, sort_value)
                if field_context:
                    translated_sort_fields.append({field: field_context})
                else:
                    translated_sort_fields.append(field)

        return translated_sort_fields

    def _translate_sort_field(self, resource_id: str, sort_value: str) -> str:
        if sort_value in self.sortable_fields[resource_id]:
            return self.sortable_fields[resource_id][sort_value].name
        else:
            raise SortError(resource_ids=[resource_id], sort_value=sort_value)
