import json
from typing import Callable, Dict, List, Optional, Tuple

import pytest  # pyre-ignore
from fastapi import status

from karp import auth
from karp.lex.application.queries import EntryViews
from karp.tests.common_data import MUNICIPALITIES, PLACES
from karp.tests.utils import add_entries, get_json


def extract_names(entries):
    return [entry["entry"]["name"] for entry in entries["hits"]]


def extract_names_set(entries):
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

    entry_views = app_context.container.get(EntryViews)  # type: ignore [misc]
    expected_result = {}
    expected_total = entry_views.get_total(resource)
    print(f"entries = {entries}")
    assert entries["total"] == expected_total
    assert len(names) == expected_total
    print("names = {}".format(names))

    # for entry in PLACES:
    #     assert entry["name"] in names

    return

    for i, name in enumerate(names):
        print("name = {}".format(name))
        print("  entry = {}".format(entries["hits"][i]["entry"]))
        if name in ["Grund test", "Hambo", "Alhamn"]:
            print("Testing 'larger_place' for '{}' ...".format(name))
            print("  entry = {}".format(entries["hits"][i]["entry"]))
            assert "larger_place" in entries["hits"][i]["entry"]
            assert "v_larger_place" in entries["hits"][i]["entry"]
        if name == "Alvik":
            print("Testing 'smaller_places' for '{}' ...".format(name))
            print("  entry = {}".format(entries["hits"][i]["entry"]))
            assert "v_smaller_places" in entries["hits"][i]["entry"]
            assert (
                entries["hits"][i]["entry"]["v_smaller_places"][0]["name"] == "Bjurvik"
            )
        elif name in ["Botten test", "Alhamn"]:
            print("Testing 'smaller_places' for '{}' ...".format(name))
            print("  entry = {}".format(entries["hits"][i]["entry"]))
            assert "v_smaller_places" in entries["hits"][i]["entry"]


def test_query_split(
    fa_data_client,
    read_token: auth.AccessToken,
):
    resources = ["places", "municipalities"]
    entries = get_json(
        fa_data_client,
        "/query/split/{}".format(",".join(resources)),
        headers=read_token.as_header(),
    )

    entry_views = fa_data_client.app.state.app_context.container.get(EntryViews)
    expected_result = {}
    for resource in resources:
        expected_result[resource] = entry_views.get_total(resource)
    assert entries["distribution"] == expected_result
    # assert entries["distribution"] == {"municipalities": 3, "places": 22}


@pytest.mark.xfail(reason="unstable")
@pytest.mark.parametrize(
    "queries,expected_result",
    [
        (["equals|population|4133", "equals|area|50000"], ["Botten test"]),
        (["regexp|name|.*bo.*", "equals|area|50000"], ["Hambo", "Botten test"]),
        (["regexp|name|.*bo.*", "equals|area|50000", "missing|density"], ["Hambo"]),
    ],
)
def test_and(
    fa_data_client,
    queries: List[str],
    expected_result: List[str],
):
    query = "/query/places?q=and({queries})".format(queries="||".join(queries))
    _test_path(fa_data_client, query, expected_result)


@pytest.mark.parametrize(
    "field,value",
    [
        ("name", "grund"),
        ("name", "Grund"),
        ("name.raw", "Grund"),
        # pytest.param(
        #     "population",
        #     3122,
        #     ["Grund test"],
        #     marks=pytest.mark.skip(
        #         reason="Can't search with regex on LONG fields"),
        # ),
        # ("|and|name|v_larger_place.name|", "vi", ["Bjurvik"]),
        # pytest.param(
        #     "|and|name|v_smaller_places.name|",
        #     "and|Al|vi",
        #     ["Alvik"],
        #     marks=pytest.mark.xfail(reason="regex can't handle complex"),
        # ),
        # pytest.param(
        #     "|not|name|",
        #     "test",
        #     ["Hambo", "Alhamn", "Bjurvik", "Bjurvik2"],
        #     marks=pytest.mark.xfail(reason="?"),
        # ),
        # ("|or|name|v_smaller_places.name|",
        #  "Al", ["Alvik", "Alhamn", "Hambo"]),
        # ("name", "|and|un|es", ["Grund test"]),
        # pytest.param(
        #     "name",
        #     "|or|vi|bo",
        #     ["Alvik", "Rutvik", "Bjurvik", "Botten test", "Hambo", "Bjurvik2"],
        #     marks=pytest.mark.xfail(reason="?"),
        # ),
    ],
)
def test_contains(
    fa_data_client,
    field: str,
    value,
    app_context,
):
    query = f"/query/places?q=contains|{field}|{value}"
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


@pytest.mark.xfail(reason="unstable")
@pytest.mark.parametrize(
    "fields,values,expected_result",
    [(("name", "v_larger_place.name"), ("vi", "vi"), ["Bjurvik"])],
)
def test_contains_and_separate_calls(
    fa_data_client,
    fields: Tuple,
    values: Tuple,
    expected_result: List[str],
):
    names = set()
    for field, value in zip(fields, values):
        query = f"/query/places?q=contains|{field}|{value}"
        entries = get_json(
            fa_data_client,
            query,
        )
        if not names:
            print("names is empty")
            names = extract_names_set(entries)
        else:
            names = names & extract_names_set(entries)

    assert len(names) == len(expected_result)
    for name in names:
        assert name in expected_result
    for expected in expected_result:
        assert expected in names


@pytest.mark.xfail(reason="unstable")
@pytest.mark.parametrize(
    "field,value,expected_result",
    [
        ("name", "est", ["Grund test", "Botten test"]),
        ("name", "unds", ["Grunds"]),
        ("name", "grund", ["Grund test"]),
        # pytest.param("population", 3122, [
        #              "Grund test"], marks=pytest.mark.skip),
        # ("|and|name|v_smaller_places.name|", "vik", ["Alvik"]),
        # ("|and|name|v_larger_place.name|", "vik", ["Bjurvik"]),
        # pytest.param(
        #     "|and|name|v_smaller_places.name|",
        #     "and|Al|vi",
        #     ["Alvik"],
        #     marks=pytest.mark.skip(reason="regex can't handle complex"),
        # ),
        # pytest.param(
        #     "|not|name|",
        #     "vik",
        #     [
        #         "Botten test",  # through larger_place
        #         "Alvik",  # through smaller_places
        #         "Bjurvik",  # through larger_place
        #     ],
        #     marks=pytest.mark.xfail(reason="Too restrictive"),
        # ),
        # ("|or|name|v_smaller_places.name|",
        #  "otten", ["Botten test", "Bjurvik"]),
        # ("name", "|and|und|est", ["Grund test"]),
        # ("name", "|or|vik|bo", ["Alvik", "Rutvik", "Bjurvik", "Hambo"]),
    ],
)
def test_endswith(fa_data_client, field: str, value, expected_result: List[str]):
    query = f"/query/places?q=endswith|{field}|{value}"
    _test_path(fa_data_client, query, expected_result)


@pytest.mark.xfail(reason="unstable")
@pytest.mark.parametrize(
    "field,value,expected_result",
    [
        ("name", "grunds", ["Grunds"]),
        ("name", "Grunds", ["Grunds"]),
        ("name", "Grund test", ["Grund test"]),
        ("name.raw", "Grund test", ["Grund test"]),
        # ("name", "|and|grund|test", ["Grund test"]),
        ("density", 7, ["Botten test"]),
        # ("|and|population|area|", 6312, ["Alvik"]),
        # pytest.param(
        #     "|and|area||or|population|density|",
        #     6312,
        #     ["Alvik", "Grund test"],
        #     marks=pytest.mark.xfail(
        #         reason="Current query dsl can't handle this."),
        # ),
        # pytest.param(
        #     "|not|area|",
        #     6312,
        #     ["Alvik", "Grunds"],
        #     marks=pytest.mark.xfail(reason="Too restrictive."),
        # ),
        # (
        #     "|or|population|area|",
        #     6312,
        #     ["Alhamn", "Alvik", "Bjurvik", "Grund test", "Grunds"],
        # ),
        # ("name", "|and|botten|test", ["Botten test"]),
        # ("population", "|or|6312|3122", ["Alvik", "Grund test", "Grunds"]),
    ],
)
def test_equals(fa_data_client, field: str, value, expected_result: List[str]):
    query = f"/query/places?q=equals|{field}|{value}"
    _test_path(fa_data_client, query, expected_result)


@pytest.mark.xfail(reason="unstable")
@pytest.mark.parametrize(
    "field,expected_result",
    [
        # (
        #     "|and|v_larger_place|v_smaller_places",
        #     ["Bjurvik", "Hambo", "Botten test", "Alhamn", "Grund test"],
        # ),
        ("name", [])
    ],
)
def test_exists(fa_data_client, field: str, expected_result: List[str]):
    query = f"/query/places?q=exists|{field}"
    _test_path(fa_data_client, query, expected_result)


@pytest.mark.xfail(reason="unstable")
@pytest.mark.parametrize(
    "field,expected_result",
    [
        pytest.param(
            "|and|.*test|Gr.*",
            [
                "Grund test",
                "Alhamn",  # through smaller_places
                "Bjurvik2",  # through larger_place
            ],
            marks=pytest.mark.xfail(reason="?"),
        ),
        # ("|not|Gr.*", ["Botten test", "Hambo", "Alvik", "Rutvik", "Bjurvik"]),
        pytest.param(
            "|or|.*test|Gr.*",
            [
                "Grund test",
                "Grunds",
                "Botten test",
                "Hambo",  # through larger_place
                "Alhamn",  # through smaller_places
                "Bjurvik",  # through smaller_places
                "Bjurvik2",  # through larger_place
            ],
            marks=pytest.mark.xfail(reason="?"),
        ),
        pytest.param(
            "Grunds?",
            ["Grund test", "Grunds", "Bjurvik2", "Alhamn"],
            marks=pytest.mark.xfail(reason="?"),
        ),
    ],
)
def test_freergxp(fa_data_client, field: str, expected_result: List[str]):
    query = f"/query/places?q=freergxp|{field}"
    _test_path(fa_data_client, query, expected_result)


@pytest.mark.xfail(reason="unstable")
@pytest.mark.parametrize(
    "field,expected_result",
    [
        pytest.param(
            "grund",
            [
                "Grund test",
                "Grunds",
                "Alhamn",  # through smaller_places
                "Bjurvik2",  # through larger_place
            ],
            marks=pytest.mark.xfail(reason="?"),
        ),
        ("3122", ["Grund test"]),
        (3122, ["Grund test"]),
        # (
        #     "|and|botten|test",
        #     [
        #         "Botten test",
        #         "Hambo",  # through larger_place
        #         "Bjurvik",  # through smaller_places
        #     ],
        # ),
        pytest.param(
            "|or|botten|test",
            [
                "Botten test",
                "Hambo",  # through smaller_places
                "Grund test",
                "Alhamn",  # through smaller_places
                "Bjurvik",  # through smaller_places
                "Bjurvik2",  # through larger_places
            ],
            marks=pytest.mark.xfail(reason="?"),
        ),
    ],
)
def test_freetext(fa_data_client, field: str, expected_result: List[str]):
    query = f"/query/places?q=freetext|{field}"
    _test_path(fa_data_client, query, expected_result)


@pytest.mark.xfail(reason="unstable")
@pytest.mark.parametrize(
    "field,value,expected_n_hits",
    [
        ("population", (4132,), 4),
        ("area", (20000,), 11),
        ("name", ("alvik", "Alvik"), 16),
        pytest.param(
            "name",
            ("Alvik",),
            2,
            marks=pytest.mark.skip(
                reason="'name' is lower case, so greater than Uppercase returns all."
            ),
        ),
        pytest.param(
            "name",
            ("B",),
            2,
            marks=pytest.mark.skip(
                reason="'name' is lower case, so greater than Uppercase returns all."
            ),
        ),
        ("name.raw", ("Alvik",), 20),
        ("name.raw", ("B",), 20),
        pytest.param(
            "name",
            ("r", "R"),
            2,
            marks=pytest.mark.xfail(
                reason="'name' is tokenized, so greater than matches second word."
            ),
        ),
        pytest.param(
            "name",
            ("R",),
            2,
            marks=pytest.mark.xfail(
                reason="'name' is lower case, so greater than Uppercase returns all."
            ),
        ),
        ("name.raw", ("r",), 5),
        ("name.raw", ("R",), 15),
    ],
)
def test_gt(fa_data_client, field, value, expected_n_hits):
    query = f"/query/places?q=gt|{field}|{value[0]}"
    _test_path_has_expected_length(fa_data_client, query, expected_n_hits)
    # _test_against_entries(fa_data_client, query, field, lambda x: value[-1] < x)


@pytest.mark.xfail(reason="unstable")
@pytest.mark.parametrize(
    "field,value,expected_n_hits",
    [
        ("population", (4132,), 5),
        ("area", (20000,), 12),
        ("name", ("alvik", "Alvik"), 17),
        pytest.param(
            "name",
            ("Alvik",),
            2,
            marks=pytest.mark.skip(
                reason="'name' is lower case, so greater than Uppercase returns all."
            ),
        ),
        pytest.param(
            "name",
            ("B",),
            2,
            marks=pytest.mark.skip(
                reason="'name' is lower case, so greater than Uppercase returns all."
            ),
        ),
        ("name.raw", ("Alvik",), 21),
        ("name.raw", ("B",), 20),
    ],
)
def test_gte(fa_data_client, field, value, expected_n_hits):
    query = f"/query/places?q=gte|{field}|{value[0]}"
    _test_path_has_expected_length(fa_data_client, query, expected_n_hits)
    # _test_against_entries(fa_data_client, query, field, lambda x: value[-1] <= x)


@pytest.mark.xfail(reason="unstable")
@pytest.mark.parametrize(
    "field,value,expected_n_hits",
    [
        ("population", (4132,), 10),
        ("area", (20000,), 4),
        ("name", ("alvik", "Alvik"), 5),
        pytest.param(
            "name",
            ("Alvik",),
            2,
            marks=pytest.mark.skip(
                reason="'name' is lower case, so lesser than Uppercase returns all."
            ),
        ),
        pytest.param(
            "name",
            ("B",),
            2,
            marks=pytest.mark.skip(
                reason="'name' is lower case, so lesser than Uppercase returns all."
            ),
        ),
        ("name.raw", ("Alvik",), 1),
        ("name.raw", ("B",), 2),
    ],
)
def test_lt(fa_data_client, field, value, expected_n_hits: int):
    query = f"/query/places?q=lt|{field}|{value[0]}"
    _test_path_has_expected_length(fa_data_client, query, expected_n_hits)
    # _test_against_entries(fa_data_client, query, field, lambda x: x < value[-1])


@pytest.mark.xfail(reason="unstable")
@pytest.mark.parametrize(
    "field,value,expected_n_hits",
    [
        ("population", (4132,), 11),
        ("area", (20000,), 5),
        ("name", ("alvik", "Alvik"), 6),
        pytest.param(
            "name",
            ("Alvik",),
            2,
            marks=pytest.mark.skip(
                reason="'name' is lower case, so lesser than Uppercase returns all."
            ),
        ),
        pytest.param(
            "name",
            ("B",),
            2,
            marks=pytest.mark.skip(
                reason="'name' is lower case, so lesser than Uppercase returns all."
            ),
        ),
        ("name.raw", ("Alvik",), 2),
        ("name.raw", ("B",), 2),
    ],
)
def test_lte(fa_data_client, field, value, expected_n_hits: int):
    query = f"/query/places?q=lte|{field}|{value[0]}"
    _test_path_has_expected_length(fa_data_client, query, expected_n_hits)
    # _test_against_entries(fa_data_client, query, field, lambda x: x <= value[-1])


@pytest.mark.skip()
@pytest.mark.parametrize(
    "op,fields,value,expected_n_hits",
    [
        ("gt", ("population", "area"), (6212,), 2),
        (
            "gt",
            ("name", "v_smaller_places.name"),
            ("bjurvik",),
            4,
        ),
        ("gte", ("population", "area"), (6212,), 3),
        (
            "gte",
            ("name", "v_smaller_places.name"),
            ("bjurvik",),
            5,
        ),
        ("lt", ("population", "area"), (6313,), 4),
        ("lt", ("name", "v_smaller_places.name"), ("c",), 2),
        ("lte", ("population", "area"), (6312,), 4),
        ("lte", ("name", "v_smaller_places.name"), ("bjurvik",), 1),
    ],
)
def test_binary_range_1st_arg_and(
    fa_data_client,
    op: str,
    fields: Tuple[str, str],
    value: Tuple,
    expected_n_hits: int,
):
    query = f"/query/places?q={op}||and|{fields[0]}|{fields[1]}||{value[0]}"
    _test_path_has_expected_length(fa_data_client, query, expected_n_hits)
    # if expected_result:
    #     _test_path(fa_data_client, query, expected_result)

    # elif op == "gt":
    #     _test_against_entries_general(
    #         fa_data_client,
    #         query,
    #         fields,
    #         lambda entry, fields: all(
    #             f in entry and value[-1] < entry[f] for f in fields
    #         ),
    #     )
    # elif op == "gte":
    #     _test_against_entries_general(
    #         fa_data_client,
    #         query,
    #         fields,
    #         lambda entry, fields: all(
    #             f in entry and value[-1] <= entry[f] for f in fields
    #         ),
    #     )
    # elif op == "lt":
    #     _test_against_entries_general(
    #         fa_data_client,
    #         query,
    #         fields,
    #         lambda entry, fields: all(
    #             f in entry and entry[f] < value[-1] for f in fields
    #         ),
    #     )
    # elif op == "lte":
    #     _test_against_entries_general(
    #         fa_data_client,
    #         query,
    #         fields,
    #         lambda entry, fields: all(
    #             f in entry and entry[f] <= value[-1] for f in fields
    #         ),
    #     )
    # else:
    #     pytest.fail(msg="Unknown range operator '{op}'".format(op=op))


# @pytest.mark.parametrize(
#     "op,fields,value,expected_n_hits",
#     [
#         ("gt", ("population", "area"), (6212,), 16),
#         (
#             "gt",
#             ("name", "v_smaller_places.name"),
#             ("bjurvik",),
#             16,
#         ),
#         ("gte", ("population", "area"), (6212,), 16),
#         (
#             "gte",
#             ("name", "v_smaller_places.name"),
#             ("bjurvik",),
#             17,
#         ),
#         ("lt", ("population", "area"), (6212,), 12),
#         (
#             "lt",
#             ("name", "v_smaller_places.name"),
#             ("bjurvik",),
#             8,
#         ),
#         ("lte", ("population", "area"), (6212,), 13),
#         (
#             "lte",
#             ("name", "v_smaller_places.name"),
#             ("bjurvik",),
#             9,
#         ),
#     ],
# )
# def test_binary_range_1st_arg_or(
#     fa_data_client,
#     op: str,
#     fields: Tuple,
#     value: Tuple,
#     expected_n_hits: int,
# ):
#     query = f"/query/places?q={op}||or|{fields[0]}|{fields[1]}||{value[0]}"
#     _test_path_has_expected_length(fa_data_client, query, expected_n_hits)

# elif op == "gt":
#     _test_against_entries_general(
#         fa_data_client,
#         query,
#         fields,
#         lambda entry, fields: any(
#             f not in entry or value[-1] < entry[f] for f in fields
#         ),
#     )
# elif op == "gte":
#     _test_against_entries_general(
#         fa_data_client,
#         query,
#         fields,
#         lambda entry, fields: any(
#             f not in entry or value[-1] <= entry[f] for f in fields
#         ),
#     )
# elif op == "lt":
#     _test_against_entries_general(
#         fa_data_client,
#         query,
#         fields,
#         lambda entry, fields: any(
#             f in entry and entry[f] < value[-1] for f in fields
#         ),
#     )
# elif op == "lte":
#     _test_against_entries_general(
#         fa_data_client,
#         query,
#         fields,
#         lambda entry, fields: any(
#             f in entry and entry[f] <= value[-1] for f in fields
#         ),
#     )
# else:
#     pytest.fail(msg=f"Unknown range operator '{op}'")


@pytest.mark.xfail(reason="unstable")
@pytest.mark.parametrize(
    "field,lower,upper,expected_n_hits",
    [
        ("population", (3812,), (4133,), 1),
        pytest.param("area", (6312,), (50000,), 1, marks=pytest.mark.xfail(reason="?")),
        # ("name", ("alhamn", "Alhamn"), ("bjurvik", "Bjurvik"), 2),
        pytest.param("name", ("b", "B"), ("h", "H"), 1, marks=pytest.mark.xfail),
        pytest.param("name", ("Alhamn",), ("Bjurvik",), 1, marks=pytest.mark.xfail),
        pytest.param("name", ("B",), ("H",), 1, marks=pytest.mark.xfail),
        ("name.raw", ("Alhamn",), ("Bjurvik",), 1),
        pytest.param(
            "name.raw", ("B",), ("H",), 4, marks=pytest.mark.xfail(reason="?")
        ),
    ],
)
def test_and_gt_lt(fa_data_client, field, lower, upper, expected_n_hits):
    query = f"/query/places?q=and(gt|{field}|{lower[0]}||lt|{field}|{upper[0]})"
    print(f"testing query='{query}'")
    _test_against_entries(
        fa_data_client,
        query,
        field,
        lambda x: lower[-1] < x < upper[-1],
        expected_n_hits,
    )


@pytest.mark.xfail(reason="unstable")
@pytest.mark.parametrize(
    "query,expected_n_hits", [("and(gt|name|alhamn||lt|name|bjurvik)", 2)]
)
def test_and_gt_lt_expected_length(fa_data_client, query: str, expected_n_hits: int):
    path = f"/query/places?q={query}"
    _test_path_has_expected_length(fa_data_client, path, expected_n_hits)


@pytest.mark.xfail(reason="unstable")
@pytest.mark.parametrize(
    "field,expected_length",
    [
        ("density", 8),
        # ("|and|density|population", 7),
        # (
        #     "|not|density",
        #     14,
        # ),
        # ("|or|density|population", 8),
        # (
        #     "|or|density|population|v_smaller_places",
        #     17,
        # ),
    ],
)
def test_missing(fa_data_client, field: str, expected_length: int):
    query = f"/query/places?q=missing|{field}"
    _test_path_has_expected_length(fa_data_client, query, expected_length)


@pytest.mark.xfail(reason="unstable")
@pytest.mark.parametrize(
    "queries,expected_length",
    [
        (
            "freetext|botten",
            19,
        ),
        ("freergxp|.*test", 17),
        ("freergxp|.*test||freergxp|.*vik", 14),
    ],
)
def test_not(fa_data_client, queries: str, expected_length: int):
    query = f"/query/places?q=not({queries})"
    _test_path_has_expected_length(fa_data_client, query, expected_length)


@pytest.mark.xfail(reason="unstable")
@pytest.mark.parametrize(
    "queries,expected_result",
    [
        (["equals|population|3122", "equals|population|4132"], ["Hambo", "Grund test"]),
        (
            ["equals|population|3122", "equals|population|4132", "endswith|name|est"],
            ["Hambo", "Grund test", "Botten test"],
        ),
    ],
)
def test_or(fa_data_client, queries: List[str], expected_result: List[str]):
    query = f"/query/places?q=or({'||'.join(queries)})"
    _test_path(fa_data_client, query, expected_result)


@pytest.mark.xfail(reason="unstable")
@pytest.mark.parametrize(
    "field,value,expected_result",
    [
        ("name", "grun.*", ["Grund test", "Grunds"]),
        ("name", "Grun.*", ["Grund test", "Grunds"]),
        ("name", "Grunds?", ["Grunds"]),
        ("name", "grunds?", ["Grund test", "Grunds"]),
        ("name", "Grun.*est", ["Grund test"]),
        # ("name", "|and|grun.*|.*est", ["Grund test"]),
        # ("name", "|or|grun.*|.*est", ["Grund test", "Grunds", "Botten test"]),
        # ("|and|name|v_larger_place.name|", ".*vik", ["Bjurvik"]),
        # ("|or|name|v_larger_place.name|", "al.*n", ["Grund test", "Alhamn"]),
        # ("|not|name|", "Al.*", ["Grund test", "Hambo", "Bjurvik"]),
    ],
)
def test_regexp(fa_data_client, field: str, value, expected_result: List[str]):
    query = f"/query/places?q=regexp|{field}|{value}"
    _test_path(fa_data_client, query, expected_result)


@pytest.mark.xfail(reason="unstable")
@pytest.mark.parametrize(
    "field,value,expected_result",
    [
        ("name", "grun", ["Grund test", "Grunds"]),
        ("name", "Grun", ["Grund test", "Grunds"]),
        ("name", "tes", ["Grund test", "Botten test"]),
        # ("name", "|and|grun|te", ["Grund test"]),
        # ("name", "|or|grun|te", ["Grund test", "Grunds", "Botten test"]),
        # ("|and|name|v_larger_place.name|", "b", ["Botten test"]),
        # ("|and|name|v_larger_place.name|", "B", ["Botten test"]),
        # ("|or|name|v_larger_place.name|", "alh", ["Grund test", "Alhamn"]),
        # ("|not|name|", "Al", ["Grund test", "Hambo", "Bjurvik"]),
    ],
)
def test_startswith(fa_data_client, field: str, value, expected_result: List[str]):
    query = f"/query/places?q=startswith|{field}|{value}"
    _test_path(fa_data_client, query, expected_result)


@pytest.mark.xfail(reason="unstable")
@pytest.mark.parametrize(
    "query_str,expected_length",
    [
        ("contains|name|2", 6),
        pytest.param(
            "contains|name||not|test",
            20,
            marks=pytest.mark.skip(reason="currently not supported"),
        ),
        pytest.param(
            "contains|name||not|test|bo",
            19,
            marks=pytest.mark.skip(reason="currently not supported"),
        ),
        ("endswith|name|2", 1),
        pytest.param(
            "endswith|name||not|vik",
            19,
            marks=pytest.mark.skip(reason="currently not supported"),
        ),
        pytest.param(
            "equals|area||not|6312",
            18,
            marks=pytest.mark.skip(reason="currently not supported"),
        ),
        ("exists|density", 14),
        pytest.param(
            "exists||and|density|population",
            14,
            marks=pytest.mark.skip(reason="currently not supported"),
        ),
        pytest.param(
            "exists||or|density|population",
            15,
            marks=pytest.mark.skip(reason="currently not supported"),
        ),
        pytest.param(
            "exists||not|density",
            8,
            marks=pytest.mark.skip(reason="currently not supported"),
        ),
        pytest.param(
            "freergxp||not|Gr.*",
            19,
            marks=pytest.mark.skip(reason="currently not supported"),
        ),
        pytest.param(
            "freetext||not|botten",
            19,
            marks=pytest.mark.skip(reason="currently not supported"),
        ),
        pytest.param(
            "freetext||not|botten|test",
            17,
            marks=pytest.mark.skip(reason="currently not supported"),
        ),
        pytest.param(
            "regexp|name||not|.*est",
            20,
            marks=pytest.mark.skip(reason="currently not supported"),
        ),
        pytest.param(
            "startswith|name||not|te",
            20,
            marks=pytest.mark.skip(reason="currently not supported"),
        ),
    ],
)
def test_response_has_correct_length(
    fa_data_client, query_str: str, expected_length: int
):
    query = f"/query/places?q={query_str}"
    print(f"testing query='{query}'")
    _test_path_has_expected_length(fa_data_client, query, expected_length)


# @pytest.mark.xfail(reason="no protected stuff")
# def test_protected(client_with_data_scope_module):
#     response = client_with_data_scope_module.get("/municipalities/query")
#     names = response
#     assert "403 FORBIDDEN" in names


@pytest.mark.xfail(reason="unstable")
def test_pagination_explicit_0_5(fa_data_client):
    # client = init_data(client_with_data_f, es, 30)
    resource = "places"
    json_data = get_json(
        fa_data_client,
        f"/query/{resource}?from=0&size=5",
    )
    assert "hits" in json_data
    assert "distribution" in json_data
    print(f"json_data = {json_data}")
    assert len(json_data["hits"]) == 5

    hit_3 = json_data["hits"][3]

    response = fa_data_client.get(
        f"/query/{resource}?from=3&size=5&lexicon_stats=false",
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data
    assert "hits" in json_data
    assert "distribution" not in json_data
    assert len(json_data["hits"]) == 5

    assert json_data["hits"][0]["id"] == hit_3["id"]


# #
# #
# # def test_pagination_default_size(fa_data_client):
# #     client = init_data(client_with_data_f, es, 30)
# #     resource = 'places'
# #     response = client.get('/{}/query?from=0'.format(resource))
# #     assert response.status == '200 OK'
# #     assert response.is_json
# #     json_data = response.get_json()
# #     assert len(json_data['hits']) == 25
# #
# #
# # def test_pagination_default_from(fa_data_client):
# #     client = init_data(client_with_data_f, es, 50)
# #     resource = 'places'
# #     response = client.get('/{}/query?size=45'.format(resource))
# #     assert response.status == '200 OK'
# #     assert response.is_json
# #     json_data = response.get_json()
# #     assert len(json_data['hits']) == 45


@pytest.mark.xfail(reason="unstable")
def test_pagination_fewer(fa_data_client):
    # client = init_data(client_with_data_f, es, 5)
    resource = "places"
    response = fa_data_client.get(
        f"/query/{resource}?from=10",
    )
    assert response.status_code == 200
    json_data = response.json()
    print(f"json_data = {json_data}")
    assert len(json_data["hits"]) == json_data["total"] - 10


# def test_resource_not_existing(fa_data_client):
#     response = fa_data_client.get("/asdf/query")
#     assert response.status_code == 400
#     assert (
#         'Resource is not searchable: "asdf"'
#         == json.loads(response.data.decode())["error"]
#     )


# def init_data(client, es_status_code, no_entries):
#     if es_status_code == "skip":
#         pytest.skip("elasticsearch disabled")
#     client_with_data = client(use_elasticsearch=True)

#     for i in range(0, no_entries):
#         entry = {"code": i, "name": "name", "municipality": [1]}
#         client_with_data.post(
#             "places/add",
#             data=json.dumps({"entry": entry}),
#             content_type="application/json",
#         )
#     return client_with_data


@pytest.mark.xfail(reason="unstable")
@pytest.mark.parametrize("endpoint", ["query", "query/split"])
@pytest.mark.parametrize(
    "query",
    [
        (""),
        ("freetext|eat my shorts"),
    ],
)
def test_distribution_in_result(fa_data_client, query: str, endpoint: str):
    result = get_json(
        fa_data_client,
        f"/{endpoint}/places?{f'q={query}&' if query else ''}lexicon_stats=true",
    )

    assert "distribution" in result


@pytest.mark.xfail(reason="unstable")
@pytest.mark.parametrize("endpoint", ["query"])
def test_sorting(fa_data_client, endpoint: str):
    result = get_json(
        fa_data_client,
        f"/{endpoint}/places?sort=population|desc",
    )

    assert (
        result["hits"][0]["entry"]["population"]
        >= result["hits"][1]["entry"]["population"]
    )


@pytest.mark.xfail(reason="unstable")
@pytest.mark.parametrize("fields", [(["population"])])
def test_query_include_fields(fa_data_client, fields: List[str]) -> None:
    result = get_json(
        fa_data_client,
        f"/query/places?{'&'.join((f'include_field={field}' for field in fields))}",
    )

    for entry in (entry["entry"] for entry in result["hits"]):
        for field in fields:
            assert field in fields
