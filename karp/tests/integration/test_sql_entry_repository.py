import pytest

from karp.lex_infrastructure.repositories.sql_entries import SqlEntryRepository

from karp.tests.unit.lex import factories


@pytest.fixture(name="entry_repo")
def fixture_entry_repo(sqlite_session_factory):
    session = sqlite_session_factory()
    entry_repo = SqlEntryRepository.from_dict(
        name="test_name",
        resource_config={},
        session=session,
    )
    yield entry_repo

    entry_repo.teardown()


@pytest.fixture(name="entry_repo2")
def fixture_entry_repo2(sqlite_session_factory):
    session = sqlite_session_factory()
    entry_repo = SqlEntryRepository.from_dict(
        name="test_name2",
        resource_config={},
        session=session,
    )
    yield entry_repo

    entry_repo.teardown()


def test_create_entry_repository(entry_repo):
    assert entry_repo.entry_ids() == []


def test_save_entry_to_entry_repo(entry_repo):
    entry = factories.EntryFactory()
    entry_repo.save(entry)

    assert entry_repo.by_id(entry.id).entry_id == entry.entry_id
    assert entry_repo.by_entry_id(entry.entry_id).id == entry.id


def test_update_entry_to_entry_repo(entry_repo):
    entry = factories.EntryFactory()
    entry_repo.save(entry)

    entry.stamp(user='kristoff@example.com', message='hi')
    entry_repo.save(entry)

    assert entry_repo.by_id(entry.id).entry_id == entry.entry_id
    assert entry_repo.by_id(entry.id).version == entry.version
    assert entry_repo.by_id(entry.id, version=1).version == 1
    assert entry_repo.by_entry_id(entry.entry_id).id == entry.id
    assert entry_repo.by_entry_id(entry.entry_id).version == entry.version
    assert entry_repo.by_entry_id(entry.entry_id, version=1).version == 1


def test_change_entry_id_changes(entry_repo):
    entry = factories.EntryFactory()
    entry_repo.save(entry)
    prev_entry_id = entry.entry_id

    entry._entry_id = 'changed_entry_id'
    entry.stamp(user='kristoff@example.com', message='hi')
    entry_repo.save(entry)

    assert entry_repo.get_by_entry_id_optional(prev_entry_id) is None
    assert entry_repo.entry_ids() == ['changed_entry_id']



def test_discard_entry_and_insert_new(entry_repo):
    entry = factories.EntryFactory()
    entry_repo.save(entry)

    entry.stamp(user='kristoff@example.com', message='hi')
    entry_repo.save(entry)

    entry.discard(
        user='kristoff@example.com',
        message='hi',
    )
    entry_repo.save(entry)

    assert entry_repo.entry_ids() == []

    entry2 = factories.EntryFactory(entry_id=entry.entry_id)
    entry_repo.save(entry2)

    entry2.stamp(user='kristoff@example.com', message='hi')
    entry_repo.save(entry2)

    assert entry_repo.by_entry_id(entry.entry_id).entity_id == entry2.entity_id
    assert entry_repo.by_entry_id(entry2.entry_id, version=1).entity_id == entry2.entity_id

    assert entry_repo.entry_ids() == [entry2.entry_id]


def test_create_entry_repository2(entry_repo2):
    assert entry_repo2.entry_ids() == []


class TestSqlEntryRepoGetHistory:
    def test_discard_entry_and_insert_new(self, entry_repo):
        pass
