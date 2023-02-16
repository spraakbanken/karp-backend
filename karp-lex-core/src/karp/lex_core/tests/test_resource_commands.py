import pytest
from karp.lex_core.commands.resource_commands import EntityOrResourceIdMixin


class TestEntityOrResourceIdMixin:
    def test_given_both_raises_value_error(self):  # noqa: ANN201
        with pytest.raises(ValueError):
            EntityOrResourceIdMixin(
                resourceId="abc",
                entityId="01GSAHD0K063FBMFE19BFDM4E9",
            )

    def test_given_either_raises_value_error(self):  # noqa: ANN201
        with pytest.raises(ValueError):
            EntityOrResourceIdMixin()

    def test_both_given_none_raises_value_error(self):  # noqa: ANN201
        with pytest.raises(ValueError):
            EntityOrResourceIdMixin(
                resourceId=None,
                entityId=None,
            )
