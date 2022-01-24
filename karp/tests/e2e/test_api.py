import pytest
from starlette import status


class TestResourcesRoutes:
    def test_routes_exist(self, fa_client):
        response = fa_client.get("/resources")
        assert response.status_code != status.HTTP_404_NOT_FOUND


class TestEntriesRoutes:
    def test_routes_exist(self, fa_client):
        response = fa_client.post("/places/add")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize("invalid_data", [
        ({},),
        ({},),
    ])
    def test_invalid_data_returns_422(self, fa_client, invalid_data):
        response = fa_client.post("/places/add", json=invalid_data)
        print(f'{response.json()=}')
        assert response.status_code != status.HTTP_422_UNPROCESSABLE_ENTITY
