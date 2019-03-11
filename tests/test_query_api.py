import pytest  # pyre-ignore
import json
import time

ENTRIES = [{
    "code": 1,
    "name": "Grund test",
    "population": 3122,
    "area": 30000,
    "density": 5,
    "municipality": [1]
}, {
    "code": 2,
    "name": "Grunds",
    "population": 6312,
    "area": 20000,
    "density": 6,
    "municipality": [1]
}, {
    "code": 3,
    "name": "Botten test",
    "population": 4132,
    "area": 50000,
    "density": 7,
    "municipality": [2, 3]
},
{
    "code": 4,
    "name": "Hambo",
    "population": 4133,
    "area": 50000,
    "municipality": [2, 3]
},
{
    "code": 5,
    "name": "Rutvik",
    "area": 50000,
    "municipality": [2, 3]
},
]


def get_json(client, path):
    response = client.get(path)
    return json.loads(response.data.decode())


def init(client, es_status_code, entries):
    if es_status_code == 'skip':
        pytest.skip('elasticsearch disabled')
    client_with_data = client(use_elasticsearch=True)

    for entry in entries:
        client_with_data.post('places/add',
                              data=json.dumps({'entry': entry}),
                              content_type='application/json')
    return client_with_data


def test_query_no_q(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query')
    assert len(entries['hits']) == 5
    assert entries['hits'][0]['entry']['name'] == 'Grund test'
    assert entries['hits'][1]['entry']['name'] == 'Grunds'
    assert entries['hits'][2]['entry']['name'] == 'Botten test'
    assert entries['hits'][3]['entry']['name'] == 'Hambo'
    assert entries['hits'][4]['entry']['name'] == 'Rutvik'


def test_and_equals_equals(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    query = 'and||equals|population|4133||equals|area|50000'
    entries = get_json(client, 'places/query?q=' + query)

    assert len(entries['hits']) == 1
    assert entries['hits'][0]['entry']['name'] == 'Hambo'


def test_and_regexp_equals(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    query = 'and||regexp|name|.*bo.*||equals|area|50000'
    entries = get_json(client, 'places/query?q=' + query)

    assert len(entries['hits']) == 2
    assert entries['hits'][0]['entry']['name'] == 'Hambo'
    assert entries['hits'][1]['entry']['name'] == 'Botten test'


def test_contains_string_lowercase(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=contains|name|Grund')
    assert len(entries['hits']) == 2
    assert entries['hits'][0]['entry']['name'] == 'Grund test'
    assert entries['hits'][1]['entry']['name'] == 'Grunds'


def test_contains_string_correct_case(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=contains|name|Grund')
    assert len(entries['hits']) == 2
    assert entries['hits'][0]['entry']['name'] == 'Grund test'
    assert entries['hits'][1]['entry']['name'] == 'Grunds'


def test_contains_raw_field_string_correct_case(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=contains|name.raw|Grund')
    assert len(entries['hits']) == 2
    assert entries['hits'][0]['entry']['name'] == 'Grund test'
    assert entries['hits'][1]['entry']['name'] == 'Grunds'


@pytest.mark.skip(reason="regex can't handle integer")
def test_contains_integer(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=contains|population|3122')
    assert len(entries['hits']) == 1
    assert entries['hits'][0]['entry']['name'] == 'Grund test'


def test_endswith_string_lower_case(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=endswith|name|est')
    assert len(entries['hits']) == 2
    assert entries['hits'][0]['entry']['name'] == 'Grund test'
    assert entries['hits'][1]['entry']['name'] == 'Botten test'


def test_endswith_string_regex(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=endswith|name|unds')
    assert len(entries['hits']) == 1
    assert entries['hits'][0]['entry']['name'] == 'Grunds'


def test_endswith_string_lower_case_first_word(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=endswith|name|grund')
    assert len(entries['hits']) == 1
    assert entries['hits'][0]['entry']['name'] == 'Grund test'


def test_equals_string_lowercase(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=equals|name|Grunds')
    assert len(entries['hits']) == 1
    assert entries['hits'][0]['entry']['name'] == 'Grunds'


def test_equals_string_correct_case(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=equals|name|Grunds')
    assert len(entries['hits']) == 1
    assert entries['hits'][0]['entry']['name'] == 'Grunds'


@pytest.mark.skip(reason='es tokenizer splits on whitespace')
def test_equals_string_whole_name(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=equals|name|Grund test')
    assert len(entries['hits']) == 1
    assert entries['hits'][0]['entry']['name'] == 'Grunds'


def test_equals_integer(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=equals|density|7')
    assert len(entries['hits']) == 1
    assert entries['hits'][0]['entry']['name'] == 'Botten test'


def test_exists(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=exists|density')
    assert len(entries['hits']) == 3


def test_exists_and(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=exists||and|density|population')
    assert len(entries['hits']) == 3


def test_exists_or(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=exists||or|density|population')
    assert len(entries['hits']) == 4


def test_exists_not(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=exists||not|density')
    assert len(entries['hits']) == 2

    assert entries['hits'][0]['entry']['name'] == 'Hambo'
    assert entries['hits'][1]['entry']['name'] == 'Rutvik'


def test_freetext_string(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=freetext|grund')
    assert len(entries['hits']) == 2
    assert entries['hits'][1]['entry']['name'] == 'Grund test'
    assert entries['hits'][0]['entry']['name'] == 'Grunds'


def test_freetext_integer(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=freetext|3122')
    assert len(entries['hits']) == 1
    assert entries['hits'][0]['entry']['name'] == 'Grund test'


def test_freetext_and(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=freetext||and|botten|test')

    assert len(entries['hits']) == 1
    assert entries['hits'][0]['entry']['name'] == 'Botten test'


def test_freetext_not(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=freetext||not|botten')

    assert len(entries['hits']) == 4
    assert entries['hits'][0]['entry']['name'] == 'Grund test'
    assert entries['hits'][1]['entry']['name'] == 'Grunds'
    assert entries['hits'][2]['entry']['name'] == 'Hambo'
    assert entries['hits'][3]['entry']['name'] == 'Rutvik'


def test_freergxp_and(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=freergxp||and|.*test|Gr.*')

    assert len(entries['hits']) == 1
    assert entries['hits'][0]['entry']['name'] == 'Grund test'


@pytest.mark.skip(reason='Currently only allow top level NOT')
def test_freergxp_not(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=freergxp||not|Gr.*')

    assert len(entries['hits']) == 2
    assert entries['hits'][0]['entry']['name'] == 'Botten test'
    assert entries['hits'][1]['entry']['name'] == 'Hambo'


def test_freergxp_or(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=freergxp||or|.*test|Gr.*')

    assert len(entries['hits']) == 3
    assert entries['hits'][0]['entry']['name'] == 'Grund test'
    assert entries['hits'][1]['entry']['name'] == 'Grunds'
    assert entries['hits'][2]['entry']['name'] == 'Botten test'


def test_freergxp_string(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=freergxp|Grunds?')
    assert len(entries['hits']) == 2
    assert entries['hits'][0]['entry']['name'] == 'Grund test'
    assert entries['hits'][1]['entry']['name'] == 'Grunds'


def test_missing(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=missing|density')
    assert len(entries['hits']) == 2
    assert entries['hits'][0]['entry']['name'] == 'Hambo'
    assert entries['hits'][1]['entry']['name'] == 'Rutvik'


def test_missing_and(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=missing||and|density|population')
    assert len(entries['hits']) == 1
    assert entries['hits'][0]['entry']['name'] == 'Rutvik'


def test_missing_not(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=missing||not|density')
    assert len(entries['hits']) == 3
    assert entries['hits'][0]['entry']['name'] == 'Grund test'
    assert entries['hits'][1]['entry']['name'] == 'Grunds'
    assert entries['hits'][2]['entry']['name'] == 'Botten test'


def test_missing_or(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=missing||or|density|population')
    assert len(entries['hits']) == 2
    assert entries['hits'][0]['entry']['name'] == 'Rutvik'
    assert entries['hits'][1]['entry']['name'] == 'Hambo'


def test_not_freetext(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=not||freetext|botten')

    assert len(entries['hits']) == 4
    assert entries['hits'][0]['entry']['name'] == 'Grund test'
    assert entries['hits'][1]['entry']['name'] == 'Grunds'
    assert entries['hits'][2]['entry']['name'] == 'Hambo'
    assert entries['hits'][3]['entry']['name'] == 'Rutvik'


def test_not_freergxp(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=not||freergxp|.*test')

    assert len(entries['hits']) == 3
    assert entries['hits'][0]['entry']['name'] == 'Grunds'
    assert entries['hits'][1]['entry']['name'] == 'Hambo'
    assert entries['hits'][2]['entry']['name'] == 'Rutvik'


def test_or(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    query = 'or||equals|population|6312||equals|population|4132'
    entries = get_json(client, 'places/query?q=' + query)
    assert len(entries['hits']) == 2


def test_regex_string_lower_case(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=regexp|name|grun.*')
    assert len(entries['hits']) == 2
    assert entries['hits'][0]['entry']['name'] == 'Grund test'
    assert entries['hits'][1]['entry']['name'] == 'Grunds'


def test_regex_string_correct_case(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=regexp|name|Grun.*')
    assert len(entries['hits']) == 2
    assert entries['hits'][0]['entry']['name'] == 'Grund test'
    assert entries['hits'][1]['entry']['name'] == 'Grunds'


def test_regex_string_correct_case_question_mark(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=regexp|name|Grunds?')
    assert len(entries['hits']) == 1
    assert entries['hits'][0]['entry']['name'] == 'Grunds'


def test_regex_string_lower_case_question_mark(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=regexp|name|grunds?')
    assert len(entries['hits']) == 2
    assert entries['hits'][0]['entry']['name'] == 'Grund test'
    assert entries['hits'][1]['entry']['name'] == 'Grunds'


def test_regex_string_whole_name(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=regexp|name|Grun.*est')
    assert len(entries['hits']) == 1
    assert entries['hits'][0]['entry']['name'] == 'Grund test'


def test_startswith_string_lower_case(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=startswith|name|grun')
    assert len(entries['hits']) == 2
    assert entries['hits'][0]['entry']['name'] == 'Grund test'
    assert entries['hits'][1]['entry']['name'] == 'Grunds'


def test_startswith_string_correct_case(es, client_with_data_f):
    client = init(client_with_data_f, es, ENTRIES)

    entries = get_json(client, 'places/query?q=startswith|name|Grun')
    assert len(entries['hits']) == 2
    assert entries['hits'][0]['entry']['name'] == 'Grund test'
    assert entries['hits'][1]['entry']['name'] == 'Grunds'


@pytest.mark.skip(reason="places doesn't exist")
def test_no_q(client):
    response = client.get('/places/query')
    assert response.status == '200 OK'
    assert response.status_code == 200
    json_data = response.get_json()
    assert "query_params" in json_data


@pytest.mark.skip(reason='no protected stuff')
def test_protected(client_with_data_scope_module):
    response = client_with_data_scope_module.get('/municipalities/query')
    assert response.status == '403 FORBIDDEN'


# def test_pagination_explicit_0_25(es, client_with_data_f):
#     client = init_data(client_with_data_f, es, 30)
#     resource = 'places'
#     response = client.get('/{}/query?from=0&size=25'.format(resource))
#     assert response.status == '200 OK'
#     assert response.is_json
#     json_data = response.get_json()
#     assert json_data
#     assert 'hits' in json_data
#     assert len(json_data['hits']) == 25
#
#
# def test_pagination_explicit_13_45(es, client_with_data_f):
#     client = init_data(client_with_data_f, es, 60)
#     resource = 'places'
#     response = client.get('/{}/query?from=13&size=45'.format(resource))
#     assert response.status == '200 OK'
#     assert response.is_json
#     json_data = response.get_json()
#     assert json_data
#     assert 'hits' in json_data
#     assert len(json_data['hits']) == 45
#
#
# def test_pagination_default_size(es, client_with_data_f):
#     client = init_data(client_with_data_f, es, 30)
#     resource = 'places'
#     response = client.get('/{}/query?from=0'.format(resource))
#     assert response.status == '200 OK'
#     assert response.is_json
#     json_data = response.get_json()
#     assert len(json_data['hits']) == 25
#
#
# def test_pagination_default_from(es, client_with_data_f):
#     client = init_data(client_with_data_f, es, 50)
#     resource = 'places'
#     response = client.get('/{}/query?size=45'.format(resource))
#     assert response.status == '200 OK'
#     assert response.is_json
#     json_data = response.get_json()
#     assert len(json_data['hits']) == 45
#
#
# def test_pagination_fewer(es, client_with_data_f):
#     client = init_data(client_with_data_f, es, 5)
#     resource = 'places'
#     response = client.get('/{}/query?from=10'.format(resource))
#     assert response.status == '200 OK'
#     assert response.is_json
#     json_data = response.get_json()
#     assert len(json_data['hits']) == 0


def test_resource_not_existing(es, client_with_data_f):
    client = init_data(client_with_data_f, es, 0)
    response = client.get('/asdf/query')
    assert response.status_code == 400
    assert 'Resource is not searchable: "asdf"' == json.loads(response.data.decode())['error']


def init_data(client, es_status_code, no_entries):
    if es_status_code == 'skip':
        pytest.skip('elasticsearch disabled')
    client_with_data = client(use_elasticsearch=True)

    for i in range(0, no_entries):
        entry = {
            'code': i,
            'name': 'name',
            'municipality': [1]
        }
        client_with_data.post('places/add',
                              data=json.dumps({'entry': entry}),
                              content_type='application/json')
    return client_with_data
