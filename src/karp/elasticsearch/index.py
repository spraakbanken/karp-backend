import elasticsearch.helpers
from datetime import datetime
from karp.resourcemgr.index import IndexInterface


def _create_es_mapping(config):
    es_mapping = {
        'dynamic': False,
        'properties': {}
    }

    fields = config['fields']

    def recursive_field(parent_schema, parent_field_name, parent_field_def):
        if parent_field_def.get('virtual', False):
            # TODO fix mapping for virtual, fields, get result object
            return
        if parent_field_def['type'] != 'object':
            # TODO this will not work when we have user defined types, s.a. saldoid
            # TODO number can be float/non-float, strings can be keyword or text in need of analyzing etc.
            if parent_field_def['type'] == 'number':
                mapped_type = 'long'
            elif parent_field_def['type'] == 'string':
                mapped_type = 'keyword'
            else:
                mapped_type = 'keyword'
            result = {
                'type': mapped_type
            }
        else:
            result = {
                'properties': {}
            }

            for child_field_name, child_field_def in parent_field_def['fields'].items():
                recursive_field(result, child_field_name, child_field_def)

        parent_schema['properties'][parent_field_name] = result

    for field_name, field_def in fields.items():
        recursive_field(es_mapping, field_name, field_def)

    return es_mapping


class EsIndex(IndexInterface):

    def __init__(self, es):
        self.es = es

    def create_index(self, resource_id, config):
        mapping = _create_es_mapping(config)

        body = {
            'settings': {
                'number_of_shards': 1,
                'number_of_replicas': 1
            },
            'mappings': {
                'entry': mapping
            }
        }

        date = datetime.now().strftime('%Y-%m-%d-%H%M%S%f')
        index_name = resource_id + '_' + date
        result = self.es.indices.create(index=index_name, body=body)
        if 'error' in result:
            raise RuntimeError('failed to create index')
        return index_name

    def publish_index(self, alias_name, index_name):
        if self.es.indices.exists_alias(name=alias_name):
            self.es.indices.delete_alias(name=alias_name, index='*')

        self.es.indices.put_alias(name=alias_name, index=index_name)

    def add_entries(self, resource_id, entries):
        index_to_es = []
        for (db_id, entry) in entries:
            index_to_es.append({
                '_index': resource_id,
                '_id': db_id,
                '_type': 'entry',
                '_source': entry
            })

        elasticsearch.helpers.bulk(self.es, index_to_es)

    def delete_entry(self, resource_id, entry_id):
        self.es.delete(index=resource_id, doc_type='entry', id=entry_id)
