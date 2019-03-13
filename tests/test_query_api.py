import pytest  # pyre-ignore
import json
import time

from typing import List


ENTRIES = [{
    "code": 1,
    "name": "Grund test",
    "population": 3122,
    "area": 6312,
    "density": 5,
    "municipality": [1],
    "larger_place": 7 # Alhamn
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
    "population": 4133,
    "area": 50000,
    "density": 7,
    "municipality": [2, 3]
    # "smaller_places": 4 "Hambo"
},
{
    "code": 4,
    "name": "Hambo",
    "population": 4132,
    "area": 50000,
    "municipality": [2, 3],
    "larger_place": 3 # Botten test
},
{
    "code": 5,
    "name": "Rutvik",
    "area": 50000,
    "municipality": [2, 3]
},
{
    "code": 6,
    "name": "Alvik",
    "area": 6312,
    "population": 6312,
    "density": 12,
    "municipality": [2, 3]
    # "smaller_places": 7  "Alhamn"
},
{
    "code": 7,
    "name": "Alhamn",
    "area": 6312,
    "population": 3812,
    "density": 12,
    "municipality": [2, 3],
    "larger_place": 6 # Alvik
    # "smaller_places": 1  "Botten test"
},
{
    "code": 8,
    "name": "Bjurvik",
    "area": 6312,
    "population": 6212,
    "density": 12,
    "municipality": [2, 3],
    "larger_place": 6 # Alvik
    # "smaller_places": 1  "Botten test"
},
]


@pytest.fixture(scope='module')
def client_with_entries(es, client_with_data_f_scope_module):
    client_with_data = init(client_with_data_f_scope_module, es, ENTRIES)
    return client_with_data


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


def extract_names(entries):
    names = []
    for entry in entries['hits']:
        names.append(entry['entry']['name'])
    return names


def test_query_no_q(client_with_entries):
    entries = get_json(client_with_entries, 'places/query')

    names = extract_names(entries)

    assert entries['total'] == len(ENTRIES)
    assert len(names) == len(ENTRIES)
    print('names = {}'.format(names))

    for entry in ENTRIES:
        assert entry['name'] in names

    for i, name in enumerate(names):
        print('name = {}'.format(name))
        print('  entry = {}'.format(entries['hits'][i]['entry']))
        if name in ['Grund test', 'Hambo', 'Alhamn']:
            print("Testing 'larger_place' for '{}' ...".format(name))
            print('  entry = {}'.format(entries['hits'][i]['entry']))
            assert 'larger_place' in entries['hits'][i]['entry']
            assert 'v_larger_place' in entries['hits'][i]['entry']
        if name in ['Alvik', 'Botten test', 'Alhamn']:
            print("Testing 'smaller_places' for '{}' ...".format(name))
            print('  entry = {}'.format(entries['hits'][i]['entry']))
            assert 'v_smaller_places' in entries['hits'][i]['entry']


def test_and_equals_equals(client_with_entries):
    query = 'and||equals|population|4133||equals|area|50000'
    entries = get_json(client_with_entries, 'places/query?q=' + query)

    names = extract_names(entries)

    assert len(names) == 1
    assert 'Botten test' in names


def test_and_regexp_equals(client_with_entries):
    query = 'and||regexp|name|.*bo.*||equals|area|50000'
    entries = get_json(client_with_entries, 'places/query?q=' + query)

    names = extract_names(entries)

    assert len(names) == 2
    assert 'Hambo' in names
    assert 'Botten test' in names


def test_contains_string_lowercase(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=contains|name|Grund')
    names = extract_names(entries)
    assert len(names) == 2
    assert 'Grund test' in names
    assert 'Grunds' in names


def test_contains_string_correct_case(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=contains|name|Grund')
    names = extract_names(entries)
    assert len(names) == 2
    assert 'Grund test' in names
    assert 'Grunds' in names


def test_contains_raw_field_string_correct_case(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=contains|name.raw|Grund')
    names = extract_names(entries)
    assert len(names) == 2
    assert 'Grund test' in names
    assert 'Grunds' in names


@pytest.mark.skip(reason="regex can't handle integer")
def test_contains_integer(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=contains|population|3122')
    names = extract_names(entries)
    assert len(names) == 1
    assert 'Grund test' in names


def test_contains_1st_arg_and(client_with_entries):
    query = 'places/query?q=contains||and|name|v_smaller_places.name||Al'
    entries = get_json(client_with_entries, query)
    names = extract_names(entries)
    assert len(names) == 1
    assert 'Alvik' in names


@pytest.mark.skip(reason="regex can't handle complex")
def test_contains_1st_arg_and_2nd_arg_and(client_with_entries):
    query = 'places/query?q=contains||and|name|v_smaller_places.name||and|Al|vi'
    entries = get_json(client_with_entries, query)
    names = extract_names(entries)
    assert len(names) == 1
    assert 'Alvik' in names


def test_contains_1st_arg_not(client_with_entries):
    query = 'places/query?q=contains||not|name||test'
    entries = get_json(client_with_entries, query)
    names = extract_names(entries)
    assert len(names) == 6
    assert 'Grunds' in names
    assert 'Hambo' in names
    assert 'Alhamn' in names
    assert 'Rutvik' in names
    assert 'Alvik' in names
    assert 'Bjurvik' in names


def test_contains_1st_arg_or(client_with_entries):
    query = 'places/query?q=contains||or|name|v_smaller_places.name||Al'
    entries = get_json(client_with_entries, query)
    names = extract_names(entries)
    assert len(names) == 2
    assert 'Alvik' in names
    assert 'Alhamn' in names


def test_contains_2nd_arg_and(client_with_entries):
    query = 'places/query?q=contains|name||and|un|es'
    entries = get_json(client_with_entries, query)
    names = extract_names(entries)
    assert len(names) == 1
    assert 'Grund test' in names


def test_contains_2nd_arg_not(client_with_entries):
    query = 'places/query?q=contains|name||not|test'
    entries = get_json(client_with_entries, query)
    names = extract_names(entries)
    assert len(names) == 6
    assert 'Grunds' in names
    assert 'Hambo' in names
    assert 'Alhamn' in names
    assert 'Rutvik' in names
    assert 'Alvik' in names
    assert 'Bjurvik' in names


def test_contains_2nd_arg_or(client_with_entries):
    query = 'places/query?q=contains|name||or|vi|bo'
    entries = get_json(client_with_entries, query)
    names = extract_names(entries)
    assert len(names) == 5
    assert 'Alvik' in names
    assert 'Rutvik' in names
    assert 'Bjurvik' in names
    assert 'Botten test' in names
    assert 'Hambo' in names


def test_endswith_string_lower_case(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=endswith|name|est')
    names = extract_names(entries)
    assert len(names) == 2
    assert 'Grund test' in names
    assert 'Botten test' in names


def test_endswith_string_regex(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=endswith|name|unds')
    names = extract_names(entries)
    assert len(names) == 1
    assert 'Grunds' in names


def test_endswith_string_lower_case_first_word(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=endswith|name|grund')
    names = extract_names(entries)
    assert len(names) == 1
    assert 'Grund test' in names


def test_endswith_1st_arg_and(client_with_entries):
    query = 'places/query?q=endswith||and|name|v_larger_place||vik'
    entries = get_json(client_with_entries, query)
    names = extract_names(entries)
    assert len(names) == 1
    assert 'Bjurvik' in names


def test_endswith_1st_arg_not(client_with_entries):
    query = 'places/query?q=endswith||not|name||vik'
    entries = get_json(client_with_entries, query)
    names = extract_names(entries)
    assert len(names) == (len(ENTRIES) - 3)
    assert 'Grund test' in names


def test_endswith_1st_arg_or(client_with_entries):
    query = 'places/query?q=endswith||or|name|v_smaller_places||grund'
    entries = get_json(client_with_entries, query)
    names = extract_names(entries)
    assert len(names) == 1
    assert 'Grund test' in names


def test_endswith_2nd_arg_and(client_with_entries):
    query = 'places/query?q=endswith|name||and|grund|est'
    entries = get_json(client_with_entries, query)
    names = extract_names(entries)
    assert len(names) == 1
    assert 'Grund test' in names


def test_endswith_2nd_arg_not(client_with_entries):
    query = 'places/query?q=endswith|name||not|vik'
    entries = get_json(client_with_entries, query)
    names = extract_names(entries)
    assert len(names) == 5
    assert 'Grund test' in names


def test_endswith_2nd_arg_or(client_with_entries):
    query = 'places/query?q=endswith|name||or|vik|bo'
    entries = get_json(client_with_entries, query)
    names = extract_names(entries)
    assert len(names) == 4
    assert 'Hambo' in names
    assert 'Rutvik' in names
    assert 'Alvik' in names
    assert 'Bjurvik' in names


@pytest.mark.parametrize("field,value,expected_result", [
    ('name', 'grunds', ['Grunds']),
    ('name', 'Grunds', ['Grunds']),
    ('name', 'Grund test', ['Grund test']),
    ('name.raw', 'Grund test', ['Grund test']),
    ('name', '|and|grund|test', ['Grund test']),
    ('density', 7, ['Botten test']),
    ('|and|population|area|', 6312, ['Alvik']),
    ('|not|area|', 6312, ['Alhamn', 'Alvik', 'Bjurvik', 'Grund test']),
    ('|or|population|area|', 6312, [
        'Alhamn',
        'Alvik',
        'Bjurvik',
        'Grund test',
        'Grunds',
    ]),
    ('name', '|and|botten|test', ['Botten test']),
    ('area', '|not|6312', ['Grunds']),
    ('population', '|or|6312|3122', ['Alvik', 'Grund test', 'Grunds']),
])
def test_equals(client_with_entries, field: str, value, expected_result: List[str]):
    query = 'places/query?q=equals|{field}|{value}'.format(
        field=field,
        value=value
    )
    entries = get_json(client_with_entries, query)
    names = extract_names(entries)

    assert len(names) == len(expected_result)
    for name in names:
        assert name in expected_result
    for expected in expected_result:
        assert expected in names


def test_exists(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=exists|density')
    names = extract_names(entries)
    assert len(names) == 6
    assert 'Bjurvik' in names


def test_exists_and(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=exists||and|density|population')
    names = extract_names(entries)
    assert len(names) == 6
    assert 'Bjurvik' in names


def test_exists_or(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=exists||or|density|population')
    names = extract_names(entries)
    assert len(names) == 7
    assert 'Bjurvik' in names


def test_exists_not(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=exists||not|density')
    names = extract_names(entries)
    assert len(names) == 2

    assert 'Hambo' in names
    assert 'Rutvik' in names


def test_freergxp_and(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=freergxp||and|.*test|Gr.*')

    names = extract_names(entries)

    assert len(names) == 2
    assert 'Grund test' in names
    assert 'Alhamn' in names  # through smaller_places


# @pytest.mark.skip(reason='Currently only allow top level NOT')
def test_freergxp_not(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=freergxp||not|Gr.*')

    names = extract_names(entries)

    assert len(names) == 5
    assert 'Botten test' in names
    assert 'Hambo' in names
    assert 'Alvik' in names
    assert 'Rutvik' in names
    assert 'Bjurvik' in names


def test_freergxp_or(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=freergxp||or|.*test|Gr.*')

    names = extract_names(entries)

    assert len(names) == 5
    assert 'Grund test' in names
    assert 'Grunds' in names
    assert 'Botten test' in names
    assert 'Hambo' in names  # through smaller_places
    assert 'Alhamn' in names


def test_freergxp_string(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=freergxp|Grunds?')
    names = extract_names(entries)
    assert len(names) == 3
    assert 'Grund test' in names
    assert 'Grunds' in names
    assert 'Alhamn' in names


def test_freetext_string(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=freetext|grund')
    names = extract_names(entries)
    assert len(names) == 3
    assert 'Grund test' in names
    assert 'Grunds' in names
    assert 'Alhamn' in names  # through smaller_places


def test_freetext_integer(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=freetext|3122')
    names = extract_names(entries)
    assert len(names) == 1
    assert 'Grund test' in names


def test_freetext_and(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=freetext||and|botten|test')

    names = extract_names(entries)

    assert len(names) == 2
    assert 'Botten test' in names
    assert 'Hambo' in names  # through smaller_places


def test_freetext_not(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=freetext||not|botten')

    names = extract_names(entries)

    assert len(names) == 6
    assert 'Grund test' in names
    assert 'Grunds' in names
    assert 'Alhamn' in names
    assert 'Rutvik' in names
    assert 'Alvik' in names
    assert 'Bjurvik' in names


def test_freetext_or(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=freetext||or|botten|test')

    names = extract_names(entries)

    assert len(names) == 4
    assert 'Botten test' in names
    assert 'Hambo' in names  # through smaller_places
    assert 'Grund test' in names
    assert 'Alhamn' in names


def _test_against_entries(entries, field: str, predicate):
    names = extract_names(entries)

    if field.endswith('.raw'):
        field = field[:-4]

    assert len(names) == sum(1 for entry in ENTRIES if field in entry and predicate(entry[field]))

    num_names_to_match = len(names)
    for entry in ENTRIES:
        if field in entry and predicate(entry[field]):
            assert entry['name'] in names
            num_names_to_match -= 1
    assert num_names_to_match == 0


@pytest.mark.parametrize("field,value", [
    ('population', (4132,)),
    ('area', (20000,)),
    ('name', ('alvik', 'Alvik')),
    pytest.param('name', ('Alvik',), marks=pytest.mark.xfail),
    pytest.param('name', ('B',), marks=pytest.mark.xfail),
    ('name.raw', ('Alvik',)),
    ('name.raw', ('B',)),
    pytest.param('name', ('r','R'), marks=pytest.mark.xfail),
    pytest.param('name', ('R',), marks=pytest.mark.xfail),
    ('name.raw', ('r',)),
    ('name.raw', ('R',)),
])
def test_gt(client_with_entries, field, value):
    query = 'places/query?q=gt|{field}|{value}'.format(field=field, value=value[0])
    entries = get_json(client_with_entries, query)
    _test_against_entries(entries, field, lambda x: value[-1] < x)


@pytest.mark.parametrize("field,value", [
    ('population', (4132,)),
    ('area', (20000,)),
    ('name', ('alvik', 'Alvik')),
    pytest.param('name', ('Alvik',), marks=pytest.mark.xfail),
    pytest.param('name', ('B',), marks=pytest.mark.xfail),
    ('name.raw', ('Alvik',)),
    ('name.raw', ('B',)),
])
def test_gte(client_with_entries, field, value):
    query = 'places/query?q=gte|{field}|{value}'.format(field=field, value=value[0])
    entries = get_json(client_with_entries, query)

    _test_against_entries(entries, field, lambda x: value[-1] <= x)


@pytest.mark.parametrize("field,value", [
    ('population', (4132,)),
    ('area', (20000,)),
    ('name', ('alvik', 'Alvik')),
    pytest.param('name', ('Alvik',), marks=pytest.mark.xfail),
    pytest.param('name', ('B',), marks=pytest.mark.xfail),
    ('name.raw', ('Alvik',)),
    ('name.raw', ('B',)),
])
def test_lt(client_with_entries, field, value):
    query = 'places/query?q=lt|{field}|{value}'.format(field=field, value=value[0])
    entries = get_json(client_with_entries, query)

    _test_against_entries(entries, field, lambda x: x < value[-1])


@pytest.mark.parametrize("field,value", [
    ('population', (4132,)),
    ('area', (20000,)),
    ('name', ('alvik', 'Alvik')),
    pytest.param('name', ('Alvik',), marks=pytest.mark.xfail),
    pytest.param('name', ('B',), marks=pytest.mark.xfail),
    ('name.raw', ('Alvik',)),
    ('name.raw', ('B',)),
])
def test_lte(client_with_entries, field, value):
    query = 'places/query?q=lte|{field}|{value}'.format(field=field, value=value[0])
    entries = get_json(client_with_entries, query)

    _test_against_entries(entries, field, lambda x: x <= value[-1])


@pytest.mark.parametrize("field,lower,upper,expected_hits", [
    ('population', (3812,), (4133,), 1),
    ('area', (6312,), (50000,), 1),
    ('name', ('alhamn', 'Alhamn'), ('bjurvik', 'Bjurvik'), 1),
    pytest.param('name', ('b', 'B'), ('h', 'H'), 1, marks=pytest.mark.xfail),
    pytest.param('name', ('Alhamn',), ('Bjurvik',), 1, marks=pytest.mark.xfail),
    pytest.param('name', ('B',), ('H',), 1, marks=pytest.mark.xfail),
    ('name.raw', ('Alhamn',), ('Bjurvik',), 1),
    ('name.raw', ('B',), ('H',), 1),
])
def test_and_gt_lt(client_with_entries, field, lower, upper, expected_hits):
    query = 'places/query?q=and||gt|{field}|{lower}||lt|{field}|{upper}'.format(
        field=field,
        lower=lower[0],
        upper=upper[0]
    )
    entries = get_json(client_with_entries, query)

    _test_against_entries(entries, field, lambda x: lower[-1] < x < upper[-1])
    assert len(entries['hits']) == expected_hits


def test_missing(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=missing|density')
    names = extract_names(entries)
    assert len(names) == 2
    assert 'Hambo' in names
    assert 'Rutvik' in names


def test_missing_and(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=missing||and|density|population')
    names = extract_names(entries)
    assert len(names) == 1
    assert 'Rutvik' in names


def test_missing_not(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=missing||not|density')
    names = extract_names(entries)
    assert len(names) == 6
    assert 'Grund test' in names
    assert 'Grunds' in names
    assert 'Botten test' in names
    assert 'Alvik' in names
    assert 'Alhamn' in names
    assert 'Bjurvik' in names


def test_missing_or(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=missing||or|density|population')
    names = extract_names(entries)
    assert len(names) == 2
    assert 'Rutvik' in names
    assert 'Hambo' in names


def test_not_freetext(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=not||freetext|botten')

    names = extract_names(entries)

    assert len(names) == 6
    assert 'Grunds' in names
    assert 'Rutvik' in names
    assert 'Alvik' in names
    assert 'Bjurvik' in names
    assert 'Grund test' in names
    assert 'Alhamn' in names


def test_not_freergxp(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=not||freergxp|.*test')

    names = extract_names(entries)

    assert len(names) == 4
    assert 'Grunds' in names
    assert 'Rutvik' in names
    assert 'Alvik' in names
    assert 'Bjurvik' in names


def test_or(client_with_entries):
    query = 'or||equals|population|6312||equals|population|4132'
    entries = get_json(client_with_entries, 'places/query?q=' + query)
    names = extract_names(entries)
    assert len(names) == 3


def test_regex_string_lower_case(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=regexp|name|grun.*')
    names = extract_names(entries)
    assert len(names) == 2
    assert 'Grund test' in names
    assert 'Grunds' in names


def test_regex_string_correct_case(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=regexp|name|Grun.*')
    names = extract_names(entries)
    assert len(names) == 2
    assert 'Grund test' in names
    assert 'Grunds' in names


def test_regex_string_correct_case_question_mark(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=regexp|name|Grunds?')
    names = extract_names(entries)
    assert len(names) == 1
    assert 'Grunds' in names


def test_regex_string_lower_case_question_mark(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=regexp|name|grunds?')
    names = extract_names(entries)
    assert len(names) == 2
    assert 'Grund test' in names
    assert 'Grunds' in names


def test_regex_string_whole_name(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=regexp|name|Grun.*est')
    names = extract_names(entries)
    assert len(names) == 1
    assert 'Grund test' in names


def test_startswith_string_lower_case(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=startswith|name|grun')
    names = extract_names(entries)
    assert len(names) == 2
    assert 'Grund test' in names
    assert 'Grunds' in names


def test_startswith_string_correct_case(client_with_entries):
    entries = get_json(client_with_entries, 'places/query?q=startswith|name|Grun')
    names = extract_names(entries)
    assert len(names) == 2
    assert 'Grund test' in names
    assert 'Grunds' in names


@pytest.mark.skip(reason='no protected stuff')
def test_protected(client_with_data_scope_module):
    response = client_with_data_scope_module.get('/municipalities/query')
    assert '403 FORBIDDEN' in names


# def test_pagination_explicit_0_25(client_with_entries):
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
# def test_pagination_explicit_13_45(client_with_entries):
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
# def test_pagination_default_size(client_with_entries):
#     client = init_data(client_with_data_f, es, 30)
#     resource = 'places'
#     response = client.get('/{}/query?from=0'.format(resource))
#     assert response.status == '200 OK'
#     assert response.is_json
#     json_data = response.get_json()
#     assert len(json_data['hits']) == 25
#
#
# def test_pagination_default_from(client_with_entries):
#     client = init_data(client_with_data_f, es, 50)
#     resource = 'places'
#     response = client.get('/{}/query?size=45'.format(resource))
#     assert response.status == '200 OK'
#     assert response.is_json
#     json_data = response.get_json()
#     assert len(json_data['hits']) == 45
#
#
# def test_pagination_fewer(client_with_entries):
#     client = init_data(client_with_data_f, es, 5)
#     resource = 'places'
#     response = client.get('/{}/query?from=10'.format(resource))
#     assert response.status == '200 OK'
#     assert response.is_json
#     json_data = response.get_json()
#     assert len(json_data['hits']) == 0


def test_resource_not_existing(client_with_entries):
    response = client_with_entries.get('/asdf/query')
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
