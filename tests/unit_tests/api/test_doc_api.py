def test_get_yaml(client):
    response = client.get("/documentation/spec.yaml")

    assert 200 <= response.status_code < 300
