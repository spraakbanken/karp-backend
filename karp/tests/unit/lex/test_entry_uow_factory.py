from karp.lex.application import repositories
from karp.lex.domain.value_objects import unique_id
from . import adapters


def test_create_fake_entry_repo_uow(
    lex_ctx: adapters.UnitTestContext,
):
    uow_factory = lex_ctx.container.get(
        repositories.EntryRepositoryUnitOfWorkFactory)

    entry_repo_uow = uow_factory.create(
        "fake", unique_id.make_unique_id(), "name", {})

    print(f"entry_repo_uow = {entry_repo_uow}")
    assert isinstance(entry_repo_uow, adapters.FakeEntryUnitOfWork)


def test_create_fake_entry_repo_uow2(
    lex_ctx: adapters.UnitTestContext,
):
    uow_factory = lex_ctx.container.get(
        repositories.EntryRepositoryUnitOfWorkFactory)

    entry_repo_uow = uow_factory.create(
        "fake2", unique_id.make_unique_id(), "name", {})

    print(f"entry_repo_uow = {entry_repo_uow}")
    assert isinstance(entry_repo_uow, adapters.FakeEntryUnitOfWork2)
