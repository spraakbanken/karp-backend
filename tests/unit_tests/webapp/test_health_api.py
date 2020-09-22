def test_healthz(fa_client):
    response = fa_client.get("/healthz")
    assert response.status_code == 200
