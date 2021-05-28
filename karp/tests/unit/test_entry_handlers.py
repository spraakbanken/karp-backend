import pytest

from .adapters import FakeUnitOfWork, FakeEntryRepository
from karp.services import messagebus
from karp.domain import events, errors, commands
from karp.utility.unique_id import make_unique_id


class TestCreateEntry:
    def test_create_entry(self):
        id_ = make_unique_id()
        entry_id = "test_entry"
        entry_name = "Test entry"
        conf = {
            "sort": ["baseform"],
            "fields": {"baseform": {"type": "string", "required": True}},
        }
        message = "test_entry added"
        #     with mock.patch("karp.utility.time.utc_now", return_value=12345):
        #         entry = create_entry(conf)

        uow = FakeUnitOfWork(FakeEntryRepository())

        cmd = commands.AddEntry(
            id=id_,
            entry_id=entry_id,
            name=entry_name,
            config=conf,
            message=message,
            created_by="kristoff@example.com",
        )

        messagebus.handle(cmd, uow)

        assert len(uow.repo) == 1

        assert uow.repo[0].id == id_
        assert uow.repo[0].entry_id == entry_id

        assert uow.repo[0].name == entry_name

        assert uow.repo[0].config == conf
        assert uow.repo[0].last_modified_by == "kristoff@example.com"

        assert uow.was_committed

    def test_create_entry_with_same_entry_id_raises(self):
        uow = FakeUnitOfWork(FakeEntryRepository())
        messagebus.handle(
            commands.AddEntry(
                id=make_unique_id(),
                entry_id="r1",
                name="R1",
                config={"fields": {}},
                message="added",
                created_by="user",
            ),
            uow=uow,
        )
        with pytest.raises(errors.IntegrityError):
            messagebus.handle(
                commands.AddEntry(
                    id=make_unique_id(),
                    entry_id="r1",
                    name="R1",
                    config={"fields": {}},
                    message="added",
                    created_by="user",
                ),
                uow=uow,
            )
        # assert uow.repo[0].events[-1] == events.EntryCreated(
        #     id=id_, entry_id=entry_id, name=entry_name, config=conf
        # )

    # assert isinstance(entry, Entry)
    # assert entry.id == uuid.UUID(str(entry.id), version=4)
    # assert entry.version == 1
    # assert entry.entry_id == entry_id
    # assert entry.name == name
    # assert not entry.discarded
    # assert not entry.is_published
    # assert "entry_id" not in entry.config
    # assert "entry_name" not in entry.config
    # assert "sort" in entry.config
    # assert entry.config["sort"] == conf["sort"]
    # assert "fields" in entry.config
    # assert entry.config["fields"] == conf["fields"]
    # assert int(entry.last_modified) == 12345
    # assert entry.message == "Entry added."
    # assert entry.op == EntryOp.ADDED


class TestUpdateEntry:
    def test_update_entry(self):
        uow = FakeUnitOfWork(FakeEntryRepository())
        id_ = make_unique_id()
        messagebus.handle(
            commands.AddEntry(
                id=id_,
                entry_id="r1",
                name="R1",
                config={"a": "b"},
                message="added",
                created_by="user",
            ),
            uow=uow,
        )
        messagebus.handle(
            commands.UpdateEntry(
                entry_id="r1",
                version=1,
                name="R1",
                config={"a": "changed", "b": "added"},
                message="changed",
                user="bob",
            ),
            uow=uow,
        )

        entry = uow.repo.by_id(id_)
        assert entry is not None
        assert entry.config["a"] == "changed"
        assert entry.config["b"] == "added"
        assert entry.version == 2
