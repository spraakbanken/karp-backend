"""Utilities for working with JSON objects."""

from itertools import takewhile
from typing import Dict, Iterator, Tuple, Union

Path = list[Union[str, int]]


def make_path(path: Union[str, Path]) -> Path:
    """
    Convert a string (e.g. "SOLemman.s_nr") into a path (e.g. ["SOLemman", "s_nr"]).
    """

    if isinstance(path, str):
        return path.split(".")
    elif isinstance(path, list):
        return path
    else:
        raise AssertionError(f"path of wrong type {type(path)}")


def get_path(path: Union[str, Path], data):
    """
    Look up a path in a JSON object, returning the value stored at that path.

    The path can either be a string (e.g. "SOLemman.s_nr") or a list of
    components (e.g. ["SOLemman", "s_nr"]).

    When the JSON contains a list field, the path can say what list index to look at:

    >>> get_path(["SOLemman", 0, "s_nr"], data)
    # returns data["SOLemman"][0]["s_nr"]
    # note that data["SOLemman"] is a list of objects

    If the path doesn't include a list index, get_path searches all members of
    the list, returning a list of results:

    >>> get_path("SOLemman.s_nr", data)
    # returns [lemma["s_nr"] for lemma in data["SOLemman"]]

    If multiple components of the path are lists, the result is a nested list:

    >>> get_path("SOLemman.lexem.kc_nr", data)
    # returns [[lexem["kc_nr"] for lexem in lemma] for lemma in data["SOLemman"]]
    """

    path = make_path(path)

    if not path:
        return data

    if isinstance(data, list):
        # Does the path specify what list index to read?
        if isinstance(path[0], int):
            return get_path(path[1:], data[path[0]])
        else:
            return [get_path(path, x) for x in data]

    elif isinstance(data, dict):
        return get_path(path[1:], data[path[0]])

    else:
        raise AssertionError(f"can't look up field {field[0]} in non-object {data}")


def set_path(path: Union[str, Path], value, data):
    """
    Set the value at a given path.

    The path must give a list index for any list values along the path.
    """

    path = make_path(path)
    for component in path[:-1]:
        data = data[component]

    data[path[-1]] = value


def localise_path(path1, path2: Union[str, Path]) -> Path:
    """
    Paths can (but do not have to) specify what index to read when encountering
    a list of objects:

    >>> get_path(["SOLemman", 0, "s_nr"], data) # SOLemman[0].s_nr
    >>> get_path(["SOLemman", "s_nr"], data)    # SOLemman[i].s_nr for all i

    The localise_path function adds list indexes to a path, by copying them
    from a second path that includes the positions:

    >>> localise_path("SOLemman.s_nr", ["SOLemman", 0])
    ["SOLemman", 0, "s_nr"]

    The positions are copied only as long as the paths match:

    >>> localise_path("SOLemman.uttal.visas", ["SOLemman", 0, "lexem", 1])
    ["SOLemman", 0, "uttal", "visas"] # not [..., "uttal", 1, "visas"]

    This function is intended for doing relative lookups when we are processing
    some part of the JSON object. For example, if we are currently processing
    SOLemman[0], we might like SOLemman.s_nr to resolve to just SOLemman[0].s_nr,
    rather than the list of s_nr values for all SOLemman objects.
    """

    path1 = path_fields(make_path(path1))
    path2 = path_fields(make_path(path2))
    result = []

    while path1 and path2:
        field1, args1 = path1[0]
        field2, args2 = path2[0]

        # Keep on following path2 as long as it matches path1
        if field1 == field2 and args2[: len(args1)] == args1:
            result.append(field2)
            result.extend(args2)
            path1 = path1[1:]
            path2 = path2[1:]
        else:
            break

    # Follow the rest of path1
    for field1, args1 in path1:
        result.append(field1)
        result.extend(args1)

    return result


def path_fields(path: Union[str, Path]) -> list[tuple[str, list[int]]]:
    """
    Convert a path into a list of (field name, list indexes) tuples.
    Helper for localise_path.

    >>> path_fields(["SOLemman", 0, "s_nr"])
    [("SOLemman", [0]), ("s_nr", [])]
    """

    path = make_path(path)
    result = []

    while path:
        field = path[0]
        if not isinstance(field, str):
            raise AssertionError(f"leading path component of wrong type {type(field)}")

        args = list(takewhile(lambda x: isinstance(x, int), path[1:]))
        path = path[len(args) + 1 :]
        result.append((field, args))

    return result


def all_paths(data) -> Iterator[Path]:
    """Generate all possible paths in a JSON object.

    >>> for path in all_paths({"SOLemman": [{"s_nr": 1}, {"s_nr": 2}]}): print(path)
    []
    ["SOLemman"]
    ["SOLemman", 0]
    ["SOLemman", 0, "s_nr"]
    ["SOLemman", 1]
    ["SOLemman", 1, "s_nr"]
    """

    yield []

    if isinstance(data, dict):
        for name, value in data.items():
            for path in all_paths(value):
                yield [name] + path

    if isinstance(data, list):
        for i, value in enumerate(data):
            for path in all_paths(value):
                yield [i] + path


def expand_path(path: Union[str, Path], data, prefix=None) -> Iterator[Path]:
    """
    Look up a path in a JSON object.
    Instead of returning the values, return the paths to the values.

    >>> doc = {"SOLemman": [{"s_nr": 1}, {"s_nr": 2}]}
    >>> for path in matching_paths("SOLemman", doc): print(path)
    ["SOLemman", 0]
    ["SOLemman", 1]
    >>> for path in matching_paths("SOLemman.s_nr", doc): print(path)
    ["SOLemman", 0, "s_nr"]
    ["SOLemman", 1, "s_nr"]
    """

    if prefix is None:
        prefix = []

    path = make_path(path)

    if isinstance(data, list) and (not path or not isinstance(path[0], int)):
        for i, item in enumerate(data):
            yield from expand_path(path, item, prefix + [i])

    elif not path:
        yield prefix

    elif isinstance(data, Dict) and path[0] not in data:
        # Skip if the field doesn't exist
        pass

    else:
        yield from expand_path(path[1:], data[path[0]], prefix + [path[0]])


def has_path(path: Union[str, Path], data) -> bool:
    """
    Check if a given path exists.
    """

    try:
        next(expand_path(path, data))
        return True
    except StopIteration:
        return False
