import pytest


@pytest.mark.usefixtures("places_published")
@pytest.mark.usefixtures("main_db")
def test_get_resources(fa_client):
    response = fa_client.get("/resources")

    assert response.status_code == 200

    response_data = response.json()

    assert len(response_data) == 1
    assert response_data[0] == {"resource_id": "places"}
