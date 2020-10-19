import json

import pytest  # pyre-ignore

from tests.utils import get_json


@pytest.mark.parametrize("endpoint", ["query", "query_split"])
@pytest.mark.parametrize(
    "query",
    [
        (""),
        ("freetext||eat my shorts"),
    ],
)
def test_distribution_in_result(
    fa_client_w_places_w_municipalities_scope_module, query, endpoint
):
    path = "/{endpoint}/places?{query}lexicon_stats=true".format(
        endpoint=endpoint, query="q={}&".format(query) if query else ""
    )
    result = get_json(
        fa_client_w_places_w_municipalities_scope_module,
        path,
        headers={"Authorization": "Bearer 1234"},
    )

    assert "distribution" in result
