import logging
import re
import json
import elasticsearch_dsl as es_dsl  # pyre-ignore

from typing import Dict

from karp.query_dsl import basic_ast as ast, op, is_a
# from karp import query_dsl
from karp import search


logger = logging.getLogger('karp')


class EsQuery(search.Query):
    def __init__(self):
        super().__init__()
        self.query = None
        self.resource_str = None

    def parse_arguments(self, args, resource_str):
        super().parse_arguments(args, resource_str)
        self.resource_str = resource_str
        if not self.ast.is_empty():
            self.query = create_es_query(self.ast.root)

    def _self_name(self) -> str:
        return 'EsQuery query={} resource_str={}'.format(self.query,
                                                         self.resource_str)


def get_value(value_node):
    if is_a(value_node, op.STRING):
        return value_node.value
    elif is_a(value_node, op.INT):
        return value_node.value
    elif is_a(value_node, op.FLOAT):
        return value_node.value
    else:
        raise NotImplementedError()


def create_es_query(node: ast.Node):
    node.pprint(0)
    if node is None:
        raise TypeError()

    q = None
    if is_a(node, op.LOGICAL):
        # TODO check minimum should match rules in different contexts
        queries = [create_es_query(n) for n in node.children]
        q1 = queries[0]
        q2 = queries[1]
        print('q1 = {}'.format(q1.to_dict()))
        print('q2 = {}'.format(repr(q2)))
        q1_dict = q1.to_dict()
        q2_dict = q2.to_dict()
        if 'range' in q1_dict and 'range' in q2_dict:
            for q1_field, q1_value in q1_dict['range'].items():
                for q2_field, q2_value in q2_dict['range'].items():
                    if q1_field == q2_field:
                        print('q1_field == q2_field')
                        range_args = q1_value
                        range_args.update(q2_value)
                        print('field = {}'.format(q1_field))
                        print('range_args = {}'.format(range_args))
                        q = es_dsl.Q('range', **{q1_field: range_args})
                        return q
        if is_a(node, op.AND):
            q = es_dsl.Q('bool', must=queries)
        elif is_a(node, op.OR):
            q = es_dsl.Q('bool', should=queries)
        else:
            q = es_dsl.Q('bool', must_not=queries)
    elif is_a(node, op.UNARY_OPS):
        arg = node.children[0]
        values = []
        if is_a(arg, op.ARG_LOGICAL):
            for child in arg.children:
                values.append(child.value)
            print('values = {}'.format(values))
        if is_a(node, op.FREETEXT):
            def construct_freetext_query(node):
                if is_a(node, op.STRING):
                    return es_dsl.Q('multi_match', query=node.value, fuzziness=1)
                else:
                    return es_dsl.Q('multi_match', query=node.value)
            if not values:
                q = construct_freetext_query(arg)
            else:
                queries = [construct_freetext_query(n) for n in arg.children]
                if is_a(arg, op.ARG_OR):
                    q = es_dsl.Q('bool', should=queries)
                elif is_a(arg, op.ARG_AND):
                    q = es_dsl.Q('bool', must=queries)
                else:
                    q = es_dsl.Q('bool', must_not=queries)
        elif is_a(node, op.FREERGXP):
            kwargs = {
                'default_field': '*'
            }
            if not values:
                kwargs['query'] = '/{}/'.format(arg.value)
            else:
                if is_a(arg, op.ARG_OR):
                    operator = ' OR '
                else:  # if is_a(arg, op.ARG_AND):
                    operator = ' AND '
                kwargs['query'] = operator.join('(/{}/)'.format(v) for v in values)
            print('kwargs = {}'.format(kwargs))
            q = es_dsl.Q('query_string', **kwargs)
            if is_a(arg, op.ARG_NOT):
                q = es_dsl.Q('bool', must_not=q)
        elif is_a(node, op.EXISTS):
            if not values:
                q = es_dsl.Q('exists', field=arg.value)
            else:
                queries = [es_dsl.Q('exists', field=value) for value in values]
                if is_a(arg, op.ARG_OR):
                    q = es_dsl.Q('bool', should=queries)
                elif is_a(arg, op.ARG_AND):
                    q = es_dsl.Q('bool', must=queries)
                else:  # if is_a(arg, op.ARG_NOT):
                    q = es_dsl.Q('bool', must_not=queries)
        elif is_a(node, op.MISSING):
            if not values:
                q = es_dsl.Q('bool', must_not=es_dsl.Q('exists', field=arg.value))
            else:
                queries = [es_dsl.Q('exists', field=value) for value in values]

                if is_a(arg, op.ARG_AND):
                    q = es_dsl.Q('bool', must_not=queries)
                elif is_a(arg, op.ARG_OR):
                    q = None
                    for query in queries:
                        q_tmp = es_dsl.Q('bool', must_not=query)
                        if not q:
                            q = q_tmp
                        else:
                            q = q | q_tmp
                else:  # is_a(arg, op.ARG_NOT):
                    q = es_dsl.Q('bool', must=queries)
        else:
            raise RuntimeError('not implemented')
    elif is_a(node, op.BINARY_OPS):
        arg1 = node.children[0]
        arg2 = node.children[1]
        arg1_values = []
        arg2_values = []

        if is_a(arg1, op.ARG_LOGICAL):
            for child in arg1.children:
                arg1_values.append(child.value)
            print('arg1_values = {}'.format(arg1_values))

        if is_a(arg2, op.ARG_LOGICAL):
            for child in arg2.children:
                arg2_values.append(child.value)
            print('arg2_values = {}'.format(arg2_values))
        # TODO this check breaks and and or since they always (?) have ast.ArgNode as parameters
        # if not isinstance(arg1, ast.ArgNode) or not isinstance(arg2, ast.ArgNode):
            # TODO these need to be moved outside of current query, for example:
            # "equals|name||or|Partille|Kumla" could be expressed in two ways
            # es_dsl.Q('terms', name=['Partille', 'Kumla'])
            # or
            # es_dsl.Q('bool', should=[es_dsl.Q('term', name='Partille'), es_dsl.Q('term', name='Kumla')])
            # but "regexp|name||or|Part*|Kum*"
            # can only be expressed as in the longer form above
            # raise RuntimeError()

        if is_a(node, op.EQUALS):
            def construct_equals_query(field: str, query):
                kwargs = {
                    field: {
                        'query': query,
                        'operator': 'and'
                    }
                }
                return es_dsl.Q('match', **kwargs)

            # if not arg1_values:
            #     arg1_values.append(get_value(arg1))
            # # arg11 = get_value(arg1)
            # if not arg2_values:
            #     arg2_values.append(get_value(arg2))
            # arg22 = get_value(arg2)

            q = None
            # if len(arg1_values) == 1:
            if not arg1_values:
                if not arg2_values:
                    q = construct_equals_query(get_value(arg1), get_value(arg2))
                else:
                    queries = [construct_equals_query(get_value(arg1), query) for query in arg2_values]
                    if is_a(arg2, op.ARG_AND):
                        q = es_dsl.Q('bool', must=queries)
                    elif is_a(arg2, op.ARG_OR):
                        q = es_dsl.Q('bool', should=queries)
                    else:
                        q = es_dsl.Q('bool', must_not=queries)  # , must=es_dsl.Q('multi_match', query=get_value(arg1)))
                    # for query in arg2_values:
                    #     q_tmp = construct_equals_query(get_value(arg1), query)
                    #     if is_a(arg2, op.ARG_NOT):
                    #         q_tmp = ~q_tmp
                    #     if not q:
                    #         q = q_tmp
                    #     else:
                    #         if is_a(arg2, op.ARG_OR):
                    #             q = q | q_tmp
                    #         else:
                    #             q = q & q_tmp
            else:  # if arg1_values:
                # if len(arg2_values) == 1:
                if not arg2_values:
                    queries = [construct_equals_query(field, get_value(arg2)) for field in arg1_values]
                    if is_a(arg1, op.ARG_AND):
                        q = es_dsl.Q('bool', must=queries)
                    elif is_a(arg1, op.ARG_OR):
                        q = es_dsl.Q('bool', should=queries)
                    else:
                        q = es_dsl.Q('bool', must_not=queries, must=es_dsl.Q('multi_match', query=get_value(arg2)))
                    # if is_a(arg1, op.ARG_AND):
                    #     # q = es_dsl.Q('multi_match',
                    #     #               query=arg2_values[0],
                    #     #               fields=arg1_values,
                    #     #               operator='and',
                    #     #               type='cross_fields')
                    #     for field in arg1_values:
                    #         q_tmp = construct_equals_query(field, get_value(arg2))
                    #         if not q:
                    #             q = q_tmp
                    #         else:
                    #             if is_a(arg2, op.ARG_OR):
                    #                 q = q | q_tmp
                    #             else:
                    #                 q = q & q_tmp

                    # else:
                    #     q = es_dsl.Q('multi_match', query=get_value(arg2), fields=arg1_values)
                else:  # if arg2_values:
                    raise RuntimeError("Don't know how to handle ")

            # kwargs = {
            #     arg11: {
            #         'query': arg22,
            #         'operator': 'and'
            #     }
            # }
            # q = es_dsl.Q('match', **kwargs)
        elif is_a(node, op.REGEX_OPS):
            def extract_field_plus_rawfield(field: str):
                if field.endswith('.raw'):
                    yield field
                else:
                    yield field
                    yield field + '.raw'

            # fields = set()
            # if not arg1_values:
            #
            # else:
            #     for v in arg1_values:
            #         fields = extract_field_plus_rawfield(v, fields)
            # arg11 = extract_field_plus_rawfield(get_value(arg1))

            # arg22 = get_value(arg2)
            def prepare_regex(node, s: str):
                if is_a(node, op.CONTAINS):
                    return '.*' + re.escape(s) + '.*'
                elif is_a(node, op.STARTSWITH):
                    return re.escape(s) + '.*'
                elif is_a(node, op.ENDSWITH):
                    return '.*' + re.escape(s)
                else:
                    return s

            # if is_a(node, op.CONTAINS):
            #     arg22 = '.*' + re.escape(arg22) + '.*'
            # elif is_a(node, op.STARTSWITH):
            #     arg22 = re.escape(arg22) + '.*'
            # elif is_a(node, op.ENDSWITH):
            #     arg22 = '.*' + re.escape(arg22)
            # arg22 = prepare_regex(op, arg22)
            # print('arg22 = {}'.format(arg22))
            # Construct query
            def construct_regexp_query(field_in: str, regex: str):
                q = None
                for field in extract_field_plus_rawfield(field_in):
                    q_tmp = es_dsl.Q('regexp', **{field: regex})
                    if not q:
                        q = q_tmp
                    else:
                        q = q | q_tmp
                return q

            q = None
            if not arg1_values:
                if not arg2_values:
                    q = construct_regexp_query(
                            get_value(arg1),
                            prepare_regex(node, get_value(arg2))
                        )
                else:
                    queries = []
                    for regex in arg2_values:
                        q_tmp = construct_regexp_query(
                                    get_value(arg1),
                                    prepare_regex(node, regex)
                                )
                        print('q_tmp = {q_tmp}'.format(q_tmp=q_tmp))
                        # if is_a(arg2, op.ARG_NOT):
                        #     queries.append(~q_tmp)
                        # else:
                        queries.append(q_tmp)
                    # if len(queries) == 1:
                    #     q = queries[0]
                    if is_a(arg2, op.ARG_OR):
                        q = es_dsl.Q('bool', should=queries)
                    elif is_a(arg2, op.ARG_AND):
                        q = es_dsl.Q('bool', must=queries)
                    else:
                        # kwargs = {
                        #     'default_field': '*'
                        # }
                        # # if not arg2_values:
                        # #     kwargs['query'] = '/{}/'.format(arg2.value)
                        # # else:
                        # if is_a(arg2, op.ARG_OR):
                        #     operator = ' OR '
                        # else:  # if is_a(arg, op.ARG_AND):
                        #     operator = ' AND '
                        # kwargs['query'] = operator.join('(/{}/)'.format(v) for v in arg2_values)
                        # print('regex NOT kwargs = {}'.format(kwargs))

                        q = es_dsl.Q('bool', must_not=queries)  # , must=es_dsl.Q('query_string', **kwargs))
            else:  # if arg1_values:
                if not arg2_values:
                    regex = prepare_regex(node, get_value(arg2))
                    queries = []
                    for field in arg1_values:
                        q_tmp = construct_regexp_query(field, regex)
                        print('q_tmp = {q_tmp}'.format(q_tmp=q_tmp))
                        # if is_a(arg1, op.ARG_NOT):
                        #     queries.append(~q_tmp)
                        # else:
                        queries.append(q_tmp)
                    # if len(queries) == 1:
                    #     q = queries[0]
                    if is_a(arg1, op.ARG_OR):
                        q = es_dsl.Q('bool', should=queries)
                    elif is_a(arg1, op.ARG_AND):
                        q = es_dsl.Q('bool', must=queries)
                    else:
                        kwargs = {
                            'default_field': '*'
                        }
                        # if not values:
                        kwargs['query'] = '/{}/'.format(regex)
                        # else:
                        #     if is_a(arg2, op.ARG_OR):
                        #         operator = ' OR '
                        #     else:  # if is_a(arg2, op.ARG_AND):
                        #         operator = ' AND '
                        #     kwargs['query'] = operator.join('(/{}/)'.format(v) for v in arg2_values)
                        print('regex NOT kwargs = {}'.format(kwargs))

                        q = es_dsl.Q('bool', must_not=queries, must=es_dsl.Q('query_string', **kwargs))
                else:
                    raise RuntimeError('Complex regex not implemented')

            # q = construct_regexp_query(get_value(arg1), arg22)
            # if len(fields) == 1:
            #     q = es_dsl.Q('regexp', **{arg11[0]: arg22})
            # else:
            #     q = es_dsl.Q('bool', should=[es_dsl.Q('regexp', **{field: arg22}) for field in fields])
        elif is_a(node, op.RANGE_OPS):
            if arg2_values:
                raise RuntimeError('Unsupported usage')
            arg22 = get_value(arg2)
            range_args = {}
            if is_a(node, op.LT):
                range_args['lt'] = arg22
            elif is_a(node, op.LTE):
                range_args['lte'] = arg22
            elif is_a(node, op.GT):
                range_args['gt'] = arg22
            elif is_a(node, op.GTE):
                range_args['gte'] = arg22

            def construct_range_query(field: str, range_args: Dict):
                return es_dsl.Q('range', **{field: range_args})

            q = None
            if not arg1_values:
                q = construct_range_query(get_value(arg1), range_args)
            else:
                for field in arg1_values:
                    q_tmp = construct_range_query(field, range_args)
                    if not q:
                        q = q_tmp
                    elif is_a(arg1, op.ARG_AND):
                        q = q & q_tmp
                    else:  # if is_a(arg1, op.ARG_OR):
                        q = q | q_tmp
            # arg11 = get_value(arg1)
            # if is_a(node, op.LT):
            #     range_args['lt'] = arg22
            # elif is_a(node, op.LTE):
            #     range_args['lte'] = arg22
            # elif is_a(node, op.GT):
            #     range_args['gt'] = arg22
            # elif is_a(node, op.GTE):
            #     range_args['gte'] = arg22
            # q = es_dsl.Q('range', **{arg11: range_args})
    # elif isinstance(node, ast.TernaryOp):
    #     op = node.value
    #     arg1 = node.children[0]
    #     arg2 = node.children[1]
    #     arg3 = node.children[2]
    #     if op == query_dsl.Operators.RANGE:
    #         raise RuntimeError('don\'t now what to do yet')
    #     else:
    #         raise RuntimeError('what operators?')
    else:
        raise ValueError('Unknown query op %s' % node)

    return q


class EsSearch(search.SearchInterface):

    def __init__(self, es):
        self.es = es
        self.analyzed_fields = self._init_field_mapping()

    def _init_field_mapping(self):
        """
        Create a field mapping based on the mappings of elasticsearch
        currently the only information we need is if a field is analyzed (i.e. text)
        or not.
        """
        def parse_mapping(properties):
            analyzed_fields = []
            for prop_name, prop_values in properties.items():
                if 'properties' in prop_values:
                    res = parse_mapping(prop_values['properties'])
                    analyzed_fields.extend([prop_name + '.' + prop for prop in res])
                else:
                    if prop_values['type'] == 'text':
                        analyzed_fields.append(prop_name)
            return analyzed_fields

        field_mapping = {}

        # Doesn't work for tests, can't find resource_definition
        # for resource in resourcemgr.get_available_resources():
        #     mapping = self.es.indices.get_mapping(index=resource.resource_id)
        #     field_mapping[resource.resource_id] = parse_mapping(
        #         next(iter(mapping.values()))['mappings']['entry']['properties']
        #     )
        aliases = self._get_all_aliases()
        mapping = self.es.indices.get_mapping()
        for (alias, index) in aliases:
            if (
                    'mappings' in mapping[index]
                    and 'entry' in mapping[index]['mappings']
                    and 'properties' in mapping[index]['mappings']['entry']
                    ):
                field_mapping[alias] = parse_mapping(
                    mapping[index]['mappings']['entry']['properties']
                )
        return field_mapping

    def _get_all_aliases(self):
        """
        :return: a list of tuples (alias_name, index_name)
        """
        result = self.es.cat.aliases(h='alias,index')
        index_names = []
        for index_name in result.split('\n')[:-1]:
            if index_name[0] != '.':
                groups = re.search(r'([^ ]*) +(.*)', index_name).groups()
                alias = groups[0]
                index = groups[1]
                index_names.append((alias, index))
        return index_names

    def build_query(self, args, resource_str: str) -> EsQuery:
        query = EsQuery()
        query.parse_arguments(args, resource_str)
        return query

    def _format_result(self, resource_ids, response):

        def format_entry(entry):
            dict_entry = entry.to_dict()
            version = dict_entry.pop('_entry_version', None)
            last_modified_by = dict_entry.pop('_last_modified_by', None)
            last_modified = dict_entry.pop('_last_modified', None)
            return {
                'id': entry.meta.id,
                'version': version,
                'last_modified': last_modified,
                'last_modified_by': last_modified_by,
                'resource': next(resource for resource in resource_ids if entry.meta.index.startswith(resource)),
                'entry': dict_entry
            }

        result = {
            'total': response.hits.total,
            'hits': [format_entry(entry) for entry in response]
        }
        return result

    def search_with_query(self, query: EsQuery):
        logger.info('search_with_query called with query={}'.format(query))
        if query.split_results:
            ms = es_dsl.MultiSearch(using=self.es)

            for resource in query.resources:
                s = es_dsl.Search(index=resource)

                if query.query is not None:
                    s = s.query(query.query)
                s = s[query.from_:query.from_ + query.size]
                ms = ms.add(s)

            responses = ms.execute()
            result = {
                'total': 0,
                'hits': {}
            }
            for i, response in enumerate(responses):
                result['hits'][query.resources[i]] = self._format_result(query.resources, response).get('hits', [])
                result['total'] += response.hits.total
                if query.lexicon_stats:
                    if 'distribution' not in result:
                        result['distribution'] = {}
                    result['distribution'][query.resources[i]] = response.hits.total
            return result
        else:
            s = es_dsl.Search(using=self.es, index=query.resource_str)
            logger.debug('s = {}'.format(s))
            if query.query is not None:
                s = s.query(query.query)

            s = s[query.from_:query.from_ + query.size]

            if query.lexicon_stats:
                s.aggs.bucket('distribution', 'terms', field='_index', size=len(query.resources))

            response = s.execute()

            logger.debug('response = {}'.format(response.to_dict()))

            result = self._format_result(query.resources, response)
            if query.lexicon_stats:
                result['distribution'] = {}
                for bucket in response.aggregations.distribution.buckets:
                    key = bucket['key']
                    value = bucket['doc_count']
                    result['distribution'][key.rsplit('_', 1)[0]] = value

            return result

    def search_ids(self, args, resource_id: str, entry_ids: str):
        logger.info('Called EsSearch.search_ids(self, args, resource_id, entry_ids) with:')
        logger.info('  resource_id = {}'.format(resource_id))
        logger.info('  entry_ids = {}'.format(entry_ids))
        entries = entry_ids.split(',')
        query = es_dsl.Q('terms', _id=entries)
        logger.debug('query = {}'.format(query))
        s = es_dsl.Search(using=self.es, index=resource_id).query(query)
        logger.debug('s = {}'.format(s.to_dict()))
        response = s.execute()

        return self._format_result([resource_id], response)

    def statistics(self, resource_id: str, field: str):
        s = es_dsl.Search(using=self.es, index=resource_id)
        s = s[0:0]

        if field in self.analyzed_fields[resource_id]:
            field = field + '.raw'

        logger.debug('Statistics: analyzed fields are:')
        logger.debug(json.dumps(self.analyzed_fields, indent=4))
        logger.debug('Doing aggregations on resource_id: {resource_id}, on field {field}'.format(
            resource_id=resource_id,
            field=field
        ))
        s.aggs.bucket('field_values', 'terms', field=field, size=2147483647)
        response = s.execute()
        result = []
        for bucket in response.aggregations.field_values.buckets:
            result.append({'value': bucket['key'], 'count': bucket['doc_count']})
        return result
