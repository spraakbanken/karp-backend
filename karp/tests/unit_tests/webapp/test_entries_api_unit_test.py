from karp.errors import ClientErrorCodes


def test_add_fails_with_invalid_entry(fa_client_w_places):
    response = fa_client_w_places.post(
        "places/add", json={"entry": {}}, headers={"Authorization": "Bearer 1234"}
    )

    assert response.status_code == 400
    response_data = response.json()

    assert response_data["error"] == "entry not valid"
    assert response_data["errorCode"] == ClientErrorCodes.ENTRY_NOT_VALID
