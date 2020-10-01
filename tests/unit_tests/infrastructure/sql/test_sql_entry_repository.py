import pytest

from karp.domain.models.entry import (
    create_entry,
    Entry,
    EntryRepository,
)

from karp.infrastructure.unit_of_work import unit_of_work
from karp.infrastructure.sql.sql_entry_repository import SqlEntryRepository


@pytest.fixture(name="entry_repo", scope="session")
def fixture_entry_repo():
    entry_repo = EntryRepository.create(
        "sql_v1", {"table_name": "test_name", "config": {}}
    )
    assert isinstance(entry_repo, SqlEntryRepository)
    assert entry_repo.type == "sql_v1"
    yield entry_repo

    entry_repo.teardown()


@pytest.fixture(name="entry_repo2", scope="session")
def fixture_entry_repo2():
    entry_repo = EntryRepository.create(
        None, {"table_name": "test_name2", "config": {}}
    )
    assert isinstance(entry_repo, SqlEntryRepository)
    assert entry_repo.type == "sql_v1"
    yield entry_repo

    entry_repo.teardown()


def test_create_entry_repository(entry_repo):
    with unit_of_work(using=entry_repo) as uw:
        uw.entry_ids() == []


def test_put_entry_to_entry_repo(entry_repo):
    with unit_of_work(using=entry_repo) as uw:
        entry = create_entry("a", {})
        uw.put(entry)


#         uw.commit()

#         assert uw.entry_ids() == ["a"]

#         entry_copy = uw.by_id(entry.id)

#         assert entry_copy.id == entry.id

#         entry_copy_from_str = uw.by_id(str(entry.id))

#         assert entry_copy_from_str.id == entry.id


def test_entry_repo_by_entry_id(entry_repo):
    with unit_of_work(using=entry_repo) as uw:
        entry = uw.by_entry_id("a")

        assert entry.entry_id == "a"


def test_create_entry_repository2(entry_repo2):
    with unit_of_work(using=entry_repo2) as uw:
        uw.entry_ids() == []


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
