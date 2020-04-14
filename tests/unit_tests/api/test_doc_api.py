
def test_get_yaml(client):
    response = client.get("/documentation/spec.yaml")

    assert 200 <= response.status_code < 300

    print(f"{response!r}")
    assert b"Karp API" in response.data
    assert b"Karp TNG" in response.data
