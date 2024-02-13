"""Pytest entry point."""
import pytest  # noqa: I001

from starlette.config import environ

environ["TESTING"] = "True"
environ["ELASTICSEARCH_HOST"] = "http://localhost:9202"
environ["CONSOLE_LOG_LEVEL"] = "DEBUG"

from . import common_data, utils  # nopep8  # noqa: E402, F401


@pytest.fixture
def json_schema_config():  # noqa: ANN201
    return common_data.CONFIG_PLACES
