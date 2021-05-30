import pytest

from .adapters import FakeUnitOfWork, FakeEntryRepository, FakeResourceRepository, bootstrap_test_app
from karp.services import messagebus
from karp.domain import events, errors, commands
from karp.utility.unique_id import make_unique_id


class TestAddEntry:
    def test_add_entry(self):
        bus = bootstrap_test_app()
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

        # uow = FakeUnitOfWork(FakeEntryRepository())

        # cmd = commands.CreateResource(
        #     id=make_unique_id(),
        #     resource_id="test_id",
        #     name="Test",
        #     config=conf,
        #     message=message,
        #     created_by="kristoff@example.com",
        #     entry_repository_type="fake",
        # )
        # messagebus.handle(cmd, uow)

        cmd = commands.AddEntry(
            resource_id="test_id",
            id=id_,
            entry_id=entry_id,
            name=entry_name,
            body=conf,
            message=message,
            user="kristoff@example.com",
        )

        bus.handle(cmd)

        assert len(bus.resource_uow.resources) == 1

        # resource = uow.repo.by_resource_id("test_id")

        # assert len(resource.entry_repository) == 1

        entry = uow.repo.by_id(id_)
        assert entry.id == id_
        assert entry.entry_id == entry_id
        assert entry.resource_id == "test_id"

        assert entry.body == conf
        assert entry.last_modified_by == "kristoff@example.com"

        assert uow.was_committed

    def test_create_entry_with_same_entry_id_raises(self):
        resource_id = "abc"
        uow = FakeUnitOfWork(FakeEntryRepository())
        messagebus.handle(
            commands.AddEntry(
                id=make_unique_id(),
                entry_id="r1",
                resource_id=resource_id,
                name="R1",
                body={"fields": {}},
                message="added",
                user="user",
            ),
            uow=uow,
        )
        with pytest.raises(errors.IntegrityError):
            messagebus.handle(
                commands.AddEntry(
                    id=make_unique_id(),
                    entry_id="r1",
                    resource_id=resource_id,
                    name="R1",
                    body={"fields": {}},
                    message="added",
                    user="user",
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
        resource_id = "abc"
        uow = FakeUnitOfWork(FakeEntryRepository())
        id_ = make_unique_id()
        messagebus.handle(
            commands.AddEntry(
                id=id_,
                entry_id="r1",
                resource_id=resource_id,
                body={"a": "b"},
                message="added",
                user="user",
            ),
            uow=uow,
        )
        messagebus.handle(
            commands.UpdateEntry(
                entry_id="r1",
                version=1,
                resource_id=resource_id,
                body={"a": "changed", "b": "added"},
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
