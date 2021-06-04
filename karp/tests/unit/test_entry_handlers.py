from typing import Dict, Optional
import pytest

from .adapters import bootstrap_test_app
from karp.services import messagebus
from karp.domain import events, errors, commands
from karp.utility.unique_id import make_unique_id


def make_create_resource_command(
    resource_id: str, config: Optional[Dict] = None
) -> commands.CreateResource:
    config = config or {
        "fields": {},
        "id": "id",
    }
    return commands.CreateResource(
        id=make_unique_id(),
        resource_id=resource_id,
        name=resource_id.upper(),
        config=config,
        message="create resource",
        created_by="kristoff@example.com",
    )


class TestAddEntry:
    def test_cannot_add_entry_to_nonexistent_resource(self):
        bus = bootstrap_test_app()
        with pytest.raises(errors.ResourceNotFound):
            bus.handle(
                commands.AddEntry(
                    id=make_unique_id(),
                    resource_id="non_existent",
                    entry_id="a",
                    version=3,
                    entry={},
                    user="kristoff@example.com",
                    message="update",
                )
            )

    def test_add_entry(self):
        resource_id = "test_id"
        bus = bootstrap_test_app([resource_id])
        id_ = make_unique_id()
        entry_id = "test_entry"
        entry_name = "Test entry"
        conf = {
            "sort": ["baseform"],
            "fields": {"baseform": {"type": "string", "required": True}},
            "id": "baseform",
        }
        message = "test_entry added"
        #     with mock.patch("karp.utility.time.utc_now", return_value=12345):
        #         entry = create_entry(conf)

        # uow = FakeUnitOfWork(FakeEntryRepository())

        # cmd = commands.CreateResource(
        #     id=make_unique_id(),
        #     resource_id=resource_id,
        #     name="Test",
        #     config=conf,
        #     message=message,
        #     created_by="kristoff@example.com",
        #     entry_repository_type="fake",
        # )
        # bus.handle(cmd)
        bus.handle(make_create_resource_command(resource_id, config=conf))

        cmd = commands.AddEntry(
            resource_id=resource_id,
            id=id_,
            entry_id=entry_id,
            name=entry_name,
            entry={"baseform": entry_id},
            message=message,
            user="kristoff@example.com",
        )

        bus.handle(cmd)

        assert len(bus.ctx.resource_uow.resources) == 1

        # resource = uow.repo.by_resource_id("test_id")

        # assert len(resource.entry_repository) == 1

        uow = bus.ctx.entry_uows.get(resource_id)
        entry = uow.repo.by_id(id_)
        assert entry.id == id_
        assert entry.entry_id == entry_id
        assert entry.resource_id == "test_id"

        assert entry.body == {"baseform": entry_id}
        assert entry.last_modified_by == "kristoff@example.com"

        assert uow.was_committed

        assert (
            bus.ctx.index_uow.repo.indicies[resource_id].entries[entry_id].id
            == entry_id
        )
        assert bus.ctx.index_uow.was_committed

    def test_create_entry_with_same_entry_id_raises(self):
        resource_id = "abc"
        bus = bootstrap_test_app([resource_id])
        bus.handle(make_create_resource_command(resource_id))
        bus.handle(
            commands.AddEntry(
                id=make_unique_id(),
                entry_id="r1",
                resource_id=resource_id,
                name="R1",
                entry={"id": "r1"},
                message="added",
                user="user",
            ),
        )
        with pytest.raises(errors.IntegrityError):
            bus.handle(
                commands.AddEntry(
                    id=make_unique_id(),
                    entry_id="r1",
                    resource_id=resource_id,
                    name="R1",
                    entry={"id": "r1"},
                    message="added",
                    user="user",
                ),
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
        bus = bootstrap_test_app([resource_id])
        id_ = make_unique_id()
        bus.handle(make_create_resource_command(resource_id))
        bus.handle(
            commands.AddEntry(
                id=id_,
                entry_id="r1",
                resource_id=resource_id,
                entry={"id": "r1", "a": "b"},
                message="added",
                user="user",
            ),
        )
        bus.handle(
            commands.UpdateEntry(
                entry_id="r1",
                version=1,
                resource_id=resource_id,
                entry={"id": "r1", "a": "changed", "b": "added"},
                message="changed",
                user="bob",
            ),
        )

        uow = bus.ctx.entry_uows.get(resource_id)
        entry = uow.repo.by_id(id_)
        assert entry is not None
        assert entry.body["a"] == "changed"
        assert entry.body["b"] == "added"
        assert entry.version == 2
        assert uow.was_committed
        assert (
            bus.ctx.index_uow.repo.indicies[resource_id]
            .entries[entry.entry_id]
            .entry["_entry_version"]
            == entry.version
        )
        assert bus.ctx.index_uow.was_committed

    def test_cannot_update_entry_in_nonexistent_resource(self):
        bus = bootstrap_test_app()
        with pytest.raises(errors.ResourceNotFound):
            bus.handle(
                commands.UpdateEntry(
                    resource_id="non_existent",
                    entry_id="a",
                    version=3,
                    entry={},
                    user="kristoff@example.com",
                    message="update",
                )
            )


class TestDeleteEntry:
    def test_can_delete_entry(self):
        resource_id = "abc"
        bus = bootstrap_test_app([resource_id])
        id_ = make_unique_id()
        bus.handle(make_create_resource_command(resource_id))
        bus.handle(
            commands.AddEntry(
                id=id_,
                entry_id="r1",
                resource_id=resource_id,
                entry={"id": "r1", "a": "b"},
                message="added",
                user="user",
            ),
        )
        bus.handle(
            commands.DeleteEntry(
                entry_id="r1",
                version=1,
                resource_id=resource_id,
                message="deleted",
                user="bob",
            ),
        )

        uow = bus.ctx.entry_uows.get_uow(resource_id)
        assert uow.was_committed
        entry = uow.repo.by_id(id_)
        assert entry.version == 2
        assert entry.discarded
        assert (
            entry.entry_id not in bus.ctx.index_uow.repo.indicies[resource_id].entries
        )
        assert bus.ctx.index_uow.was_committed
