"""Utilities for working with JSON objects."""

from itertools import takewhile
from typing import Dict, Iterator, Union

Path = list[Union[str, int]]


def make_path(path: Union[str, Path]) -> Path:
    """
    Convert a string (e.g. "SOLemman.s_nr") into a path (e.g. ["SOLemman", "s_nr"]).
    """

    if isinstance(path, str):
        if path:
            return path.split(".")
        else:
            return []
    elif isinstance(path, list):
        return path
    else:
        raise AssertionError(f"path of wrong type {type(path)}")


def path_str(path: Union[str, Path]) -> str:
    """
    Convert a path (e.g. ["SOLemman", "s_nr"]) into a string (e.g. "SOLemman.s_nr").
    """

    if isinstance(path, str):
        return path
    elif isinstance(path, list):
        return ".".join(map(str, path))
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
        raise AssertionError(f"can't look up field {path[0]} in non-object {data}")


def set_path(path: Union[str, Path], value, data):
    """
    Set the value at a given path.

    The path must give a list index for any list values along the path.
    """

    path = make_path(path)
    for component in path[:-1]:
        data = data[component]

    data[path[-1]] = value


def del_path(path: Union[str, Path], data):
    """
    Delete the value at a given path.

    The path must give a list index for any list values along the path.
    """

    path = make_path(path)
    for component in path[:-1]:
        data = data[component]

    del data[path[-1]]


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


def all_fields(data) -> Iterator[str]:
    """Generate all possible field names in a JSON object.

    >>> for path in all_fields({"SOLemman": [{"s_nr": 1}, {"s_nr": 2}]}): print(path)
    "SOLemman"
    "SOLemman.s_nr"
    """

    def field_name(path):
        return ".".join(x for x in path if isinstance(x, str))

    return list(dict.fromkeys(field_name(path) for path in all_paths(data) if path))


def expand_path(path: Union[str, Path], data, prefix=None, expand_arrays=True) -> Iterator[Path]:
    """
    Look up a path in a JSON object.
    Instead of returning the values, return the paths to the values.

    >>> doc = {"SOLemman": [{"s_nr": 1}, {"s_nr": 2}]}
    >>> for path in expand_path("SOLemman", doc): print(path)
    ["SOLemman", 0]
    ["SOLemman", 1]
    >>> for path in expand_path("SOLemman.s_nr", doc): print(path)
    ["SOLemman", 0, "s_nr"]
    ["SOLemman", 1, "s_nr"]

    If expand_arrays is False, arrays are not descended into if they are the
    last component of the path:

    >>> for path in expand_path("SOLemman", doc, expand_arrays=False): print(path)
    ["SOLemman"]
    >>> for path in expand_path("SOLemman.s_nr", doc, expand_arrays=False): print(path)
    ["SOLemman", 0, "s_nr"]
    ["SOLemman", 1, "s_nr"]
    """

    if prefix is None:
        prefix = []

    path = make_path(path)

    def should_descend_into_array():
        if not path and expand_arrays:
            return True
        elif path and not isinstance(path[0], int):
            return True
        else:
            return False

    def field_present():
        if isinstance(data, Dict) and path[0] in data:
            return True
        elif isinstance(data, list) and path[0] in range(len(data)):
            return True
        else:
            return False

    if isinstance(data, list) and should_descend_into_array():
        for i, item in enumerate(data):
            yield from expand_path(path, item, prefix + [i], expand_arrays)

    elif not path:
        yield prefix

    elif not field_present():
        # Skip if the field doesn't exist
        pass

    else:
        yield from expand_path(path[1:], data[path[0]], prefix + [path[0]], expand_arrays)


def has_path(path: Union[str, Path], data) -> bool:
    """
    Check if a given path exists.
    """

    try:
        next(expand_path(path, data))
        return True
    except StopIteration:
        return False
