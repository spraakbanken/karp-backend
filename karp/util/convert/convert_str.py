"""Helpers for converting.
"""
from typing import Callable, List


def str2list(delimiter: str = None) -> Callable[[str], List[str]]:
    """Return a function that splits a string using {delimiter} provided

    Keyword Arguments:
        delimiter {str} -- the delimiter to split by, defaults to ' ' (default: {None})

    Returns:
        Callable[[str], List[str]] -- the function to do the spliting.
    """

    def result(string: str) -> List[str]:
        return string.split(delimiter)

    return result
