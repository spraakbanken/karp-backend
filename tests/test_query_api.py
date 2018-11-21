

def test_query(client):
    response = client.get('/places/query')
    assert response.status == '200 OK'


def test_protected(client):
    response = client.get('/protected/query')
    assert response.status == '403 FORBIDDEN'
