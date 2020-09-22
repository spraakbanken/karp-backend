def test_get_yaml(fa_client):
    response = fa_client.get("/openapi.json")

    assert response.status_code == 200

    # print(f"{response!r}")
    # assert b"Karp API" in response.json()
    # assert b"Karp TNG" in response.json()
