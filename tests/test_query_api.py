

def test_query(client):
    response = client.get('/places/query')
    assert response.status == '200 OK'
