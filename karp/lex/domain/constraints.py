"""Constraints."""
from karp.foundation import constraints
from karp.lex.domain import errors


def valid_resource_id(name: str):
    try:
        name = constraints.length_ge("resource_id", name, 2)
        return constraints.no_space_in_str(name)
    except constraints.ConstraintsError as err:
        raise errors.InvalidResourceId(str(err)) from err
