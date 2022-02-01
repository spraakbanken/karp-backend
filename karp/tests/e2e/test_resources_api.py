import pytest
from starlette import status


class TestResourcesRoutes:
    def test_get_routes_exist(self, fa_data_client):
        response = fa_data_client.get('/resources')
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_get_resources(self, fa_data_client):
        response = fa_data_client.get('/resources')

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert len(response_data) == 2
        assert response_data[0] == {
            'resource_id': 'places',
            'protected': None,
        }
        assert response_data[1] == {
            'resource_id': 'municipalities',
            'protected': 'READ',
        }
