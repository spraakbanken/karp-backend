from starlette import status


def test_healthz_works(fa_client):
    response = fa_client.get("/healthz")
    assert response.status_code == status.HTTP_200_OK
