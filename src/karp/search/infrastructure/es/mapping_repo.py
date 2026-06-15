# pyright: strict
import functools
import logging
import re
from dataclasses import dataclass
from itertools import groupby
from typing import Any, Iterable

from karp.globals import es
from karp.lex.infrastructure.sql import resource_repository
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


@functools.cache
def _get_fields(resource_id: str) -> dict[str, Field]:
    return _update_field_mapping()[0][resource_id]


@functools.cache
def is_nested(resource_ids: tuple[str], field: str):
    """
    Checks if field is nested (collection: true and type: object)
    Raises exception if the field is configured differently in resources
    """

    def is_nested_single_resource(resource_id: str):
        fields = _get_fields(resource_id)
        return field in fields and fields[field].type == "nested"

    # TODO this cannot be the clearest way to achieve checking if all elements in a list are the same...
    g = groupby([is_nested_single_resource(resource_id) for resource_id in resource_ids])
    is_nested = next(g)[0]
    # if there is a next value for interator, not all values are the same
    if next(g, False):
        raise IncompatibleResources(field=field)
    return is_nested


@functools.cache
def get_nest_levels(resource_id: str, field: str) -> list[str]:
    """
    Given a dot-separated path ("apa.bepa.cepa") it will check if any of the fields in the path is
    nested and return those, path included, otherwise return [].

    Example: if both "apa" and "apa.bepa" are nested, it will return ["apa", "apa.bepa"]
    """
    nest_levels: list[str] = []
    subfield = None
    parts = field.split(".")[0:-1]
    for part in parts:
        subfield = ".".join([subfield, part]) if subfield else part
        if is_nested((resource_id,), subfield):
            nest_levels.append(subfield)
    return nest_levels


@functools.cache
def get_non_nested_children(resources: tuple[str, ...], field_path: str) -> Iterable[str]:
    """
    Return each field under field_path that is not a nested. Check every given resource
    and make sure that the fields are the same.
    """
    res: dict[str, list[str]] = {resource: [] for resource in resources}
    for resource in resources:
        for name in _get_fields(resource):
            # find fields that are children of field_path but not children of other nesteds
            if name.startswith(field_path + ".") and name != field_path:
                nest_levels = get_nest_levels(resource, name)
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


@functools.cache
def get_field(resource_ids: tuple[str, ...], field_name: str, allow_missing: bool = False) -> Field | None:
    if field_name == "@id":
        return Field(path=["_id"], type="keyword")
    if field_name[0] == "@":
        return internal_fields[field_name[1:]]

    # check that field_name is defined with the same type in all given resources
    # assume that resource_ids exist
    fields = [_get_fields(resource_id).get(field_name) for resource_id in resource_ids]

    if fields.count(fields[0]) != len(fields):
        raise IncompatibleResources(field=field_name)

    if allow_missing and (len(fields) == 0 or fields[0] is None):
        return None

    if None in fields:
        # the field does not exist in at least one of the selected resources
        raise FieldDoesNotExist(
            resource_ids=[resource_id for resource_id, field in zip(resource_ids, fields, strict=False) if not field],
            field=field_name,
        )
    return fields[0]


@functools.cache
def get_reverse_aliases():
    aliases = _get_all_aliases()
    return {index: alias for alias, index in aliases}


@functools.cache
def _update_field_mapping() -> tuple[dict[str, dict[str, Field]], dict[str, dict[str, Field]]]:
    """
    Create a field mapping based on the mappings of elasticsearch.
    """
    fields: dict[str, dict[str, Field]] = {}
    sortable_fields: dict[str, dict[str, Field]] = {}
    aliases = _get_all_aliases()
    mapping: dict[str, dict[str, dict[str, dict[str, dict[str, Any]]]]] = es.indices.get_mapping().body
    for alias, index in aliases:
        if "mappings" in mapping[index] and "properties" in mapping[index]["mappings"]:
            fields[alias] = _get_fields_from_mapping(mapping[index]["mappings"]["properties"])
            sortable_fields[alias] = {}
            for field in fields[alias].values():
                if field.sort_form in fields[alias]:
                    sort_form = fields[alias][field.sort_form]
                    sortable_fields[alias][field.name] = sort_form
    return fields, sortable_fields


def _get_fields_from_mapping(
    properties: dict[str, dict[str, dict[str, Any]]],
    path: list[str] | None = None,
    extra: bool | None = False,
) -> dict[str, Field]:
    if path is None:
        path = []
    fields: dict[str, Field] = {}

    for prop_name, prop_value in properties.items():
        prop_path = path + [prop_name]
        if "properties" in prop_value and "type" not in prop_value:
            field_type = "object"
        else:
            field_type = str(prop_value["type"])
        field = Field(path=prop_path, type=field_type, extra=extra)
        fields[field.name] = field

        # Add all recursive fields too
        res1 = _get_fields_from_mapping(prop_value.get("properties", {}), prop_path)
        res2 = _get_fields_from_mapping(prop_value.get("fields", {}), prop_path, True)
        fields.update(res1)
        fields.update(res2)

    return fields


@functools.cache
def _get_all_aliases() -> list[tuple[str, str]]:
    """
    :return: a list of tuples (alias_name, index_name)
    """
    result = es.cat.aliases(h="alias,index")
    logger.debug(f"{result}")
    index_names: list[tuple[str, str]] = []
    for index_name in result.split("\n")[:-1]:
        logger.debug(f"index_name = {index_name}")
        if index_name[0] != ".":
            if match := re.search(r"([^ ]*) +(.*)", index_name):
                groups = match.groups()
                alias = groups[0]
                index = groups[1]
                index_names.append((alias, index))
    return index_names


@functools.cache
def get_fields_as_tree(resource_ids: tuple[str, ...], path: tuple[str, ...]) -> dict[str, Any]:
    """
    Create a dict that represents all fields on path as a tree
    sort of:
    field1.field2, field1.field3 ->
    field1 {
        field2: ...
        field3: ...
    }
    """
    tree: dict[str, Any] = {}
    for resource_id in resource_ids:
        for field_name, field_def in _get_fields(resource_id).items():
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


@functools.cache
def _load_sort(resource_id: str) -> list[str] | None:
    resource = resource_repository.by_resource_id(resource_id)
    # TODO ResourceConfig model allows for sort or id to be None also sort to be list[str] and this
    # code does not account for that, set dict-values to Any for now
    sort = resource.config.sort or resource.config.id
    if sort is None:
        return None
    elif not isinstance(sort, list):
        return [sort]
    else:
        return sort


@functools.cache
def get_default_sort(resources: tuple[str]) -> list[str] | None:
    """
    Returns the default sort field for the resources. Throws an error
    if the resources have different sort fields, or if those sort  fields
    have different types (i.e. if _raw must be added)
    """

    def _translate_unless_none(resource: str):
        maybe_sort_fields = _load_sort(resource)
        return maybe_sort_fields and [_translate_sort_field(resource, sort_field) for sort_field in maybe_sort_fields]

    g = groupby(map(_translate_unless_none, resources))
    sort_field = next(g)[0]
    if next(g, False):
        raise SortError(resource_ids=list(resources))
    return sort_field


@functools.cache
def translate_sort_fields(resources: tuple[str], sort_values: tuple[str]) -> list[str | dict[str, dict[str, str]]]:
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
            if is_nested(resources, path):
                field_context["nested"] = {"path": path}

        if sort_order:
            field_context["order"] = sort_order

        for resource_id in resources:
            field = _translate_sort_field(resource_id, sort_value)
            if field_context:
                translated_sort_fields.append({field: field_context})
            else:
                translated_sort_fields.append(field)

    return translated_sort_fields


def _translate_sort_field(resource_id: str, sort_value: str) -> str:
    sortable_fields = _update_field_mapping()[1][resource_id]
    if sort_value in sortable_fields:
        return sortable_fields[sort_value].name
    else:
        raise SortError(resource_ids=[resource_id], sort_value=sort_value)
