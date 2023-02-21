from starlette import status


def test_healthz_works(fa_client):  # noqa: ANN201
    response = fa_client.get("/healthz")
    assert response.status_code == status.HTTP_200_OK
