

def test_no_q(client):
    response = client.get('/places/query')
    assert response.status == '200 OK'


def test_protected(client):
    response = client.get('/protected/query')
    assert response.status == '403 FORBIDDEN'


def test_pagination_explicit(client):
    response = client.get('/places/query?from=0&size=25')
    assert response.status == '200 OK'


def test_pagination_default_size(client):
    response = client.get('/places/query?from=0')
    assert response.status == '200 OK'


def test_pagination_default_from(client):
    response = client.get('/places/query?size=25')
    assert response.status == '200 OK'
