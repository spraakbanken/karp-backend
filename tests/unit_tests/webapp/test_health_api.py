def test_healthz(fa_client_wo_db):
    response = fa_client_wo_db.get("/healthz")
    assert response.status_code == 200
