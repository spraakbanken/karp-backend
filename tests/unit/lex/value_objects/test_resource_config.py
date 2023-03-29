import pytest  # noqa: I001
import pydantic

from karp.lex.domain.value_objects import ResourceConfig


class TestResourceConfig:
    def test_invalid_input_raises(self):  # noqa: ANN201
        with pytest.raises(pydantic.ValidationError):
            ResourceConfig(fields=3)
