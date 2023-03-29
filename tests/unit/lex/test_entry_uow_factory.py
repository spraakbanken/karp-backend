from karp.lex.application import repositories
from karp.lex_core.value_objects import unique_id

from . import adapters


def test_create_fake_entry_repo_uow(  # noqa: ANN201
    lex_ctx: adapters.UnitTestContext,
):
    uow_factory = lex_ctx.container.get(repositories.EntryRepositoryUnitOfWorkFactory)

    entry_repo_uow, _ = uow_factory.create(
        "fake",
        unique_id.make_unique_id(),
        "name",
        {},
        connection_str=None,
        user="kristoff@example.com",
        message="msg",
        timestamp=123456789,
    )

    print(f"entry_repo_uow = {entry_repo_uow}")
    assert isinstance(entry_repo_uow, adapters.InMemoryEntryUnitOfWork)
