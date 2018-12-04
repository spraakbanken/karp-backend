from elasticsearch_dsl import Q, Search, MultiSearch
from karp.search.search import SearchInterface


class EsSearch(SearchInterface):

    def __init__(self, es):
        self.es = es

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
