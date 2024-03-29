"""Alias generators."""


def to_lower_camel(s: str) -> str:
    """Transform snake_case to lowerCamelCase."""

    return "".join(word.capitalize() if i > 0 else word for i, word in enumerate(s.split("_")))
