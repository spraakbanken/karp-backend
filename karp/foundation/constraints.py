"""Constraints."""


class ConstraintsError(ValueError):
    """Raised when a constraint is not met."""

    pass


def length_ge(attribute, value, limit: int):  # noqa: ANN201, D103
    if len(value) < limit:
        raise ConstraintsError(
            f"'{attribute}' has to have a length of at least {limit}. Got {attribute}='{value}'"
        )
    return value


def no_space_in_str(s: str) -> str:  # noqa: D103
    if " " in s:
        raise ConstraintsError("whitespace not allowed")
    return s
