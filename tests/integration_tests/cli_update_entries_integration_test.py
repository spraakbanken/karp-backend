from karp import cli


def test_entries_group_exist(cli_scope_session, es):
    cli_runner = cli_scope_session(use_elasticsearch=True)
    result = cli_runner.invoke(cli.cli, ["entries", "--help"])
    assert result.exit_code == 0


def test_entries_import_exist(cli_scope_session, es):
    cli_runner = cli_scope_session(use_elasticsearch=True)
    result = cli_runner.invoke(cli.cli, ["entries", "import", "--help"])
    assert result.exit_code == 0


def test_entries_update_exist(cli_scope_session, es):
    cli_runner = cli_scope_session(use_elasticsearch=True)
    result = cli_runner.invoke(cli.cli, ["entries", "update", "--help"])
    assert result.exit_code == 0


def test_entries_delete_exist(cli_scope_session, es):
    cli_runner = cli_scope_session(use_elasticsearch=True)
    result = cli_runner.invoke(cli.cli, ["entries", "delete", "--help"])
    assert result.exit_code == 0
