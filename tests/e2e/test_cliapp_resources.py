from typer.testing import CliRunner

from karp.cliapp.main import create_app
from karp.lex.application import resource_queries

runner = CliRunner()
cliapp = create_app()


def test_help():
    result = runner.invoke(cliapp, ["resource", "--help"])
    assert result.exit_code == 0


def test_create_and_publish_repo():
    result = runner.invoke(
        cliapp,
        [
            "resource",
            "create",
            "assets/testing/config/lexlex.yaml",
        ],
    )

    if isinstance(result.exception, Exception):
        raise result.exception
    else:
        assert result.exit_code == 0

    assert resource_queries.by_resource_id_optional("lexlex") is not None
