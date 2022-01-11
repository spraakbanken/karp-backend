import pytest

# pytestmark = pytest.mark.usefixtures("use_main_index")


@pytest.mark.usefixtures("municipalites_published")
@pytest.mark.usefixtures("places_published")
@pytest.mark.usefixtures("main_db")
def test_get_resources(fa_client):
    response = fa_client.get("/resources")

    assert response.status_code == 200

    response_data = response.json()

    assert len(response_data) == 2
    assert response_data[0] == {
        "resource_id": "places",
        'protected': None,
    }
    assert response_data[1] == {
        "resource_id": "municipalities",
        'protected': 'READ',
    }
