import pytest

# from karp.application.services import entries, resources

# from karp.tests.common_data import MUNICIPALITIES, PLACES
# from karp.tests.utils import get_json, add_entries


# @pytest.fixture(scope="session", name="fa_stats_data_client")
# def fixture_fa_stats_data_client(fa_client_w_places_w_municipalities_scope_module):
#     add_entries(
#         fa_client_w_places_w_municipalities_scope_module,
#         {"places": PLACES, "municipalities": MUNICIPALITIES},
#     )

#     return fa_client_w_places_w_municipalities_scope_module


def test_stats(fa_data_client):
    response = fa_data_client.get(
        "/stats/places/area",
        headers={"Authorization": "Bearer 1234"},
    )
    assert response.status_code == 200

    entries = response.json()
    print(f'{entries=}')
    assert len(entries) == 4
