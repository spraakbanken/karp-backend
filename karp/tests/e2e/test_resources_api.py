import pytest

# pytestmark = pytest.mark.usefixtures("use_main_index")


def test_get_resources(fa_data_client):
    response = fa_data_client.get("/resources")

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
