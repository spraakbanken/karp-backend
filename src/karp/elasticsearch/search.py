import elasticsearch_dsl as es_dsl

from karp import search


class EsSearch(search.SearchInterface):
    def __init__(self, es):
        self.es = es

    def get_query(self, query):
        # Only handle simplest case, for example: 'and|baseform.search|equals|userinput'
        [_, field, op, querystr] = query.split('|')

        # some TODO s
        # 1. Need to check config if the field search must be nested https://www.elastic.co/guide/en/elasticsearch/reference/current/nested.html
        # 2. Maybe need to map query input to another field in ES

        return es_dsl.Q("term", **{field: querystr})

    def search(self, resources, query=None):
        if query and query['split_results']:
            ms = es_dsl.MultiSearch(using=self.es)

            for resource in resources:
                s = es_dsl.Search(index=resource)
                s = s.query(query['query'])
                ms = ms.add(s)

            responses = ms.execute()
            result = {}
            for i, response in enumerate(responses):
                result[resources[i]] = [part_result.to_dict() for part_result in response]

            return result
        else:
            s = es_dsl.Search(using=self.es, index=','.join(resources))
            if query:
                s = s.query(query['query'])
            response = s.execute()
            return [{'id': result.meta.id, 'version': -1, 'entry': result.to_dict()} for result in response]
