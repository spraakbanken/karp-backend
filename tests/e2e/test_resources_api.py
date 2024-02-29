from starlette import status

from karp.api.schemas import ResourcePublic


class TestResourcesRoutes:
    def test_get_resource_exist(self, fa_data_client):  # noqa: ANN201
        response = fa_data_client.get("/resources/places")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_get_resources_exist(self, fa_client):  # noqa: ANN201
        response = fa_client.get("/resources")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_post_resources_exist(self, fa_client):  # noqa: ANN201
        response = fa_client.post("/resources")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_get_resource_permissionss_exist(self, fa_client):  # noqa: ANN201
        response = fa_client.get("/resources/permissions")
        assert response.status_code != status.HTTP_404_NOT_FOUND


class TestGetResourcePermissions:
    def test_get_resources(self, fa_data_client):  # noqa: ANN201
        response = fa_data_client.get("/resources/permissions")

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert len(response_data) == 2
        assert response_data[0] == {
            "resource_id": "municipalities",
            "protected": "READ",
        }
        assert response_data[1] == {
            "resource_id": "places",
            "protected": None,
        }


class TestGetResource:
    def test_get_resource_by_resource_id(self, fa_data_client):  # noqa: ANN201
        response = fa_data_client.get("/resources/places")
        print(f"{response.json()=}")
        assert response.status_code == status.HTTP_200_OK

        resource = ResourcePublic(**response.json())
        assert resource.resource_id == "places"


class TestGetResources:
    def test_get_resources(self, fa_data_client):  # noqa: ANN201
        response = fa_data_client.get("/resources/")
        response_data = response.json()
        print(f"{response_data=}")
        assert response.status_code == status.HTTP_200_OK

        assert len(response_data) >= 3
        for resource_dict in response_data:
            ResourcePublic(**resource_dict)
