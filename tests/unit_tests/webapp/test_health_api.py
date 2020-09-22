def test_healthz(client):
    response = client.get("/healthz")
    assert response.status == "200 OK"
