from starlette import status

from karp.api.routes.resources_api import ResourceConfigResponse


class TestGetResources:
    def test_get_resources(self, fa_data_client):  # noqa: ANN201
        response = fa_data_client.get("/resources/")
        response_data = response.json()
        print(f"{response_data=}")
        assert response.status_code == status.HTTP_200_OK

        assert len(response_data) >= 2
        for resource_dict in response_data:
            ResourceConfigResponse(**resource_dict)
