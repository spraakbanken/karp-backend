from datetime import datetime
import logging
import re
from typing import Dict, List, Optional, Any, Tuple, Union

import elasticsearch
import logging

from karp.foundation.events import EventBus

from karp.lex.domain.entities import Entry
from karp.search.application.repositories import (
    Index,
    IndexEntry,
    IndexUnitOfWork,
)


logger = logging.getLogger(__name__)

KARP_CONFIGINDEX = "karp_config"
KARP_CONFIGINDEX_TYPE = "configs"


class Es6Index(Index):
    def __init__(self, es: elasticsearch.Elasticsearch):
        self.es: elasticsearch.Elasticsearch = es
        if not self.es.indices.exists(index=KARP_CONFIGINDEX):
            self.es.indices.create(
                index=KARP_CONFIGINDEX,
                body={
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 1,
                        "refresh_interval": -1,
                    },
                    "mappings": {
                        KARP_CONFIGINDEX_TYPE: {
                            "dynamic": False,
                            "properties": {"index_name": {"type": "text"}},
                        }
                    },
                },
            )
        analyzed_fields, sortable_fields = self._init_field_mapping()
        self.analyzed_fields: Dict[str, List[str]] = analyzed_fields
        self.sortable_fields: Dict[str, Dict[str, List[str]]] = sortable_fields

    @property
    def seen(self):
        return []

    def create_index(self, resource_id, config):
        logger.info("creating es mapping")
        mapping = create_es6_mapping(config)

        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 1,
            "refresh_interval": -1,
        }
        if 'settings' in mapping:
            settings.update(mapping['settings'])
            del mapping['settings']
        properties = mapping["properties"]
        properties["freetext"] = {"type": "text"}
        disabled_property = {"enabled": False}
        properties["_entry_version"] = disabled_property
        properties["_last_modified"] = disabled_property
        properties["_last_modified_by"] = disabled_property

        body = {
            "settings": settings,
            "mappings": {"entry": mapping},
        }

        date = datetime.now().strftime("%Y-%m-%d-%H%M%S%f")
        index_name = resource_id + "_" + date
        logger.info('creating index', extra={
                    'index_name': index_name, 'body': body})
        result = self.es.indices.create(index=index_name, body=body)
        if "error" in result:
            logger.error('failed to create index',
                         extra={'index_name': index_name, 'body': body})
            raise RuntimeError("failed to create index")
        logger.info("index created")
        self._set_index_name_for_resource(resource_id, index_name)
        return index_name

    def _set_index_name_for_resource(self, resource_id: str, index_name: str) -> str:
        self.es.index(
            index=KARP_CONFIGINDEX,
            id=resource_id,
            doc_type=KARP_CONFIGINDEX_TYPE,
            body={"index_name": index_name},
        )
        return index_name

    def _get_index_name_for_resource(self, resource_id: str) -> str:
        try:
            res = self.es.get(
                index=KARP_CONFIGINDEX, id=resource_id, doc_type=KARP_CONFIGINDEX_TYPE
            )
        except es_exceptions.NotFoundError as err:
            logger.debug(
                "didn't find index_name for resource '%s' details: %s", resource_id, err)
            return self._set_index_name_for_resource(resource_id, resource_id)
        return res["_source"]["index_name"]

    def publish_index(self, resource_id: str):
        if self.es.indices.exists_alias(name=resource_id):
            self.es.indices.delete_alias(name=resource_id, index="*")

        index_name = self._get_index_name_for_resource(resource_id)
        self.on_publish_resource(resource_id, index_name)
        logger.info('publishing resource',
                    extra={'resource_id': resource_id, 'index_name': index_name})
        self.es.indices.put_alias(name=resource_id, index=index_name)

    def add_entries(self, resource_id: str, entries: List[IndexEntry]):
        index_name = self._get_index_name_for_resource(resource_id)
        index_to_es = []
        for entry in entries:
            assert isinstance(entry, IndexEntry)
            # entry.update(metadata.to_dict())
            index_to_es.append(
                {
                    "_index": index_name,
                    "_id": entry.id,
                    "_type": "entry",
                    "_source": entry.entry,
                }
            )

        elasticsearch.helpers.bulk(self.es, index_to_es, refresh=True)

    def delete_entry(
        self,
        resource_id: str,
        *,
        entry_id: Optional[str] = None,
        entry: Optional[Entry] = None,
    ):
        if not entry and not entry_id:
            raise ValueError("Must give either 'entry' or 'entry_id'.")
        if entry:
            entry_id = entry.entry_id
        logger.info('deleting entry', extra={'entry_id': entry_id,
                    'resource_id': resource_id})
        index_name = self._get_index_name_for_resource(resource_id)
        try:
            self.es.delete(
                index=index_name,
                doc_type="entry",
                id=entry_id,
                refresh=True,
            )
        except elasticsearch.exceptions.ElasticsearchException:
            logger.exception('Error deleting entry',
                             extra={'entry_id': entry_id, 'resource_id': resource_id, 'index_name': index_name, })

    @staticmethod
    def get_analyzed_fields_from_mapping(
        properties: Dict[str, Dict[str, Dict[str, Any]]]
    ) -> List[str]:
        analyzed_fields = []

        for prop_name, prop_values in properties.items():
            if "properties" in prop_values:
                res = Es6Index.get_analyzed_fields_from_mapping(
                    prop_values["properties"]
                )
                analyzed_fields.extend(
                    [prop_name + "." + prop for prop in res])
            else:
                if prop_values["type"] == "text":
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
                field_mapping[alias] = Es6Index.get_analyzed_fields_from_mapping(
                    mapping[index]["mappings"]["entry"]["properties"]
                )
                sortable_fields[alias] = Es6Index.create_sortable_map_from_mapping(
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
        print(f"{result}")
        index_names = []
        for index_name in result.split("\n")[:-1]:
            print(f"index_name = {index_name}")
            if index_name[0] != ".":
                match = re.search(r"([^ ]*) +(.*)", index_name)
                if match:
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
        translated_sort_fields: List[Union[str,
                                           Dict[str, Dict[str, str]]]] = []
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
        print(
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
            ] = Es6Index.get_analyzed_fields_from_mapping(
                mapping[index_name]["mappings"]["entry"]["properties"]
            )
            self.sortable_fields[
                alias_name
            ] = Es6Index.create_sortable_map_from_mapping(
                mapping[index_name]["mappings"]["entry"]["properties"]
            )

    @staticmethod
    def create_sortable_map_from_mapping(properties: Dict) -> Dict[str, List[str]]:
        sortable_map = {}

        def parse_prop_value(sort_map, base_name, prop_name, prop_value: Dict):
            if "properties" in prop_value:
                for ext_name, ext_value in prop_value["properties"].items():
                    ext_base_name = f"{base_name}.{ext_name}"
                    parse_prop_value(sort_map, ext_base_name,
                                     ext_base_name, ext_value)
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
                recursive_field(parent_schema, "v_" +
                                parent_field_name, res_object)
            if "result" in fun:
                res_object = fun["result"]
                recursive_field(parent_schema, "v_" +
                                parent_field_name, res_object)
            return
        if parent_field_def.get("ref"):
            if "field" in parent_field_def["ref"]:
                res_object = parent_field_def["ref"]["field"]
            else:
                res_object = {}
                res_object.update(parent_field_def)
                del res_object["ref"]
            recursive_field(parent_schema, "v_" +
                            parent_field_name, res_object)
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
            elif parent_field_def['type'] == 'long_string':
                mapped_type = 'text'
            else:
                mapped_type = "keyword"
            result = {"type": mapped_type}
            if parent_field_def['type'] == 'string':
                result["fields"] = {"raw": {"type": "keyword"}}
        else:
            result = {"properties": {}}

            for child_field_name, child_field_def in parent_field_def["fields"].items():
                recursive_field(result, child_field_name, child_field_def)

        parent_schema["properties"][parent_field_name] = result

    for field_name, field_def in fields.items():
        print(f"creating mapping for field '{field_name}'")
        recursive_field(es_mapping, field_name, field_def)

    return es_mapping


def create_es6_mapping(config: Dict) -> Dict:
    mapping = _create_es_mapping(config)
    mapping['settings'] = {
        'analysis': {
            'analyzer': {
                'default': {
                    'char_filter': [
                        'compound',
                        'swedish_aa',
                        'swedish_ae',
                        'swedish_oe'
                    ],
                    'filter': [
                        'swedish_folding',
                        'lowercase'
                    ],
                    'tokenizer': 'standard'
                }
            },
            'char_filter': {
                'compound': {
                    'pattern': '-',
                    'replacement': '',
                    'type': 'pattern_replace'
                },
                'swedish_aa': {
                    'pattern': '[Ǻǻ]',
                    'replacement': 'å',
                    'type': 'pattern_replace'
                },
                'swedish_ae': {
                    'pattern': '[æÆǞǟ]',
                    'replacement': 'ä',
                    'type': 'pattern_replace'
                },
                'swedish_oe': {
                    'pattern': '[ØøŒœØ̈ø̈ȪȫŐőÕõṌṍṎṏȬȭǾǿǬǭŌōṒṓṐṑ]',
                    'replacement': 'ö',
                    'type': 'pattern_replace'
                },
            },
            'filter': {
                'swedish_folding': {
                    'type': 'icu_folding',
                    'unicodeSetFilter': '[^åäöÅÄÖ]'
                },
                'swedish_sort': {
                    'language': 'sv',
                    'type': 'icu_collation'
                }
            }
        }
    }
    return mapping


class Es6IndexUnitOfWork(
    IndexUnitOfWork
):
    def __init__(
        self,
        es: elasticsearch.Elasticsearch,
        event_bus: EventBus,
    ) -> None:
        super().__init__(event_bus=event_bus)
        self._index = Es6Index(es=es)

    # @classmethod
    # def from_dict(cls, **kwargs):
    #     return cls()

    def _commit(self):
        logger.debug('Calling _commit in Es6IndexUnitOfWork')

    def rollback(self):
        return super().rollback()

    @property
    def repo(self) -> Es6Index:
        return self._index

    def _close(self):
        pass
