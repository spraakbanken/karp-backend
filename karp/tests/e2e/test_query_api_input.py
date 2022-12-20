import pytest

from fastapi import status


class TestQueryApiInput:
    @pytest.mark.parametrize(
        "query_string",
        [
            "sort=name",
            "sort=name|asc",
            "sort=name|desc",
            "from=10",
            "size=10",
            "q=",
            "q=&sort=name&from=0&size=25",
        ],
    )
    @pytest.mark.parametrize("path", ["query", "query/split"])
    def test_valid_query_strings(self, fa_client, path: str, query_string: str):
        response = fa_client.get(f"/{path}/places?{query_string}")

        print(f"{response.json()=}")
        assert response.status_code != status.HTTP_422_UNPROCESSABLE_ENTITY
