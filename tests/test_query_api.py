

def test_query(client):
    response = client.get('/query')
    assert response.status == '200 OK'
