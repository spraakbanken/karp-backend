import pytest

from .adapters import bootstrap_test_app
from karp.services import messagebus
from karp.domain import events, errors, commands
from karp.utility.unique_id import make_unique_id


class TestCreateResource:
    def test_create_resource(self):
        bus = bootstrap_test_app()
        id_ = make_unique_id()
        resource_id = "test_resource"
        resource_name = "Test resource"
        conf = {
            "sort": ["baseform"],
            "fields": {"baseform": {"type": "string", "required": True}},
        }
        message = "test_resource added"
        #     with mock.patch("karp.utility.time.utc_now", return_value=12345):
        #         resource = create_resource(conf)

        # uow = FakeUnitOfWork(FakeResourceRepository())

        cmd = commands.CreateResource(
            id=id_,
            resource_id=resource_id,
            name=resource_name,
            config=conf,
            message=message,
            created_by="kristoff@example.com",
        )

        bus.handle(cmd)

        assert len(bus.resource_uow.resources) == 1

        resource = bus.resource_uow.resources.by_id(id_)
        assert resource.id == id_
        assert resource.resource_id == resource_id

        assert resource.name == resource_name

        assert resource.config == conf
        assert resource.last_modified_by == "kristoff@example.com"

        assert bus.resource_uow.was_committed

    def test_create_resource_with_same_resource_id_raises(self):
        # uow = FakeUnitOfWork(FakeResourceRepository())
        bus = bootstrap_test_app()
        bus.handle(
            commands.CreateResource(
                id=make_unique_id(),
                resource_id="r1",
                name="R1",
                config={"fields": {}},
                message="added",
                created_by="user",
            ),
        )
        with pytest.raises(errors.IntegrityError):
            bus.handle(
                commands.CreateResource(
                    id=make_unique_id(),
                    resource_id="r1",
                    name="R1",
                    config={"fields": {}},
                    message="added",
                    created_by="user",
                ),
            )
        # assert uow.repo[0].events[-1] == events.ResourceCreated(
        #     id=id_, resource_id=resource_id, name=resource_name, config=conf
        # )

    # assert isinstance(resource, Resource)
    # assert resource.id == uuid.UUID(str(resource.id), version=4)
    # assert resource.version == 1
    # assert resource.resource_id == resource_id
    # assert resource.name == name
    # assert not resource.discarded
    # assert not resource.is_published
    # assert "resource_id" not in resource.config
    # assert "resource_name" not in resource.config
    # assert "sort" in resource.config
    # assert resource.config["sort"] == conf["sort"]
    # assert "fields" in resource.config
    # assert resource.config["fields"] == conf["fields"]
    # assert int(resource.last_modified) == 12345
    # assert resource.message == "Resource added."
    # assert resource.op == ResourceOp.ADDED


class TestUpdateResource:
    def test_update_resource(self):
        bus = bootstrap_test_app()
        # uow = FakeUnitOfWork(FakeResourceRepository())
        id_ = make_unique_id()
        bus.handle(
            commands.CreateResource(
                id=id_,
                resource_id="r1",
                name="R1",
                config={"a": "b"},
                message="added",
                created_by="user",
            )
        )
        bus.handle(
            commands.UpdateResource(
                resource_id="r1",
                version=1,
                name="R1",
                config={"a": "changed", "b": "added"},
                message="changed",
                user="bob",
            ),
        )

        resource = bus.resource_uow.resources.by_id(id_)
        assert resource is not None
        assert resource.config["a"] == "changed"
        assert resource.config["b"] == "added"
        assert resource.version == 2
        assert bus.resource_uow.was_committed
