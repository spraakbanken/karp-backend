import pytest

from karp.domain.models.entry import (
    create_entry,
    Entry,
    # EntryRepository,
)
from karp.domain import repository

# from karp.infrastructure.unit_of_work import unit_of_work
from karp.infrastructure.sql.sql_entry_repository import SqlEntryRepository
from karp.utility import unique_id


@pytest.fixture(name="entry_repo")
def fixture_entry_repo(sqlite_session_factory):
    # entry_repo = EntryRepository.create(
    #     "sql_v1", {"table_name": "test_name", "config": {}}
    # )
    # assert isinstance(entry_repo, SqlEntryRepository)
    session = sqlite_session_factory()
    entry_repo = SqlEntryRepository.from_dict(
        settings={"table_name": "test_name", "resource_id": "test_name"},
        resource_config={},
        session=session,
    )
    assert entry_repo.type == "sql_v1"
    yield entry_repo

    entry_repo.teardown()


@pytest.fixture(name="entry_repo2")
def fixture_entry_repo2(sqlite_session_factory):
    session = sqlite_session_factory()
    entry_repo = repository.EntryRepository.create(
        None,
        settings={
            "table_name": "test_name2",
            "resource_id": "test_name2",
        },
        resource_config={},
        session=session,
    )
    assert isinstance(entry_repo, SqlEntryRepository)
    assert entry_repo.type == "sql_v1"
    yield entry_repo

    entry_repo.teardown()


def test_create_entry_repository(entry_repo):
    assert entry_repo.entry_ids() == []


def test_put_entry_to_entry_repo(entry_repo):
    entity_id = unique_id.make_unique_id()
    entry_id = "a"
    entry = create_entry(
        body={}, entry_id=entry_id, entity_id=entity_id, resource_id="test_name"
    )
    entry_repo.put(entry)

    assert entry_repo.by_id(entity_id).entry_id == entry_id
    assert entry_repo.by_entry_id(entry_id).id == entity_id


#         uw.commit()

#         assert uw.entry_ids() == ["a"]

#         entry_copy = uw.by_id(entry.id)

#         assert entry_copy.id == entry.id

#         entry_copy_from_str = uw.by_id(str(entry.id))

#         assert entry_copy_from_str.id == entry.id


def test_create_entry_repository2(entry_repo2):
    assert entry_repo2.entry_ids() == []


# def test_put_entry_to_entry_repo2(entry_repo2):
#     with unit_of_work(using=entry_repo2) as uw:
#         uw.put(create_entry("a", {}))
#         uw.commit()

#         assert uw.entry_ids() == ["a"]


# def test_discard_entry_from_entry_repo2(entry_repo2):
#     with unit_of_work(using=entry_repo2) as uw:
#         entry = create_entry("b", {})
#         previous_last_modified = entry.last_modified
#         uw.put(entry)
#         uw.commit()

#         entry = uw.by_entry_id("b")

#         assert uw.entry_ids() == ["a", "b"]
#         entry.discard(user="Test", message="Delete.")
#         assert entry.discarded
#         assert entry.last_modified > previous_last_modified
#         uw.update(entry)
#         uw.commit()

#         entry_copy = uw.by_entry_id("b")

#         assert entry_copy.discarded

#         entry_history = uw.history_by_entry_id("b")

#         assert len(entry_history) == 2
#         assert not entry_history[0].discarded
#         assert entry_history[1].discarded
#         assert uw.entry_ids() == ["a"]
