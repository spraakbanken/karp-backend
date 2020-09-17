from datetime import datetime

import elasticsearch.helpers  # pyre-ignore

from karp.indexmgr.index import IndexInterface
from karp.util.notifier import Notifier
from .es_observer import OnPublish


def _create_es_mapping(config):
    es_mapping = {"dynamic": False, "properties": {}}

    fields = config["fields"]

    def recursive_field(parent_schema, parent_field_name, parent_field_def):
        if parent_field_def.get("virtual", False):
            fun = parent_field_def["function"]
            if list(fun.keys())[0] == "multi_ref":
                res_object = fun["multi_ref"]["result"]
                recursive_field(parent_schema, "v_" + parent_field_name, res_object)
            if "result" in fun:
                res_object = fun["result"]
                recursive_field(parent_schema, "v_" + parent_field_name, res_object)
            return
        if parent_field_def.get("ref"):
            if "field" in parent_field_def["ref"]:
                res_object = parent_field_def["ref"]["field"]
            else:
                res_object = {}
                res_object.update(parent_field_def)
                del res_object["ref"]
            recursive_field(parent_schema, "v_" + parent_field_name, res_object)
        if parent_field_def["type"] != "object":
            # TODO this will not work when we have user defined types, s.a. saldoid
            # TODO number can be float/non-float, strings can be keyword or text in need of analyzing etc.
            if parent_field_def["type"] == "integer":
                mapped_type = "long"
            elif parent_field_def["type"] == "number":
                mapped_type = "double"
            elif parent_field_def["type"] == "string":
                mapped_type = "text"
            else:
                mapped_type = "keyword"
            result = {"type": mapped_type}
            if mapped_type == "text" and not parent_field_def.get("skip_raw", False):
                result["fields"] = {"raw": {"type": "keyword"}}
        else:
            result = {"properties": {}}

            for child_field_name, child_field_def in parent_field_def["fields"].items():
                recursive_field(result, child_field_name, child_field_def)

        parent_schema["properties"][parent_field_name] = result

    for field_name, field_def in fields.items():
        recursive_field(es_mapping, field_name, field_def)

    return es_mapping


class EsIndex(IndexInterface):
    def __init__(self, es):
        self.es = es
        self.publish_notifier = Notifier()

    def register_publish_observer(self, on_publish: OnPublish):
        self.publish_notifier.register(on_publish)

    def unregister_publish_observer(self, on_publish: OnPublish):
        self.publish_notifier.unregister(on_publish)

    def create_index(self, resource_id, config):
        mapping = _create_es_mapping(config)

        properties = mapping["properties"]
        properties["freetext"] = {"type": "text"}
        disabled_property = {"enabled": False}
        properties["_entry_version"] = disabled_property
        properties["_last_modified"] = disabled_property
        properties["_last_modified_by"] = disabled_property

        body = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1,
                "refresh_interval": -1,
            },
            "mappings": {"entry": mapping},
        }

        date = datetime.now().strftime("%Y-%m-%d-%H%M%S%f")
        index_name = resource_id + "_" + date
        result = self.es.indices.create(index=index_name, body=body)
        if "error" in result:
            raise RuntimeError("failed to create index")
        return index_name

    def publish_index(self, alias_name, index_name):
        if self.es.indices.exists_alias(name=alias_name):
            self.es.indices.delete_alias(name=alias_name, index="*")

        self.es.indices.put_alias(name=alias_name, index=index_name)
        self.publish_notifier.notify(alias_name=alias_name, index_name=index_name)

    def add_entries(self, resource_id, entries):
        index_to_es = []
        for (entry_id, metadata, entry) in entries:
            entry.update(metadata.to_dict())
            index_to_es.append(
                {
                    "_index": resource_id,
                    "_id": entry_id,
                    "_type": "entry",
                    "_source": entry,
                }
            )

        elasticsearch.helpers.bulk(self.es, index_to_es, refresh=True)

    def delete_entry(self, resource_id, entry_id):
        self.es.delete(index=resource_id, doc_type="entry", id=entry_id, refresh=True)

    def create_empty_object(self):
        return {}

    def assign_field(self, _index_entry, field_name, part):
        _index_entry[field_name] = part

    def create_empty_list(self):
        return []

    def add_to_list_field(self, elems, elem):
        elems.append(elem)
