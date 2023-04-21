from typing import Callable, Dict, List, Optional, Tuple

import pytest  # pyre-ignore
from fastapi import status
from karp import auth
from karp.lex.application.queries import EntryViews
from tests.common_data import MUNICIPALITIES, PLACES  # noqa: F401
from tests.utils import add_entries, get_json  # noqa: F401


def extract_names(entries):  # noqa: ANN201
    return [entry["entry"]["name"] for entry in entries["hits"]]


def extract_names_set(entries):  # noqa: ANN201
    return {entry["entry"]["name"] for entry in entries["hits"]}


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


def _test_path_has_expected_length(
    client,
    path: str,
    expected_length: int,
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

    assert len(entries["hits"]) == expected_length


def _test_against_entries(
    client,
    path: str,
    field: str,
    predicate: Callable,
    expected_n_hits: int = None,
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

    if field.endswith(".raw"):
        field = field[:-4]

    if expected_n_hits:
        assert len(entries["hits"]) == expected_n_hits
    else:
        assert len(names) == sum(
            bool(field in entry and predicate(entry[field])) for entry in PLACES
        )

    num_names_to_match = len(names)
    for entry in PLACES:
        if field in entry and predicate(entry[field]):
            assert entry["name"] in names
            num_names_to_match -= 1
    assert num_names_to_match == 0


def _test_against_entries_general(
    client,
    path: str,
    fields: Tuple[str, str],
    predicate: Callable,
    expected_n_hits: int = None,
    *,
    access_token: Optional[auth.AccessToken] = None,
    headers: Optional[Dict] = None,
) -> None:
    if access_token:
        if headers is None:
            headers = access_token.as_header()
        else:
            headers.update(access_token.as_header())
    kwargs = {"headers": headers} if headers else {}

    entries = get_json(client, path, **kwargs)
    names = extract_names(entries)

    print("names = {names}".format(names=names))
    for i, field in enumerate(fields):
        if field.endswith(".raw"):
            fields[i] = field[:-4]

    for field in fields:
        print("field = {field}".format(field=field))

    num_names_to_match = len(names)
    for entry in PLACES:
        print("entry = {entry}".format(entry=entry))
        if predicate(entry, fields):
            print("entry '{entry}' satisfied predicate".format(entry=entry))
            assert entry["name"] in names
            num_names_to_match -= 1
    assert num_names_to_match == 0

    if expected_n_hits:
        assert len(entries["hits"]) == expected_n_hits


class TestQuery:
    def test_route_exist(self, fa_data_client):  # noqa: ANN201
        response = fa_data_client.get("/query/places")
        print(f"{response.json()=}")
        assert response.status_code != status.HTTP_404_NOT_FOUND


def test_query_no_q(  # noqa: ANN201
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
        ("name.raw", "Grund"),
    ],
)
def test_contains(  # noqa: ANN201
    fa_data_client,
    field: str,
    value,
    app_context,
):
    query = f'/query/places?q=contains|{field}|"{value}"'
    entry_views = app_context.container.get(EntryViews)  # type: ignore [misc]
    expected_result = []
    real_field = field.split(".raw")[0]
    if real_field == field:
        analyzed_value = value
    else:
        analyzed_value = value.lower()
    print(f"{value=} {analyzed_value=}")
    for entry in entry_views.all_entries("places"):
        print(f"{entry=}")
        print(f"{entry.entry=}")
        print(f"{entry.entry.get(real_field, None)=}")
        if analyzed_value in entry.entry.get(real_field, "").lower():
            expected_result.append(entry.entry["name"])
    print(f"{expected_result=}")
    _test_path(fa_data_client, query, expected_result)


@pytest.mark.parametrize(
    "field,value,hit_count",
    [
        ("name", "a.*", 2),
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
