from karp.application import context
from pathlib import Path
from typer.testing import CliRunner

import pytest

from karp.cliapp.main import create_app

from karp.infrastructure.unit_of_work import unit_of_work

from karp.application import ctx

runner = CliRunner()


@pytest.fixture(name="cliapp")
def fixture_cliapp(context):
    cliapp = create_app()
    yield cliapp


def test_resource_lifecycle(cliapp):
    result = runner.invoke(
        cliapp, ["resource", "create", "karp/tests/data/config/places.json"]
    )
    print(result.stdout)
    assert result.exit_code == 0

    with unit_of_work(using=ctx.resource_repo) as uw:
        assert "places" in uw.resource_ids()

    result = runner.invoke(cliapp, ["resource", "list"])

    assert result.exit_code == 0
    assert "No resources published." in result.stdout

    result = runner.invoke(cliapp, ["resource", "publish", "places"])

    print(result.stdout)

    assert result.exit_code == 0
    assert "Resource 'places' is published" in result.stdout

    result = runner.invoke(cliapp, ["resource", "list"])

    assert result.exit_code == 0
    assert "places" in result.stdout
