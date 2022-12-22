import abc
from datetime import datetime
import logging
import re
from typing import Dict, List, Optional, Any, Tuple, Union

import elasticsearch
from elasticsearch import exceptions as es_exceptions

from karp.foundation.events import EventBus

from karp.lex.domain.entities import Entry
from karp.search.application.repositories import (
    Index,
    IndexEntry,
    IndexUnitOfWork,
)
from karp.search.domain.errors import UnsupportedField


logger = logging.getLogger("karp")

KARP_CONFIGINDEX = "karp_config"
KARP_CONFIGINDEX_TYPE = "configs"


class MappingRepository(abc.ABC):
    @abc.abstractmethod
    def get_index_name(self, resource_id: str) -> str:
        ...

    @abc.abstractmethod
    def get_alias_name(self, resource_id: str) -> str:
        ...


class Es6MappingRepository(MappingRepository):
    def __init__(
        self,
        es: elasticsearch.Elasticsearch,
        prefix: str = "",
    ):
        self.es = es
        self._prefix = prefix
        self._config_index = f"{prefix}_config" if prefix else KARP_CONFIGINDEX
        self.ensure_config_index_exist()
        analyzed_fields, sortable_fields = self._init_field_mapping()
        self.analyzed_fields: Dict[str, List[str]] = analyzed_fields
        self.sortable_fields: Dict[str, Dict[str, List[str]]] = sortable_fields

    def ensure_config_index_exist(self) -> None:
        if not self.es.indices.exists(index=self._config_index):
            self.es.indices.create(
                index=self._config_index,
                body={
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 1,
                        "refresh_interval": -1,
                    },
                    "mappings": {
                        KARP_CONFIGINDEX_TYPE: {
                            "dynamic": False,
                            "properties": {
                                "index_name": {"type": "text"},
                                "alias_name": {"type": "text"},
                            },
                        }
                    },
                },
            )

    def create_index_name(self, resource_id: str) -> str:
        date = datetime.now().strftime("%Y-%m-%d-%H%M%S%f")
        return f"{self._prefix}{resource_id}_{date}"

    def create_alias_name(self, resource_id: str) -> str:
        return f"{self._prefix}{resource_id}"

    def _update_config(self, resource_id: str) -> dict[str, str]:
        index_name = self.create_index_name(resource_id)
        alias_name = self.create_alias_name(resource_id)
        names = {"index_name": index_name, "alias_name": alias_name}
        self.es.index(
            index=self._config_index,
            id=resource_id,
            doc_type=KARP_CONFIGINDEX_TYPE,
            body=names,
        )
        return names

    def get_index_name(self, resource_id: str) -> str:
        try:
            res = self.es.get(
                index=self._config_index, id=resource_id, doc_type=KARP_CONFIGINDEX_TYPE
            )
        except es_exceptions.NotFoundError as err:
            logger.info(
                "didn't find index_name for resource '%s' details: %s", resource_id, err
            )
            return self._update_config(resource_id)["index_name"]
        return res["_source"]["index_name"]

    def get_alias_name(self, resource_id: str) -> str:
        try:
            res = self.es.get(
                index=self._config_index, id=resource_id, doc_type=KARP_CONFIGINDEX_TYPE
            )
        except es_exceptions.NotFoundError as err:
            logger.info(
                "didn't find alias_name for resource '%s' details: %s", resource_id, err
            )
            return self._update_config(resource_id)["alias_name"]
        return res["_source"]["alias_name"]

    @staticmethod
    def get_analyzed_fields_from_mapping(
        properties: Dict[str, Dict[str, Dict[str, Any]]]
    ) -> List[str]:
        analyzed_fields = []

        for prop_name, prop_values in properties.items():
            if "properties" in prop_values:
                res = Es6MappingRepository.get_analyzed_fields_from_mapping(
                    prop_values["properties"]
                )
                analyzed_fields.extend([f"{prop_name}.{prop}" for prop in res])
            elif prop_values["type"] == "text":
                analyzed_fields.append(prop_name)
        return analyzed_fields

    def _init_field_mapping(
        self,
    ) -> Tuple[Dict[str, List[str]], Dict[str, Dict[str, List[str]]]]:
        """
        Create a field mapping based on the mappings of elasticsearch
        currently the only information we need is if a field is analyzed (i.e. text)
        or not.
        """

        field_mapping: Dict[str, List[str]] = {}
        sortable_fields = {}
        # Doesn't work for tests, can't find resource_definition
        # for resource in resourcemgr.get_available_resources():
        #     mapping = self.es.indices.get_mapping(index=resource.resource_id)
        #     field_mapping[resource.resource_id] = parse_mapping(
        #         next(iter(mapping.values()))['mappings']['entry']['properties']
        #     )
        aliases = self._get_all_aliases()
        mapping: Dict[
            str, Dict[str, Dict[str, Dict[str, Dict]]]
        ] = self.es.indices.get_mapping()
        # print(f"mapping = {mapping}")
        for (alias, index) in aliases:
            if (
                "mappings" in mapping[index]
                and "entry" in mapping[index]["mappings"]
                and "properties" in mapping[index]["mappings"]["entry"]
            ):
                field_mapping[
                    alias
                ] = Es6MappingRepository.get_analyzed_fields_from_mapping(
                    mapping[index]["mappings"]["entry"]["properties"]
                )
                sortable_fields[
                    alias
                ] = Es6MappingRepository.create_sortable_map_from_mapping(
                    mapping[index]["mappings"]["entry"]["properties"]
                )
        return field_mapping, sortable_fields

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

    def translate_sort_fields(
        self, resources: List[str], sort_values: List[str]
    ) -> List[Union[str, Dict[str, Dict[str, str]]]]:
        """Translate sort field to ES sort fields.

        Arguments:
            sort_values {List[str]} -- values to sort by

        Returns:
            List[str] -- values that ES can sort by.
        """
        translated_sort_fields: List[Union[str, Dict[str, Dict[str, str]]]] = []
        for sort_value in sort_values:
            sort_order = None
            if "|" in sort_value:
                sort_value, sort_order = sort_value.split("|", 1)
            for resource_id in resources:
                if sort_order:
                    translated_sort_fields.extend(
                        (
                            {field: {"order": sort_order}}
                            for field in self.translate_sort_field(
                                resource_id, sort_value
                            )
                        )
                    )
                translated_sort_fields.extend(
                    self.translate_sort_field(resource_id, sort_value)
                )

        return translated_sort_fields

    def translate_sort_field(self, resource_id: str, sort_value: str) -> List[str]:
        logger.debug(
            f"es6_indextranslate_sort_field: sortable_fields[{resource_id}] = {self.sortable_fields[resource_id]}"
        )
        if sort_value in self.sortable_fields[resource_id]:
            return self.sortable_fields[resource_id][sort_value]
        else:
            raise UnsupportedField(
                f"You can't sort by field '{sort_value}' for resource '{resource_id}'"
            )

    def on_publish_resource(self, alias_name: str, index_name: str):
        mapping = self._get_index_mappings(index=index_name)
        if (
            "mappings" in mapping[index_name]
            and "entry" in mapping[index_name]["mappings"]
            and "properties" in mapping[index_name]["mappings"]["entry"]
        ):
            self.analyzed_fields[
                alias_name
            ] = Es6MappingRepository.get_analyzed_fields_from_mapping(
                mapping[index_name]["mappings"]["entry"]["properties"]
            )
            self.sortable_fields[
                alias_name
            ] = Es6MappingRepository.create_sortable_map_from_mapping(
                mapping[index_name]["mappings"]["entry"]["properties"]
            )

    @staticmethod
    def create_sortable_map_from_mapping(properties: Dict) -> Dict[str, List[str]]:
        sortable_map = {}

        def parse_prop_value(sort_map, base_name, prop_name, prop_value: Dict):
            if "properties" in prop_value:
                for ext_name, ext_value in prop_value["properties"].items():
                    ext_base_name = f"{base_name}.{ext_name}"
                    parse_prop_value(sort_map, ext_base_name, ext_base_name, ext_value)
                return
            if prop_value["type"] in [
                "boolean",
                "date",
                "double",
                "keyword",
                "long",
                "ip",
            ]:
                sort_map[base_name] = [prop_name]
                sort_map[prop_name] = [prop_name]
                return
            if prop_value["type"] == "text":
                if "fields" in prop_value:
                    for ext_name, ext_value in prop_value["fields"].items():
                        parse_prop_value(
                            sort_map, base_name, f"{base_name}.{ext_name}", ext_value
                        )
                return

        for prop_name, prop_value in properties.items():
            parse_prop_value(sortable_map, prop_name, prop_name, prop_value)
            # if prop_value["type"] in ["boolean", "date", "double", "keyword", "long", "ip"]:
            #     sortable_map[prop_name] = prop_name
            # if prop_value["type"] == "text":
            #     if "fields" in prop_value:

        return sortable_map


# def parse_sortable_fields(properties: Dict[str, Any]) -> Dict[str, List[str]]:
#     for prop_name, prop_value in properties.items():
#         if prop_value["type"] in ["boolean", "date", "double", "keyword", "long", "ip"]:
#             return [prop_name]


def _create_es_mapping(config):
    es_mapping = {"dynamic": False, "properties": {}}

    fields = config["fields"]

    def recursive_field(parent_schema, parent_field_name, parent_field_def):
        if parent_field_def.get("virtual", False):
            fun = parent_field_def["function"]
            if list(fun.keys())[0] == "multi_ref":
                res_object = fun["multi_ref"]["result"]
                recursive_field(parent_schema, f"v_{parent_field_name}", res_object)
            if "result" in fun:
                res_object = fun["result"]
                recursive_field(parent_schema, f"v_{parent_field_name}", res_object)
            return
        if parent_field_def.get("ref"):
            if "field" in parent_field_def["ref"]:
                res_object = parent_field_def["ref"]["field"]
            else:
                res_object = {}
                res_object.update(parent_field_def)
                del res_object["ref"]
            recursive_field(parent_schema, f"v_{parent_field_name}", res_object)
        if parent_field_def["type"] != "object":
            # TODO this will not work when we have user defined types, s.a. saldoid
            # TODO number can be float/non-float, strings can be keyword or text in need of analyzing etc.
            if parent_field_def["type"] == "integer":
                mapped_type = "long"
            elif parent_field_def["type"] == "number":
                mapped_type = "double"
            elif parent_field_def["type"] == "boolean":
                mapped_type = "boolean"
            elif parent_field_def["type"] == "string":
                mapped_type = "text"
            elif parent_field_def["type"] == "long_string":
                mapped_type = "text"
            else:
                mapped_type = "keyword"
            result = {"type": mapped_type}
            if parent_field_def["type"] == "string":
                result["fields"] = {"raw": {"type": "keyword"}}
        else:
            result = {"properties": {}}

            for child_field_name, child_field_def in parent_field_def["fields"].items():
                recursive_field(result, child_field_name, child_field_def)

        parent_schema["properties"][parent_field_name] = result

    for field_name, field_def in fields.items():
        logger.debug(f"creating mapping for field '{field_name}'")
        recursive_field(es_mapping, field_name, field_def)

    return es_mapping


def create_es6_mapping(config: Dict) -> Dict:
    mapping = _create_es_mapping(config)
    mapping["settings"] = {
        "analysis": {
            "analyzer": {
                "default": {
                    "char_filter": [
                        "compound",
                        "swedish_aa",
                        "swedish_ae",
                        "swedish_oe",
                    ],
                    "filter": ["swedish_folding", "lowercase"],
                    "tokenizer": "standard",
                }
            },
            "char_filter": {
                "compound": {
                    "pattern": "-",
                    "replacement": "",
                    "type": "pattern_replace",
                },
                "swedish_aa": {
                    "pattern": "[Ǻǻ]",
                    "replacement": "å",
                    "type": "pattern_replace",
                },
                "swedish_ae": {
                    "pattern": "[æÆǞǟ]",
                    "replacement": "ä",
                    "type": "pattern_replace",
                },
                "swedish_oe": {
                    "pattern": "[ØøŒœØ̈ø̈ȪȫŐőÕõṌṍṎṏȬȭǾǿǬǭŌōṒṓṐṑ]",
                    "replacement": "ö",
                    "type": "pattern_replace",
                },
            },
            "filter": {
                "swedish_folding": {
                    "type": "icu_folding",
                    "unicodeSetFilter": "[^åäöÅÄÖ]",
                },
                "swedish_sort": {"language": "sv", "type": "icu_collation"},
            },
        }
    }
    return mapping


class Es6MappingRepositoryUnitOfWork(IndexUnitOfWork):
    def __init__(
        self,
        es: elasticsearch.Elasticsearch,
        event_bus: EventBus,
    ) -> None:
        super().__init__(event_bus=event_bus)
        self._index = Es6MappingRepository(es=es)

    # @classmethod
    # def from_dict(cls, **kwargs):
    #     return cls()

    def _commit(self):
        logger.debug("Calling _commit in Es6MappingRepositoryUnitOfWork")

    def rollback(self):
        return super().rollback()

    @property
    def repo(self) -> Es6MappingRepository:
        return self._index

    def _close(self):
        pass
