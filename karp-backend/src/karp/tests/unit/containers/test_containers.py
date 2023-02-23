from typing import Any

import pytest
from karp.containers import dict_get


class TestDictGet:
    @pytest.mark.parametrize(
        "d, field, expected",
        [
            ({}, "a", None),
            ({"a": "hi"}, "a", "hi"),
            ({"a": {}}, "a.b", None),
            ({"a": {"b": "hi"}}, "a.b", "hi"),
        ],
    )
    def test_getting_expected(self, d: dict[str, Any], field: str, expected) -> None:
        assert dict_get(d, field) == expected

    @pytest.mark.parametrize(
        "d, field",
        [
            ({"a": "hi"}, "a.b"),
        ],
    )
    def test_getting_raises_value_error(
        self,
        d: dict,
        field: str,
    ) -> None:
        with pytest.raises(ValueError):
            dict_get(d, field)
