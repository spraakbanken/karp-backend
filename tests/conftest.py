"""Pytest entry point."""
import pytest

from starlette.config import environ

environ["TESTING"] = "True"
environ["ELASTICSEARCH_HOST"] = "http://localhost:9202"
environ["CONSOLE_LOG_LEVEL"] = "DEBUG"
environ["AUTH_JWT_PUBKEY_PATH"] = "assets/testing/pubkey.pem"

from . import common_data, utils


@pytest.fixture
def json_schema_config():
    return common_data.CONFIG_PLACES
