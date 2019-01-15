import pytest  # pyre-ignore


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


@pytest.mark.skip(reason="places doesn't exist")
def test_pagination_explicit_0_25(client):
    resource = 'places'
    response = client.get('/{}/query?from=0&size=25'.format(resource))
    assert response.status == '200 OK'
    assert response.is_json
    json_data = response.get_json()
    assert json_data
    assert resource in json_data
    assert 'hits' in json_data[resource]
    assert len(json_data[resource]['hits']) == 25


@pytest.mark.skip(reason="places doesn't exist")
def test_pagination_explicit_13_45(client):
    resource = 'places'
    response = client.get('/{}/query?from=13&size=45'.format(resource))
    assert response.status == '200 OK'
    assert response.is_json
    json_data = response.get_json()
    assert json_data
    assert resource in json_data
    assert 'hits' in json_data[resource]
    assert len(json_data[resource]['hits']) == 45


@pytest.mark.skip(reason="places doesn't exist")
def test_pagination_default_size(client):
    resource = 'places'
    response = client.get('/{}/query?from=0'.format(resource))
    assert response.status == '200 OK'
    assert response.is_json
    json_data = response.get_json()
    assert len(json_data[resource]['hits']) == 25


@pytest.mark.skip(reason="places doesn't exist")
def test_pagination_default_from(client):
    resource = 'places'
    response = client.get('/{}/query?size=45'.format(resource))
    assert response.status == '200 OK'
    assert response.is_json
    json_data = response.get_json()
    assert len(json_data[resource]['hits']) == 45
