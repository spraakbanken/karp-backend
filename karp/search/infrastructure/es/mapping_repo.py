import logging
import re
from dataclasses import dataclass
from itertools import groupby
from typing import Any, Dict, List, Optional, Tuple, Union

import elasticsearch
from injector import inject

from karp.lex.infrastructure import ResourceRepository
from karp.main.errors import KarpError
from karp.search.domain.errors import UnsupportedField

logger = logging.getLogger("karp")


@dataclass
class Field:
    """Information about a field in the index."""

    path: list[str]  # e.g. if the field name is "foo.bar" then this is ["foo", "bar"]
    type: str  # e.g. "text"

    extra: Optional[bool] = False  # True for things like .raw fields

    @property
    def name(self) -> str:
        return ".".join(self.path)

    @property
    def lastname(self) -> str:
        return self.path[-1]

    @property
    def parent(self) -> Optional[str]:
        if self.path:
            return ".".join(self.path[:-1])
        return None

    @property
    def analyzed(self) -> bool:
        return self.type == "text"

    @property
    def sort_form(self) -> Optional[str]:
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


class EsMappingRepository:
    @inject
    def __init__(self, es: elasticsearch.Elasticsearch, resource_repo: ResourceRepository):
        self.es = es

        self.fields: Dict[str, Dict[str, Field]] = {}
        self.sortable_fields: Dict[str, Dict[str, Field]] = {}
        resources = resource_repo.get_published_resources()

        self.default_sort: Dict[str, str] = {
            resource.resource_id: resource.config.sort or resource.config.id
            for resource in resources
        }

        aliases = self._get_all_aliases()
        self._update_field_mapping(aliases)

    def is_nested(self, resource_id, field):
        fields = self.fields[resource_id]
        return field in fields and fields[field].type == "nested"

    def get_nest_levels(self, resource_id, field):
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
            if self.is_nested(resource_id, subfield):
                nest_levels.append(subfield)
        return nest_levels

    def get_nested_fields(self, resource_id):
        for field_name, field_def in self.fields[resource_id].items():
            if field_def.type == "nested":
                yield field_name

    def _update_field_mapping(self, aliases: List[Tuple[str, str]]):
        """
        Create a field mapping based on the mappings of elasticsearch.
        """

        mapping: Dict[str, Dict[str, Dict[str, Dict[str, Dict]]]] = self.es.indices.get_mapping()
        for alias, index in aliases:
            if "mappings" in mapping[index] and "properties" in mapping[index]["mappings"]:
                self.fields[alias] = self._get_fields_from_mapping(
                    mapping[index]["mappings"]["properties"]
                )
                self.sortable_fields[alias] = {}
                for field in self.fields[alias].values():
                    if field.sort_form in self.fields[alias]:
                        sort_form = self.fields[alias][field.sort_form]
                        self.sortable_fields[alias][field.name] = sort_form
                        self.sortable_fields[alias][field.lastname] = sort_form

    @staticmethod
    def _get_fields_from_mapping(
        properties: Dict[str, Dict[str, Dict[str, Any]]],
        path: Optional[list[str]] = None,
        extra: Optional[bool] = False,
    ) -> dict[str, Field]:
        if path is None:
            path = []
        fields = {}

        for prop_name, prop_value in properties.items():
            prop_path = path + [prop_name]
            if "properties" in prop_value and "type" not in prop_value:
                field_type = "object"
            else:
                field_type = prop_value["type"]
            field = Field(path=prop_path, type=field_type, extra=extra)
            fields[field.name] = field

            # Add all recursive fields too
            res1 = EsMappingRepository._get_fields_from_mapping(
                prop_value.get("properties", {}), prop_path
            )
            res2 = EsMappingRepository._get_fields_from_mapping(
                prop_value.get("fields", {}), prop_path, True
            )
            fields.update(res1)
            fields.update(res2)

        return fields

    def _get_index_mappings(
        self, index: Optional[str] = None
    ) -> Dict[str, Dict[str, Dict[str, Dict[str, Dict]]]]:
        kwargs = {"index": index} if index is not None else {}
        return self.es.indices.get_mapping(**kwargs)

    def _get_all_aliases(self) -> List[Tuple[str, str]]:
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

    def check_resource_is_published(self, resource_id):
        return resource_id in self.default_sort

    def get_default_sort(self, resources: List[str]) -> Optional[str]:
        """
        Returns the default sort field for the resources. Throws an error
        if the resources have different sort fields, or if those sort  fields
        have different types (i.e. if _raw must be added)
        """

        def _translate_unless_none(resource):
            maybe_sort_field1 = self.default_sort.get(resource)
            return maybe_sort_field1 and self._translate_sort_field(resource, maybe_sort_field1)

        g = groupby(map(_translate_unless_none, resources))
        sort_field = next(g)[0]
        if next(g, False):
            raise KarpError(
                message="Resources do not share default sort field, set sort field explicitly"
            )
        return sort_field

    def translate_sort_fields(
        self, resources: List[str], sort_values: List[str]
    ) -> List[Union[str, Dict[str, Dict[str, str]]]]:
        """Translate sort field to ES sort fields.

        Arguments:
            resources: the resources to use
            sort_values: {List[str]} -- values to sort by

        Returns
            List[str] -- values that ES can sort by.
        """
        translated_sort_fields: List[Union[str, Dict[str, Dict[str, str]]]] = []
        for sort_value in sort_values:
            sort_order = None
            if "|" in sort_value:
                sort_value, sort_order = sort_value.split("|", 1)
            for resource_id in resources:
                if sort_order:
                    field = self._translate_sort_field(resource_id, sort_value)
                    translated_sort_fields.append({field: {"order": sort_order}})
                translated_sort_fields.append(
                    self._translate_sort_field(resource_id, sort_value)
                )

        return translated_sort_fields

    def _translate_sort_field(self, resource_id: str, sort_value: str) -> str:
        if sort_value in self.sortable_fields[resource_id]:
            return self.sortable_fields[resource_id][sort_value].name
        else:
            raise UnsupportedField(
                f"You can't sort by field '{sort_value}' for resource '{resource_id}'"
            )
