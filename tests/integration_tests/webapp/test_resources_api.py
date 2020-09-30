def test_get_resources(fa_client_w_places):
    response = fa_client_w_places.get("/resources")

    assert response.status_code == 200

    response_data = response.json()

    assert len(response_data) == 1
    assert response_data[0] == {"resource_id": "places"}
