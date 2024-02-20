import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import elasticsearch
from elasticsearch import exceptions as es_exceptions

from karp.lex.domain.entities import Entry
from karp.search.domain.errors import UnsupportedField

logger = logging.getLogger("karp")

KARP_CONFIGINDEX = "karp_config"


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
                        "dynamic": False,
                        "properties": {
                            "index_name": {"type": "text"},
                            "alias_name": {"type": "text"},
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
            res = self.es.get(index=self._config_index, id=resource_id)
        except es_exceptions.NotFoundError as err:
            logger.info("didn't find index_name for resource '%s' details: %s", resource_id, err)
            return self._update_config(resource_id)["index_name"]
        return res["_source"]["index_name"]

    def get_alias_name(self, resource_id: str) -> str:
        try:
            res = self.es.get(index=self._config_index, id=resource_id)
        except es_exceptions.NotFoundError as err:
            logger.info("didn't find alias_name for resource '%s' details: %s", resource_id, err)
            return self._update_config(resource_id)["alias_name"]
        return res["_source"]["alias_name"]

    @staticmethod
    def get_analyzed_fields_from_mapping(
        properties: Dict[str, Dict[str, Dict[str, Any]]],
    ) -> List[str]:
        analyzed_fields = []

        for prop_name, prop_values in properties.items():
            if "properties" in prop_values:
                res = EsMappingRepository.get_analyzed_fields_from_mapping(
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
        aliases = self._get_all_aliases()
        mapping: Dict[str, Dict[str, Dict[str, Dict[str, Dict]]]] = self.es.indices.get_mapping()
        for alias, index in aliases:
            if "mappings" in mapping[index] and "properties" in mapping[index]["mappings"]:
                field_mapping[alias] = EsMappingRepository.get_analyzed_fields_from_mapping(
                    mapping[index]["mappings"]["properties"]
                )
                sortable_fields[alias] = EsMappingRepository.create_sortable_map_from_mapping(
                    mapping[index]["mappings"]["properties"]
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
                    translated_sort_fields.extend(
                        (
                            {field: {"order": sort_order}}
                            for field in self.translate_sort_field(resource_id, sort_value)
                        )
                    )
                translated_sort_fields.extend(self.translate_sort_field(resource_id, sort_value))

        return translated_sort_fields

    def translate_sort_field(self, resource_id: str, sort_value: str) -> List[str]:
        logger.debug(
            f"es_indextranslate_sort_field: sortable_fields[{resource_id}] = {self.sortable_fields[resource_id]}"
        )
        if sort_value in self.sortable_fields[resource_id]:
            return self.sortable_fields[resource_id][sort_value]
        else:
            raise UnsupportedField(
                f"You can't sort by field '{sort_value}' for resource '{resource_id}'"
            )

    def on_publish_resource(self, alias_name: str, index_name: str):
        mapping = self._get_index_mappings(index=index_name)
        if "mappings" in mapping[index_name] and "properties" in mapping[index_name]["mappings"]:
            self.analyzed_fields[
                alias_name
            ] = EsMappingRepository.get_analyzed_fields_from_mapping(
                mapping[index_name]["mappings"]["properties"]
            )
            self.sortable_fields[
                alias_name
            ] = EsMappingRepository.create_sortable_map_from_mapping(
                mapping[index_name]["mappings"]["properties"]
            )

    @staticmethod
    def create_sortable_map_from_mapping(
        properties: Dict,
    ) -> Dict[str, List[str]]:
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

        return sortable_map
