"""Constraints."""
from karp.domain.errors import ConstraintsError


def length_gt_zero(attribute, value):
    if len(value) == 0:
        raise ConstraintsError(
            f"'{attribute}' has to be non-empty. Got {attribute}='{value}'"
        )
    return value


def valid_resource_id(name: str):
    return length_gt_zero("resource_id", name)
