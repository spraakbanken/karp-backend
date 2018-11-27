

def test_no_q(client):
    response = client.get('/places/query')
    assert response.status == '200 OK'
    assert response.status_code == 200


def test_protected(client):
    response = client.get('/protected/query')
    assert response.status == '403 FORBIDDEN'


def test_pagination_explicit_0_25(client):
    response = client.get('/places/query?from=0&size=25')
    assert response.status == '200 OK'
    assert response.is_json
    json_data = response.get_json()
    assert json_data
    assert 'hits' in json_data
    assert 'hits' in json_data['hits']
    assert len(json_data['hits']['hits']) == 25


def test_pagination_explicit_13_45(client):
    response = client.get('/places/query?from=13&size=45')
    assert response.status == '200 OK'
    assert response.is_json
    json_data = response.get_json()
    assert json_data
    assert 'hits' in json_data
    assert 'hits' in json_data['hits']
    assert len(json_data['hits']['hits']) == 45


def test_pagination_default_size(client):
    response = client.get('/places/query?from=0')
    assert response.status == '200 OK'
    assert response.is_json
    json_data = response.get_json()
    assert len(json_data['hits']['hits']) == 25


def test_pagination_default_from(client):
    response = client.get('/places/query?size=25')
    assert response.status == '200 OK'
    assert response.is_json
    json_data = response.get_json()
    assert len(json_data['hits']['hits']) == 25
