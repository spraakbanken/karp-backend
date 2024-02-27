import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import elasticsearch
from elasticsearch import exceptions as es_exceptions

from karp.lex.domain.entities import Entry
from karp.search.domain.errors import UnsupportedField

logger = logging.getLogger("karp")

KARP_CONFIGINDEX = "karp_config"
KARP_CONFIGINDEX_TYPE = "configs"


@dataclass
class Field:
    """Information about a field in the index."""

    path: list[str]  # e.g. if the field name is "foo.bar" then this is ["foo", "bar"]
    type: str  # e.g. "text"

    extra: bool = False  # True for things like .raw fields

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
            return self.name + ".raw"


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

        self.fields: Dict[str, Dict[str, Field]] = {}
        self.sortable_fields: Dict[str, Dict[str, Field]] = {}

        aliases = self._get_all_aliases()
        self._update_field_mapping(aliases)

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

    def _update_field_mapping(
        self, aliases: List[Tuple[str, str]]
    ) -> Dict[str, Dict[str, Field]]:
        """
        Create a field mapping based on the mappings of elasticsearch.
        """

        mapping: Dict[str, Dict[str, Dict[str, Dict[str, Dict]]]] = self.es.indices.get_mapping()
        for alias, index in aliases:
            if (
                "mappings" in mapping[index]
                and "entry" in mapping[index]["mappings"]
                and "properties" in mapping[index]["mappings"]["entry"]
            ):
                self.fields[alias] = self._get_fields_from_mapping(
                    mapping[index]["mappings"]["entry"]["properties"]
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
        extra: bool = False,  # noqa: RUF013
    ) -> dict[str, Field]:
        if path is None:
            path = []
        fields = {}

        for prop_name, prop_value in properties.items():
            prop_path = path + [prop_name]  # noqa: RUF005
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
        self._update_field_mapping([(alias_name, index_name)])
