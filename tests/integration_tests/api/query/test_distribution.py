import json

import pytest  # pyre-ignore

from tests.utils import get_json


@pytest.mark.parametrize("endpoint", ["query", "query_split"])
@pytest.mark.parametrize("query", [(""), ("freetext||eat my shorts"),])
def test_distribution_in_result(client_with_entries_scope_session, query, endpoint):
    path = "places/{endpoint}?{query}lexicon_stats=true".format(
        endpoint=endpoint, query="q={}&".format(query) if query else ""
    )
    result = get_json(client_with_entries_scope_session, path)

    assert "distribution" in result
