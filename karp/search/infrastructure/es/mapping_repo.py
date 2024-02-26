import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import elasticsearch
from elasticsearch import exceptions as es_exceptions

from karp.lex.domain.entities import Entry
from karp.search.domain.errors import UnsupportedField
from dataclasses import dataclass

logger = logging.getLogger("karp")

KARP_CONFIGINDEX = "karp_config"
KARP_CONFIGINDEX_TYPE = "configs"

@dataclass
class FieldInfo:
    """Information about a field in the index."""

    path: list[str]
    type: str

    @property
    def analyzed(self) -> bool:
        return self.type == "text"

    @property
    def name(self) -> str:
        return ".".join(self.path)

    @property
    def lastname(self) -> str:
        return self.path[-1]

    @property
    def parent(self) -> str:
        return ".".join(self.path[:-1])

class EsMappingRepository:
    def __init__(
        self,
        es: elasticsearch.Elasticsearch,
        prefix: str = "",
    ):
        self.es = es
        self._prefix = prefix
        self._config_index = f"{prefix}_config" if prefix else KARP_CONFIGINDEX
        self.ensure_config_index_exist()
        fields = self._init_field_mapping()
        sortable_fields = self.get_sortable_fields(fields)
        self.fields: Dict[str, Dict[str, FieldInfo]] = fields
        self.sortable_fields: Dict[str, Dict[str, FieldInfo]] = sortable_fields

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

    def create_index_and_alias_name(self, resource_id: str) -> dict[str, str]:
        return self._update_config(resource_id)

    def get_name_base(self, resource_id: str) -> str:
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

    def delete_from_config(self, resource_id: str) -> None:
        try:
            self.es.delete(
                index=self._config_index,
                doc_type="configs",
                id=resource_id,
                refresh=True,
            )
        except elasticsearch.exceptions.ElasticsearchException:
            logger.exception(
                "Error deleting from config",
                extra={
                    "resource_id": resource_id,
                    "index_name": self._config_index,
                },
            )

    def get_index_name(self, resource_id: str) -> str:
        try:
            res = self.es.get(
                index=self._config_index, id=resource_id, doc_type=KARP_CONFIGINDEX_TYPE
            )
        except es_exceptions.NotFoundError as err:
            logger.info("didn't find index_name for resource '%s' details: %s", resource_id, err)
            return self._update_config(resource_id)["index_name"]
        return res["_source"]["index_name"]

    def get_alias_name(self, resource_id: str) -> str:
        try:
            res = self.es.get(
                index=self._config_index, id=resource_id, doc_type=KARP_CONFIGINDEX_TYPE
            )
        except es_exceptions.NotFoundError as err:
            logger.info("didn't find alias_name for resource '%s' details: %s", resource_id, err)
            return self._update_config(resource_id)["alias_name"]
        return res["_source"]["alias_name"]

    @staticmethod
    def get_fields_from_mapping(
        properties: Dict[str, Dict[str, Dict[str, Any]]], path: list[str] = None
    ) -> Dict[str, FieldInfo]:
        if path is None: path = []
        fields = {}

        for prop_name, prop_value in properties.items():
            prop_path = path + [prop_name]
            if "properties" in prop_value and "type" not in prop_value:
                field_type = "object"
            else:
                field_type = prop_value["type"]
            field_info = FieldInfo(path = prop_path, type = field_type)
            fields[field_info.name] = field_info

            # Add all recursive fields too
            res1 = EsMappingRepository.get_fields_from_mapping(prop_value.get("properties", {}), prop_path)
            res2 = EsMappingRepository.get_fields_from_mapping(prop_value.get("fields", {}), prop_path)
            fields.update(res1)
            fields.update(res2)

        return fields

    @staticmethod
    def get_sortable_fields(fields: Dict[str, FieldInfo]) -> Dict[str, FieldInfo]:
        result = {}
        for field in fields.values():
            if field.type in [
                "boolean",
                "date",
                "double",
                "keyword",
                "long",
                "ip",
            ]:
                result[field.name] = field
                result[field.lastname] = field

            if field.analyzed:
                field_raw = field.name + ".raw"
                if field_raw in fields:
                    result[field.name] = fields[field_raw]
                    result[field.lastname] = fields[field_raw]

        return result

    def _init_field_mapping(self) -> Dict[str, Dict[str, FieldInfo]]:
        """
        Create a field mapping based on the mappings of elasticsearch.
        """

        field_mapping: Dict[str, Dict[str, FieldInfo]] = {}
        aliases = self._get_all_aliases()
        mapping: Dict[str, Dict[str, Dict[str, Dict[str, Dict]]]] = self.es.indices.get_mapping()
        for alias, index in aliases:
            if (
                "mappings" in mapping[index]
                and "entry" in mapping[index]["mappings"]
                and "properties" in mapping[index]["mappings"]["entry"]
            ):
                field_mapping[alias] = EsMappingRepository.get_fields_from_mapping(
                    mapping[index]["mappings"]["entry"]["properties"]
                )
        return field_mapping

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
                    field = self.translate_sort_field(resource_id, sort_value)
                    translated_sort_fields.append({field: {"order": sort_order}})
                translated_sort_fields.append(self.translate_sort_field(resource_id, sort_value))

        return translated_sort_fields

    def translate_sort_field(self, resource_id: str, sort_value: str) -> str:
        logger.debug(
            f"es_indextranslate_sort_field: sortable_fields[{resource_id}] = {self.sortable_fields[resource_id]}"
        )
        if sort_value in self.sortable_fields[resource_id]:
            return self.sortable_fields[resource_id][sort_value].name
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
            fields = self.get_fields_from_mapping(
                mapping[index_name]["mappings"]["entry"]["properties"]
            )
            sortable_fields = self.get_sortable_fields(fields)
            self.fields[alias_name] = fields
            self.sortable_fields[alias_name] = sortable_fields
