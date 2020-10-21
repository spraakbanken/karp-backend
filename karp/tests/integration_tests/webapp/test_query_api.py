from typing import Callable, List, Optional, Tuple, Dict
import json

import pytest  # pyre-ignore

# import time


from karp.tests.common_data import MUNICIPALITIES, PLACES
from karp.tests.utils import get_json, add_entries


@pytest.fixture(scope="module", name="fa_query_data_client")
def fixture_fa_query_data_client(fa_client_w_places_w_municipalities_scope_module):
    add_entries(
        fa_client_w_places_w_municipalities_scope_module,
        {"places": PLACES, "municipalities": MUNICIPALITIES},
    )

    return fa_client_w_places_w_municipalities_scope_module


def extract_names(entries):
    return [entry["entry"]["name"] for entry in entries["hits"]]


def extract_names_set(entries):
    return {entry["entry"]["name"] for entry in entries["hits"]}


def _test_path(
    client, path: str, expected_result: List[str], *, headers: Optional[Dict] = None
):
    if headers is None:
        headers = {"Authorization": "Bearer 1234"}
    entries = get_json(client, path, headers=headers)

    names = extract_names(entries)
    print("names = {names}".format(names=names))

    assert len(names) == len(expected_result)

    for name in names:
        assert name in expected_result

    for expected in expected_result:
        assert expected in names


def _test_against_entries(
    client,
    path: str,
    field: str,
    predicate: Callable,
    expected_n_hits: int = None,
    *,
    headers: Optional[Dict] = None,
):
    if headers is None:
        headers = {"Authorization": "Bearer 1234"}
    entries = get_json(client, path, headers=headers)
    names = extract_names(entries)

    if field.endswith(".raw"):
        field = field[:-4]

    assert len(names) == sum(
        1 for entry in PLACES if field in entry and predicate(entry[field])
    )

    num_names_to_match = len(names)
    for entry in PLACES:
        if field in entry and predicate(entry[field]):
            assert entry["name"] in names
            num_names_to_match -= 1
    assert num_names_to_match == 0

    if expected_n_hits:
        assert len(entries["hits"]) == expected_n_hits


def _test_against_entries_general(
    client,
    path: str,
    fields: Tuple[str],
    predicate: Callable,
    expected_n_hits: int = None,
    *,
    headers: Optional[Dict] = None,
):
    if headers is None:
        headers = {"Authorization": "Bearer 1234"}
    entries = get_json(client, path, headers=headers)
    names = extract_names(entries)

    print("names = {names}".format(names=names))
    for i, field in enumerate(fields):
        if field.endswith(".raw"):
            fields[i] = field[:-4]

    for field in fields:
        print("field = {field}".format(field=field))

    # assert len(names) == sum(1 for entry in PLACES
    #                          if all(field in entry for field in fields) and predicate([entry[field]
    #                          for field in fields]))

    num_names_to_match = len(names)
    for entry in PLACES:
        print("entry = {entry}".format(entry=entry))
        # if all(field in entry for field in fields) and predicate(
        #     [entry[field] for field in fields]
        # ):
        if predicate(entry, fields):
            print("entry '{entry}' satisfied predicate".format(entry=entry))
            assert entry["name"] in names
            num_names_to_match -= 1
    assert num_names_to_match == 0

    if expected_n_hits:
        assert len(entries["hits"]) == expected_n_hits


def test_query_no_q(fa_query_data_client):
    entries = get_json(
        fa_query_data_client, "/query/places", headers={"Authorization": "Bearer 1234"}
    )

    names = extract_names(entries)

    print(f"entries = {entries}")
    assert entries["total"] == len(PLACES)
    assert len(names) == len(PLACES)
    print("names = {}".format(names))

    for entry in PLACES:
        assert entry["name"] in names

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


@pytest.mark.parametrize(
    "queries,expected_result",
    [
        (["equals|population|4133", "equals|area|50000"], ["Botten test"]),
        (["regexp|name|.*bo.*", "equals|area|50000"], ["Hambo", "Botten test"]),
        (["regexp|name|.*bo.*", "equals|area|50000", "missing|density"], ["Hambo"]),
    ],
)
def test_and(fa_query_data_client, queries: List[str], expected_result: List[str]):
    query = "/query/places?q=and||{queries}".format(queries="||".join(queries))
    _test_path(fa_query_data_client, query, expected_result)


@pytest.mark.parametrize(
    "field,value,expected_result",
    [
        ("name", "grund", ["Grund test", "Grunds"]),
        ("name", "Grund", ["Grund test", "Grunds"]),
        ("name", 2, ["Bjurvik2"]),
        ("name.raw", "Grund", ["Grund test", "Grunds"]),
        pytest.param(
            "population",
            3122,
            ["Grund test"],
            marks=pytest.mark.skip(reason="Can't search with regex on LONG fields"),
        ),
        ("|and|name|v_larger_place.name|", "vi", ["Bjurvik"]),
        pytest.param(
            "|and|name|v_smaller_places.name|",
            "and|Al|vi",
            ["Alvik"],
            marks=pytest.mark.xfail(reason="regex can't handle complex"),
        ),
        ("|not|name|", "test", ["Hambo", "Alhamn", "Bjurvik", "Bjurvik2"]),
        ("|or|name|v_smaller_places.name|", "Al", ["Alvik", "Alhamn", "Hambo"]),
        ("name", "|and|un|es", ["Grund test"]),
        (
            "name",
            "|not|test",
            ["Grunds", "Hambo", "Alhamn", "Rutvik", "Alvik", "Bjurvik", "Bjurvik2"],
        ),
        (
            "name",
            "|not|test|bo",
            ["Grunds", "Alhamn", "Rutvik", "Alvik", "Bjurvik", "Bjurvik2"],
        ),
        (
            "name",
            "|or|vi|bo",
            ["Alvik", "Rutvik", "Bjurvik", "Botten test", "Hambo", "Bjurvik2"],
        ),
    ],
)
def test_contains(fa_query_data_client, field: str, value, expected_result: List[str]):
    query = f"/query/places?q=contains|{field}|{value}"
    _test_path(fa_query_data_client, query, expected_result)


@pytest.mark.parametrize(
    "fields,values,expected_result",
    [(("name", "v_larger_place.name"), ("vi", "vi"), ["Bjurvik"])],
)
def test_contains_and_separate_calls(
    fa_query_data_client,
    fields: Tuple,
    values: Tuple,
    expected_result: List[str],
):
    names = set()
    for field, value in zip(fields, values):
        query = f"/query/places?q=contains|{field}|{value}"
        entries = get_json(
            fa_query_data_client, query, headers={"Authorization": "Bearer 1234"}
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


@pytest.mark.parametrize(
    "field,value,expected_result",
    [
        ("name", "est", ["Grund test", "Botten test"]),
        ("name", "unds", ["Grunds"]),
        ("name", "grund", ["Grund test"]),
        ("name", 2, ["Bjurvik2"]),
        pytest.param("population", 3122, ["Grund test"], marks=pytest.mark.skip),
        ("|and|name|v_smaller_places.name|", "vik", ["Alvik"]),
        ("|and|name|v_larger_place.name|", "vik", ["Bjurvik"]),
        pytest.param(
            "|and|name|v_smaller_places.name|",
            "and|Al|vi",
            ["Alvik"],
            marks=pytest.mark.skip(reason="regex can't handle complex"),
        ),
        pytest.param(
            "|not|name|",
            "vik",
            [
                "Botten test",  # through larger_place
                "Alvik",  # through smaller_places
                "Bjurvik",  # through larger_place
            ],
            marks=pytest.mark.xfail(reason="Too restrictive"),
        ),
        ("|or|name|v_smaller_places.name|", "otten", ["Botten test", "Bjurvik"]),
        ("name", "|and|und|est", ["Grund test"]),
        (
            "name",
            "|not|vik",
            ["Grund test", "Grunds", "Botten test", "Hambo", "Alhamn", "Bjurvik2"],
        ),
        ("name", "|or|vik|bo", ["Alvik", "Rutvik", "Bjurvik", "Hambo"]),
    ],
)
def test_endswith(fa_query_data_client, field: str, value, expected_result: List[str]):
    query = f"/query/places?q=endswith|{field}|{value}"
    _test_path(fa_query_data_client, query, expected_result)


@pytest.mark.parametrize(
    "field,value,expected_result",
    [
        ("name", "grunds", ["Grunds"]),
        ("name", "Grunds", ["Grunds"]),
        ("name", "Grund test", ["Grund test"]),
        ("name.raw", "Grund test", ["Grund test"]),
        ("name", "|and|grund|test", ["Grund test"]),
        ("density", 7, ["Botten test"]),
        ("|and|population|area|", 6312, ["Alvik"]),
        pytest.param(
            "|and|area||or|population|density|",
            6312,
            ["Alvik", "Grund test"],
            marks=pytest.mark.xfail(reason="Current query dsl can't handle this."),
        ),
        pytest.param(
            "|not|area|",
            6312,
            ["Alvik", "Grunds"],
            marks=pytest.mark.xfail(reason="Too restrictive."),
        ),
        (
            "|or|population|area|",
            6312,
            ["Alhamn", "Alvik", "Bjurvik", "Grund test", "Grunds"],
        ),
        ("name", "|and|botten|test", ["Botten test"]),
        ("area", "|not|6312", ["Grunds", "Botten test", "Hambo", "Rutvik", "Bjurvik2"]),
        ("population", "|or|6312|3122", ["Alvik", "Grund test", "Grunds"]),
    ],
)
def test_equals(fa_query_data_client, field: str, value, expected_result: List[str]):
    query = f"/query/places?q=equals|{field}|{value}"
    _test_path(fa_query_data_client, query, expected_result)


@pytest.mark.parametrize(
    "field,expected_result",
    [
        (
            "density",
            [
                "Bjurvik",
                "Bjurvik2",
                "Grund test",
                "Grunds",
                "Botten test",
                "Alvik",
                "Alhamn",
            ],
        ),
        (
            "|and|density|population",
            [
                "Bjurvik",
                "Bjurvik2",
                "Grund test",
                "Grunds",
                "Botten test",
                "Alvik",
                "Alhamn",
            ],
        ),
        (
            "|and|v_larger_place|v_smaller_places",
            ["Bjurvik", "Hambo", "Botten test", "Alhamn", "Grund test"],
        ),
        (
            "|or|density|population",
            [
                "Bjurvik",
                "Bjurvik2",
                "Grund test",
                "Grunds",
                "Hambo",
                "Botten test",
                "Alvik",
                "Alhamn",
            ],
        ),
        ("|not|density", ["Hambo", "Rutvik"]),
    ],
)
def test_exists(fa_query_data_client, field: str, expected_result: List[str]):
    query = f"/query/places?q=exists|{field}"
    _test_path(fa_query_data_client, query, expected_result)


@pytest.mark.parametrize(
    "field,expected_result",
    [
        (
            "|and|.*test|Gr.*",
            [
                "Grund test",
                "Alhamn",  # through smaller_places
                "Bjurvik2",  # through larger_place
            ],
        ),
        ("|not|Gr.*", ["Botten test", "Hambo", "Alvik", "Rutvik", "Bjurvik"]),
        (
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
        ),
        ("Grunds?", ["Grund test", "Grunds", "Bjurvik2", "Alhamn"]),
    ],
)
def test_freergxp(fa_query_data_client, field: str, expected_result: List[str]):
    query = f"/query/places?q=freergxp|{field}"
    _test_path(fa_query_data_client, query, expected_result)


@pytest.mark.parametrize(
    "field,expected_result",
    [
        (
            "grund",
            [
                "Grund test",
                "Grunds",
                "Alhamn",  # through smaller_places
                "Bjurvik2",  # through larger_place
            ],
        ),
        ("3122", ["Grund test"]),
        (3122, ["Grund test"]),
        (
            "|and|botten|test",
            [
                "Botten test",
                "Hambo",  # through larger_place
                "Bjurvik",  # through smaller_places
            ],
        ),
        (
            "|not|botten",
            ["Grund test", "Grunds", "Alhamn", "Rutvik", "Alvik", "Bjurvik2"],
        ),
        ("|not|botten|test", ["Grunds", "Rutvik", "Alvik"]),
        (
            "|or|botten|test",
            [
                "Botten test",
                "Hambo",  # through smaller_places
                "Grund test",
                "Alhamn",  # through smaller_places
                "Bjurvik",  # through smaller_places
                "Bjurvik2",  # through larger_places
            ],
        ),
    ],
)
def test_freetext(fa_query_data_client, field: str, expected_result: List[str]):
    query = f"/query/places?q=freetext|{field}"
    _test_path(fa_query_data_client, query, expected_result)


@pytest.mark.parametrize(
    "field,value",
    [
        ("population", (4132,)),
        ("area", (20000,)),
        ("name", ("alvik", "Alvik")),
        pytest.param(
            "name",
            ("Alvik",),
            marks=pytest.mark.skip(
                reason="'name' is lower case, so greater than Uppercase returns all."
            ),
        ),
        pytest.param(
            "name",
            ("B",),
            marks=pytest.mark.skip(
                reason="'name' is lower case, so greater than Uppercase returns all."
            ),
        ),
        ("name.raw", ("Alvik",)),
        ("name.raw", ("B",)),
        pytest.param(
            "name",
            ("r", "R"),
            marks=pytest.mark.xfail(
                reason="'name' is tokenized, so greater than matches second word."
            ),
        ),
        pytest.param(
            "name",
            ("R",),
            marks=pytest.mark.xfail(
                reason="'name' is lower case, so greater than Uppercase returns all."
            ),
        ),
        ("name.raw", ("r",)),
        ("name.raw", ("R",)),
    ],
)
def test_gt(fa_query_data_client, field, value):
    query = f"/query/places?q=gt|{field}|{value[0]}"
    _test_against_entries(fa_query_data_client, query, field, lambda x: value[-1] < x)


@pytest.mark.parametrize(
    "field,value",
    [
        ("population", (4132,)),
        ("area", (20000,)),
        ("name", ("alvik", "Alvik")),
        pytest.param(
            "name",
            ("Alvik",),
            marks=pytest.mark.skip(
                reason="'name' is lower case, so greater than Uppercase returns all."
            ),
        ),
        pytest.param(
            "name",
            ("B",),
            marks=pytest.mark.skip(
                reason="'name' is lower case, so greater than Uppercase returns all."
            ),
        ),
        ("name.raw", ("Alvik",)),
        ("name.raw", ("B",)),
    ],
)
def test_gte(fa_query_data_client, field, value):
    query = f"/query/places?q=gte|{field}|{value[0]}"
    _test_against_entries(fa_query_data_client, query, field, lambda x: value[-1] <= x)


@pytest.mark.parametrize(
    "field,value",
    [
        ("population", (4132,)),
        ("area", (20000,)),
        ("name", ("alvik", "Alvik")),
        pytest.param(
            "name",
            ("Alvik",),
            marks=pytest.mark.skip(
                reason="'name' is lower case, so lesser than Uppercase returns all."
            ),
        ),
        pytest.param(
            "name",
            ("B",),
            marks=pytest.mark.skip(
                reason="'name' is lower case, so lesser than Uppercase returns all."
            ),
        ),
        ("name.raw", ("Alvik",)),
        ("name.raw", ("B",)),
    ],
)
def test_lt(fa_query_data_client, field, value):
    query = f"/query/places?q=lt|{field}|{value[0]}"
    _test_against_entries(fa_query_data_client, query, field, lambda x: x < value[-1])


@pytest.mark.parametrize(
    "field,value",
    [
        ("population", (4132,)),
        ("area", (20000,)),
        ("name", ("alvik", "Alvik")),
        pytest.param(
            "name",
            ("Alvik",),
            marks=pytest.mark.skip(
                reason="'name' is lower case, so lesser than Uppercase returns all."
            ),
        ),
        pytest.param(
            "name",
            ("B",),
            marks=pytest.mark.skip(
                reason="'name' is lower case, so lesser than Uppercase returns all."
            ),
        ),
        ("name.raw", ("Alvik",)),
        ("name.raw", ("B",)),
    ],
)
def test_lte(fa_query_data_client, field, value):
    query = f"/query/places?q=lte|{field}|{value[0]}"
    _test_against_entries(fa_query_data_client, query, field, lambda x: x <= value[-1])


@pytest.mark.parametrize(
    "op,fields,value,expected_result",
    [
        ("gt", ("population", "area"), (6212,), None),
        (
            "gt",
            ("name", "v_smaller_places.name"),
            ("bjurvik",),
            ["Botten test", "Grund test"],
        ),
        ("gte", ("population", "area"), (6212,), None),
        (
            "gte",
            ("name", "v_smaller_places.name"),
            ("bjurvik",),
            ["Botten test", "Bjurvik", "Grund test"],
        ),
        ("lt", ("population", "area"), (6313,), None),
        ("lt", ("name", "v_smaller_places.name"), ("c",), ["Alvik", "Bjurvik"]),
        ("lte", ("population", "area"), (6312,), None),
        ("lte", ("name", "v_smaller_places.name"), ("bjurvik",), ["Alvik"]),
    ],
)
def test_binary_range_1st_arg_and(
    fa_query_data_client,
    op: str,
    fields: Tuple,
    value: Tuple,
    expected_result: List[str],
):
    query = f"/query/places?q={op}||and|{fields[0]}|{fields[1]}||{value[0]}"
    if not expected_result:
        if op == "gt":
            _test_against_entries_general(
                fa_query_data_client,
                query,
                fields,
                lambda entry, fields: all(
                    f in entry and value[-1] < entry[f] for f in fields
                ),
            )
        elif op == "gte":
            _test_against_entries_general(
                fa_query_data_client,
                query,
                fields,
                lambda entry, fields: all(
                    f in entry and value[-1] <= entry[f] for f in fields
                ),
            )
        elif op == "lt":
            _test_against_entries_general(
                fa_query_data_client,
                query,
                fields,
                lambda entry, fields: all(
                    f in entry and entry[f] < value[-1] for f in fields
                ),
            )
        elif op == "lte":
            _test_against_entries_general(
                fa_query_data_client,
                query,
                fields,
                lambda entry, fields: all(
                    f in entry and entry[f] <= value[-1] for f in fields
                ),
            )
        else:
            pytest.fail(msg="Unknown range operator '{op}'".format(op=op))
        # _test_against_entries_general(
        #     fa_query_data_client,
        #     query,
        #     fields,
        #     predicate)
    else:
        _test_path(fa_query_data_client, query, expected_result)


@pytest.mark.parametrize(
    "op,fields,value,expected_result",
    [
        ("gt", ("population", "area"), (6212,), None),
        (
            "gt",
            ("name", "v_smaller_places.name"),
            ("bjurvik",),
            [
                "Botten test",
                "Grund test",
                "Grunds",
                "Rutvik",
                "Alhamn",
                "Hambo",
                "Bjurvik",
                "Bjurvik2",
            ],
        ),
        ("gte", ("population", "area"), (6212,), None),
        (
            "gte",
            ("name", "v_smaller_places.name"),
            ("bjurvik",),
            [
                "Bjurvik",
                "Botten test",
                "Grund test",
                "Grunds",
                "Rutvik",
                "Alhamn",
                "Hambo",
                "Alvik",
                "Bjurvik2",
            ],
        ),
        ("lt", ("population", "area"), (6212,), None),
        (
            "lt",
            ("name", "v_smaller_places.name"),
            ("bjurvik",),
            ["Hambo", "Alvik", "Alhamn"],
        ),
        ("lte", ("population", "area"), (6212,), None),
        (
            "lte",
            ("name", "v_smaller_places.name"),
            ("bjurvik",),
            ["Hambo", "Alvik", "Alhamn", "Bjurvik"],
        ),
    ],
)
def test_binary_range_1st_arg_or(
    fa_query_data_client,
    op: str,
    fields: Tuple,
    value: Tuple,
    expected_result: List[str],
):
    query = f"/query/places?q={op}||or|{fields[0]}|{fields[1]}||{value[0]}"
    if not expected_result:
        if op == "gt":
            _test_against_entries_general(
                fa_query_data_client,
                query,
                fields,
                lambda entry, fields: any(
                    f not in entry or value[-1] < entry[f] for f in fields
                ),
            )
        elif op == "gte":
            _test_against_entries_general(
                fa_query_data_client,
                query,
                fields,
                lambda entry, fields: any(
                    f not in entry or value[-1] <= entry[f] for f in fields
                ),
            )
        elif op == "lt":
            _test_against_entries_general(
                fa_query_data_client,
                query,
                fields,
                lambda entry, fields: any(
                    f in entry and entry[f] < value[-1] for f in fields
                ),
            )
        elif op == "lte":
            _test_against_entries_general(
                fa_query_data_client,
                query,
                fields,
                lambda entry, fields: any(
                    f in entry and entry[f] <= value[-1] for f in fields
                ),
            )
        else:
            pytest.fail(msg=f"Unknown range operator '{op}'")
        # _test_against_entries_general(
        #     fa_query_data_client,
        #     query,
        #     fields,
        #     predicate)
    else:
        _test_path(fa_query_data_client, query, expected_result)


@pytest.mark.parametrize(
    "field,lower,upper,expected_n_hits",
    [
        ("population", (3812,), (4133,), 1),
        ("area", (6312,), (50000,), 2),
        ("name", ("alhamn", "Alhamn"), ("bjurvik", "Bjurvik"), 1),
        pytest.param("name", ("b", "B"), ("h", "H"), 1, marks=pytest.mark.xfail),
        pytest.param("name", ("Alhamn",), ("Bjurvik",), 1, marks=pytest.mark.xfail),
        pytest.param("name", ("B",), ("H",), 1, marks=pytest.mark.xfail),
        ("name.raw", ("Alhamn",), ("Bjurvik",), 1),
        ("name.raw", ("B",), ("H",), 5),
    ],
)
def test_and_gt_lt(fa_query_data_client, field, lower, upper, expected_n_hits):
    query = f"/query/places?q=and||gt|{field}|{lower[0]}||lt|{field}|{upper[0]}"
    _test_against_entries(
        fa_query_data_client,
        query,
        field,
        lambda x: lower[-1] < x < upper[-1],
        expected_n_hits,
    )


@pytest.mark.parametrize(
    "field,expected_result",
    [
        ("density", ["Hambo", "Rutvik"]),
        ("|and|density|population", ["Rutvik"]),
        (
            "|not|density",
            [
                "Grund test",
                "Grunds",
                "Botten test",
                "Alvik",
                "Alhamn",
                "Bjurvik",
                "Bjurvik2",
            ],
        ),
        ("|or|density|population", ["Rutvik", "Hambo"]),
        (
            "|or|density|population|v_smaller_places",
            ["Rutvik", "Grunds", "Hambo", "Bjurvik2"],
        ),
    ],
)
def test_missing(fa_query_data_client, field: str, expected_result: List[str]):
    query = f"/query/places?q=missing|{field}"
    _test_path(fa_query_data_client, query, expected_result)


@pytest.mark.parametrize(
    "queries,expected_result",
    [
        (
            "freetext|botten",
            ["Grund test", "Grunds", "Rutvik", "Alvik", "Bjurvik2", "Alhamn"],
        ),
        ("freergxp|.*test", ["Grunds", "Rutvik", "Alvik"]),
        ("freergxp|.*test||freergxp|.*vik", ["Grunds"]),
    ],
)
def test_not(fa_query_data_client, queries: str, expected_result: List[str]):
    query = f"/query/places?q=not||{queries}"
    _test_path(fa_query_data_client, query, expected_result)


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
def test_or(fa_query_data_client, queries: List[str], expected_result: List[str]):
    query = f"/query/places?q=or||{'||'.join(queries)}"
    _test_path(fa_query_data_client, query, expected_result)


@pytest.mark.parametrize(
    "field,value,expected_result",
    [
        ("name", "grun.*", ["Grund test", "Grunds"]),
        ("name", "Grun.*", ["Grund test", "Grunds"]),
        ("name", "Grunds?", ["Grunds"]),
        ("name", "grunds?", ["Grund test", "Grunds"]),
        ("name", "Grun.*est", ["Grund test"]),
        ("name", "|and|grun.*|.*est", ["Grund test"]),
        ("name", "|or|grun.*|.*est", ["Grund test", "Grunds", "Botten test"]),
        (
            "name",
            "|not|.*est",
            ["Grunds", "Hambo", "Rutvik", "Alvik", "Alhamn", "Bjurvik", "Bjurvik2"],
        ),
        ("|and|name|v_larger_place.name|", ".*vik", ["Bjurvik"]),
        ("|or|name|v_larger_place.name|", "al.*n", ["Grund test", "Alhamn"]),
        ("|not|name|", "Al.*", ["Grund test", "Hambo", "Bjurvik"]),
    ],
)
def test_regexp(fa_query_data_client, field: str, value, expected_result: List[str]):
    query = f"/query/places?q=regexp|{field}|{value}"
    _test_path(fa_query_data_client, query, expected_result)


@pytest.mark.parametrize(
    "field,value,expected_result",
    [
        ("name", "grun", ["Grund test", "Grunds"]),
        ("name", "Grun", ["Grund test", "Grunds"]),
        ("name", "tes", ["Grund test", "Botten test"]),
        ("name", "|and|grun|te", ["Grund test"]),
        ("name", "|or|grun|te", ["Grund test", "Grunds", "Botten test"]),
        (
            "name",
            "|not|te",
            ["Grunds", "Hambo", "Rutvik", "Alvik", "Alhamn", "Bjurvik", "Bjurvik2"],
        ),
        ("|and|name|v_larger_place.name|", "b", ["Botten test"]),
        ("|and|name|v_larger_place.name|", "B", ["Botten test"]),
        ("|or|name|v_larger_place.name|", "alh", ["Grund test", "Alhamn"]),
        ("|not|name|", "Al", ["Grund test", "Hambo", "Bjurvik"]),
    ],
)
def test_startswith(
    fa_query_data_client, field: str, value, expected_result: List[str]
):
    query = f"/query/places?q=startswith|{field}|{value}"
    _test_path(fa_query_data_client, query, expected_result)


# @pytest.mark.xfail(reason="no protected stuff")
# def test_protected(client_with_data_scope_module):
#     response = client_with_data_scope_module.get("/municipalities/query")
#     names = response
#     assert "403 FORBIDDEN" in names


def test_pagination_explicit_0_5(fa_query_data_client):
    # client = init_data(client_with_data_f, es, 30)
    resource = "places"
    json_data = get_json(
        fa_query_data_client,
        f"/query/{resource}?from=0&size=5",
        headers={"Authorization": "Bearer 1234"},
    )
    assert "hits" in json_data
    assert "distribution" in json_data
    assert len(json_data["hits"]) == 5

    hit_3 = json_data["hits"][3]

    response = fa_query_data_client.get(
        f"/query/{resource}?from=3&size=5&lexicon_stats=false",
        headers={"Authorization": "Bearer 1234"},
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
# # def test_pagination_default_size(fa_query_data_client):
# #     client = init_data(client_with_data_f, es, 30)
# #     resource = 'places'
# #     response = client.get('/{}/query?from=0'.format(resource))
# #     assert response.status == '200 OK'
# #     assert response.is_json
# #     json_data = response.get_json()
# #     assert len(json_data['hits']) == 25
# #
# #
# # def test_pagination_default_from(fa_query_data_client):
# #     client = init_data(client_with_data_f, es, 50)
# #     resource = 'places'
# #     response = client.get('/{}/query?size=45'.format(resource))
# #     assert response.status == '200 OK'
# #     assert response.is_json
# #     json_data = response.get_json()
# #     assert len(json_data['hits']) == 45


def test_pagination_fewer(fa_query_data_client):
    # client = init_data(client_with_data_f, es, 5)
    resource = "places"
    response = fa_query_data_client.get(
        f"/query/{resource}?from=10", headers={"Authorization": "Bearer 1234"}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert len(json_data["hits"]) == 0


# def test_resource_not_existing(fa_query_data_client):
#     response = fa_query_data_client.get("/asdf/query")
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
