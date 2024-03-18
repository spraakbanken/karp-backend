from typing import Callable, Dict, List, Optional, Tuple

import pytest  # pyre-ignore
from fastapi import status
from karp import auth
from karp.lex.application import EntryQueries
from tests.common_data import PLACES
from tests.utils import get_json


def extract_names(entries):
    return [entry["entry"]["name"] for entry in entries["hits"]]


def _test_path(
    client,
    path: str,
    expected_result: List[str],
    *,
    access_token: Optional[auth.AccessToken] = None,
    headers: Optional[Dict] = None,
) -> None:
    if access_token:
        if headers is None:
            headers = access_token.as_header()
        else:
            headers.extend(access_token.as_header())
    kwargs = {"headers": headers} if headers else {}

    entries = get_json(client, path, **kwargs)

    names = extract_names(entries)
    print("names = {names}".format(names=names))

    assert len(names) == len(expected_result)

    for name in names:
        assert name in expected_result

    for expected in expected_result:
        assert expected in names


class TestQuery:
    def test_route_exist(self, fa_data_client):
        response = fa_data_client.get("/query/places")
        print(f"{response.json()=}")
        assert response.status_code != status.HTTP_404_NOT_FOUND


def test_query_no_q(
    fa_data_client,
    read_token: auth.AccessToken,
    app_context,
):
    resource = "places"
    entries = get_json(
        fa_data_client,
        f"/query/{resource}",
        headers=read_token.as_header(),
    )

    names = extract_names(entries)

    expected_total = 22
    print(f"entries = {entries}")
    assert entries["total"] == expected_total
    assert len(names) == expected_total
    print("names = {}".format(names))


def test_query_split(  # noqa: ANN201
    fa_data_client,
    read_token: auth.AccessToken,
):
    resources = ["places", "municipalities"]
    entries = get_json(
        fa_data_client,
        "/query/split/{}".format(",".join(resources)),
        headers=read_token.as_header(),
    )

    assert entries["distribution"] == {"municipalities": 3, "places": 22}


@pytest.mark.parametrize(
    "field,value",
    [
        ("name", "grund"),
        ("name", "Grund"),
    ],
)
def test_contains(
    fa_data_client,
    field: str,
    value,
    app_context,
):
    query = f'/query/places?q=contains|{field}|"{value}"'
    entry_queries = app_context.injector.get(EntryQueries)  # type: ignore [misc]
    expected_result = []
    analyzed_value = value.lower()
    for entry in entry_queries.all_entries("places"):
        if analyzed_value in entry.entry.get(field, "").lower():
            expected_result.append(entry.entry["name"])
    _test_path(fa_data_client, query, expected_result)


@pytest.mark.parametrize(
    "field,value,hit_count",
    [
        ("name", "a.*", 6),
    ],
)
def test_regex(
    fa_data_client,
    field: str,
    value,
    hit_count,
    app_context,
):
    query = f'/query/places?q=regexp|{field}|"{value}"'
    response = fa_data_client.get(query)
    response_data = response.json()
    assert len(response_data["hits"]) == hit_count
    for hit in response_data["hits"]:
        print(hit["entry"]["name"])


# TODO: test that we can search for virtual fields
