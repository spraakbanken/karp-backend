from typing import Dict, List, Optional

import pytest
from fastapi import status

from karp.lex.application import EntryQueries
from tests.e2e.conftest import AccessToken
from tests.utils import get_json


def extract_names(entries):
    return [entry["entry"]["name"] for entry in entries["hits"]]


def _test_path(
    client,
    path: str,
    expected_result: List[str],
    *,
    access_token: Optional[AccessToken] = None,
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


def test_query_with_highlight(fa_data_client):
    entries = get_json(fa_data_client, "/query/places?q=freetext|Norsjö&highlight=true")
    assert len(entries["hits"]) > 0
    for entry in entries["hits"]:
        assert "highlight" in entry


def test_query_without_highlight(fa_data_client):
    # test that default is false and that false can be set manually
    urls = ["/query/places?q=freetext|Norsjö", "/query/places?q=freetext|Norsjö&highlight=false"]
    for url in urls:
        entries = get_json(fa_data_client, url)
        assert len(entries["hits"]) > 0
        for entry in entries["hits"]:
            assert "highlight" not in entry


def test_query_no_q_with_highlight(fa_data_client):
    entries = get_json(fa_data_client, "/query/places?highlight=true")
    assert len(entries["hits"]) > 0
    for entry in entries["hits"]:
        assert "highlight" not in entry


def test_subfield_query(fa_data_client):
    entries = get_json(fa_data_client, "/query/places?q=equals|name|Alvik")
    assert len(entries["hits"]) == 1

    entries = get_json(fa_data_client, "/query/places?q=_municipality(freetext|Alvik)")
    assert len(entries["hits"]) == 0


def test_subfield_query2(fa_data_client):
    # there is one place in test data called "Piteå" that does not have municipality "Piteå kommun".
    entries = get_json(fa_data_client, "/query/places?q=freetext|Piteå")
    assert entries["total"] == 15

    # in this query, we should not get the place with name=Piteå, since we search in "_municipality"
    entries = get_json(fa_data_client, "/query/places?q=_municipality(freetext|Piteå)")
    assert entries["total"] == 14


def test_query_no_q(
    fa_data_client,
    read_token: AccessToken,
    app_context,
):
    resource = "places"
    entries = get_json(
        fa_data_client,
        f"/query/{resource}",
        headers=read_token.as_header(),
    )

    names = extract_names(entries)

    expected_total = 23
    print(f"entries = {entries}")
    assert entries["total"] == expected_total
    assert len(names) == expected_total
    print("names = {}".format(names))


def test_query_stats(
    fa_data_client,
    read_token: AccessToken,
):
    resources = ["places", "municipalities"]
    entries = get_json(
        fa_data_client,
        "/query/stats/{}".format(",".join(resources)),
        headers=read_token.as_header(),
    )

    assert entries["distribution"] == {"municipalities": 3, "places": 23}


def test_equals(
    fa_data_client,
    read_token: AccessToken,
):
    """
    Goal of this test is to do equals on texts, integers and floats. Extend if new types are available.
    """
    all_entries = get_json(fa_data_client, "/query/municipalities?size=1000", headers=read_token.as_header())

    for entry in all_entries["hits"]:
        body = entry["entry"]
        for key in ["code", "name", "population.density.total"]:
            val = body
            for elem in key.split("."):
                val = val[elem]
            # search for the found in the same field
            query = f"/query/municipalities?q=equals|{key}|{val}"
            cmp_entries = get_json(fa_data_client, query, headers=read_token.as_header())
            # check that the ID of the outer entry is found in the query
            assert entry["id"] in [cmp_entry["id"] for cmp_entry in cmp_entries["hits"]]


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


def test_path_parameter(fa_data_client):
    query = f"/query/places?path=entry._municipality.code"
    response = fa_data_client.get(query)
    response_data = response.json()
    # there are different number of hits if running in isolation or
    # with other tests, so just check that some expected values are in there
    assert [1] in response_data["hits"]
    assert [2] in response_data["hits"]
    assert [3] in response_data["hits"]
    assert [2, 3] in response_data["hits"]


# TODO: test that we can search for virtual fields
