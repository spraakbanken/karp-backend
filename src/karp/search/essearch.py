from elasticsearch import Elasticsearch
import elasticsearch.helpers
from elasticsearch_dsl import Q, Search
from karp.search.search import SearchInterface


class EsSearch(SearchInterface):

    def __init__(self, host):
        self.es = Elasticsearch(hosts=host)

    def search(self, resource_id, version, simple_query=None, extended_query=None):
        s = Search(using=self.es)

        if simple_query:
            s = s.query("match", _all=simple_query)

        if extended_query:
            s = s.query(self._map_extended_to_query(resource_id, version, extended_query))

        s = s.index(resource_id + '_' + str(version))
        response = s.execute()
        return [result.to_dict() for result in response]

    def _map_extended_to_query(self, resource_id, version, extended_query):
        # Only handle simplest case, for example: 'and|baseform.search|equals|userinput'
        [_, field, op, querystr] = extended_query.split('|')

        # some TODO s
        # 1. Need to check config if the field search must be nested https://www.elastic.co/guide/en/elasticsearch/reference/current/nested.html
        # 2. Maybe need to map query input to another field in ES

        return Q("term", **{field: querystr})

    def create_index(self, resource_id, version, config):
        mapping = self._create_es_mapping(config)

        body = {
            'settings': {
                'number_of_shards': 1,
                'number_of_replicas': 1
            },
            'mappings': {
                'entry': mapping
            }
        }

        self.es.indices.create(index=resource_id + '_' + str(version), body=body)

    def _create_es_mapping(self, config):
        es_mapping = {
            'dynamic': False,
            'properties': {}
        }

        fields = config['fields']

        def recursive_field(parent_schema, parent_field_name, parent_field_def):
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

    def add_entries(self, resource_id, version, created_db_entries):
        index_to_es = []
        for (db_entry, src_entry) in created_db_entries:
            index_to_es.append({
                '_index': resource_id + '_' + str(version),
                '_id': db_entry.id,
                '_type': 'entry',
                '_source': src_entry
            })

        elasticsearch.helpers.bulk(self.es, index_to_es)