import pytest
from fastapi import status
from karp import auth


def test_stats_wo_auth(fa_data_client):
    response = fa_data_client.get(
        "/stats/places/area",
    )
    assert response.status_code == status.HTTP_200_OK

    entries = response.json()
    print(f"{entries=}")
    assert len(entries) == 4


def test_stats_w_auth(fa_data_client, read_token: auth.AccessToken):
    response = fa_data_client.get(
        "/stats/places/area",
        headers=read_token.as_header(),
    )
    assert response.status_code == status.HTTP_200_OK

    entries = response.json()
    print(f"{entries=}")
    assert len(entries) == 4
