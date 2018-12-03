from elasticsearch import Elasticsearch
import elasticsearch.helpers
from elasticsearch_dsl import Q, Search, MultiSearch
from karp.search.search import SearchInterface
from datetime import datetime


class EsSearch(SearchInterface):

    def __init__(self, host):
        self.es = Elasticsearch(hosts=host)

    def get_query(self, query):
        # Only handle simplest case, for example: 'and|baseform.search|equals|userinput'
        [_, field, op, querystr] = query.split('|')

        # some TODO s
        # 1. Need to check config if the field search must be nested https://www.elastic.co/guide/en/elasticsearch/reference/current/nested.html
        # 2. Maybe need to map query input to another field in ES

        return Q("term", **{field: querystr})

    def search(self, resources, query=None):
        if query['split_results']:
            ms = MultiSearch(using=self.es)

            for resource in resources:
                s = Search(index=resource)
                s = s.query(query['query'])
                ms = ms.add(s)

            responses = ms.execute()
            result = {}
            for i, response in enumerate(responses):
                result[resources[i]] = [part_result.to_dict() for part_result in response]

            return result
        else:
            s = Search(using=self.es, index=','.join(resources))
            s = s.query(query['query'])
            response = s.execute()
            return [result.to_dict() for result in response]

    def create_index(self, resource_id, config):
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

        date = datetime.now().strftime('%Y-%m-%d-%H%M%S')
        index_name = resource_id + '_' + date
        result = self.es.indices.create(index=index_name, body=body)
        if 'error' in result:
            raise RuntimeError('failed to create index')
        return index_name

    def publish_index(self, alias_name, index_name):
        if self.es.indices.exists_alias(name=alias_name):
            self.es.indices.delete_alias(name=alias_name, index='*')

        self.es.indices.put_alias(name=alias_name, index=index_name)

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

    def add_entries(self, resource_id, created_db_entries):
        index_to_es = []
        for (db_entry, src_entry) in created_db_entries:
            index_to_es.append({
                '_index': resource_id,
                '_id': db_entry.id,
                '_type': 'entry',
                '_source': src_entry
            })

        elasticsearch.helpers.bulk(self.es, index_to_es)
