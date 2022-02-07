import pytest
from starlette import status

from karp import auth
from karp.foundation.value_objects import unique_id
from karp.webapp.schemas import ResourceCreate, ResourcePublic


@pytest.fixture
def new_resource() -> ResourceCreate:
    return ResourceCreate(
        resource_id='test_resource',
        name='Test resource',
        message='test',
        config={
            'fields': {
                'foo': {'type': 'string'}
            },
            'id': 'foo',
        },
    )


class TestResourcesRoutes:
    def test_get_resources_exist(self, fa_data_client):
        response = fa_data_client.get('/resources')
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_post_resources_exist(self, fa_data_client):
        response = fa_data_client.post("/resources")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_get_resource_permissionss_exist(self, fa_data_client):
        response = fa_data_client.get('/resources/permissions')
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_get_resources(self, fa_data_client):
        response = fa_data_client.get('/resources/permissions')

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


class TestCreateResource:
    def test_missing_auth_header_returns_403(self, fa_data_client):
        response = fa_data_client.post("/resources/", json={})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_invalid_data_returns_422(
        self,
        fa_data_client,
        admin_token: auth.AccessToken
    ):
        response = fa_data_client.post(
            "/resources/",
            json={},
            headers=admin_token.as_header(),
        )
        print(f'{response.json()=}')
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_valid_input_creates_resource(
        self,
        fa_data_client,
        new_resource: ResourceCreate,
        admin_token: auth.AccessToken
    ):
        response = fa_data_client.post(
            '/resources/',
            json=new_resource.dict(),
            headers=admin_token.as_header(),
        )
        print(f'{response.json()=}')
        assert response.status_code == status.HTTP_201_CREATED

        created_resource = ResourceCreate(
            **response.json(),
        )
        assert created_resource == new_resource


class TestGetResource:
    def test_get_resource_by_resource_id(self, fa_data_client):
        response = fa_data_client.get('/resources/test_resource')
        print(f'{response.json()=}')
        assert response.status_code == status.HTTP_200_OK

        resource = ResourcePublic(**response.json())
        assert resource.resource_id == 'test_resource'

