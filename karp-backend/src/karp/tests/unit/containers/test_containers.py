from typing import Any

import pytest
from karp.containers import container_get


class TestContainerGet:
    @pytest.mark.parametrize(
        "d, field, expected",
        [
            ({}, "a", None),
            ({"a": "hi"}, "a", "hi"),
            ({"a": {}}, "a.b", None),
            ({"a": {"b": "hi"}}, "a.b", "hi"),
        ],
    )
    def test_getting_expected(self, d: dict, field: str, expected: Any) -> None:
        assert container_get(d, field) == expected

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
            container_get(d, field)
