import pytest
import pydantic

from karp.lex.domain.value_objects import ResourceConfig


class TestResourceConfig:
    def test_invalid_input_raises(self):
        with pytest.raises(pydantic.ValidationError):
            ResourceConfig(fields=3)
