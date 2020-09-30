def test_get_resources(fa_client_w_places):
    response = fa_client_w_places.get("/resources")

    assert response.status_code == 200
