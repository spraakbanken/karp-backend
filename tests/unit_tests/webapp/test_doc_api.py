def test_get_yaml(fa_client_wo_db):
    response = fa_client_wo_db.get("/openapi.json")

    assert response.status_code == 200

    print(f"{response.json()!r}")
    assert response.json()["info"]["title"] == "Karp API"
    # assert b"Karp TNG" in response.json()
