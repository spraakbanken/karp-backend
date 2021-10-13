import pytest

# from karp.services import messagebus
from karp.lex.domain import errors

from karp.lex.application import repositories
from karp.lex.application.handlers import CreateResourceHandler
from karp.lex.domain import commands
from karp.lex.domain.commands.resource_commands import CreateResource
# from karp.services impor: repositories

from karp.tests.unit.adapters import (FakeEntryUowFactory, FakeEntryUowRepositoryUnitOfWork, FakeResourceUnitOfWork,
                                      )
from karp.tests.unit import factories


class TestCreateResource:
    def test_create_resource_w_no_entry_repo_raises(
        self,
        entry_repo_repo_uow: FakeEntryUowRepositoryUnitOfWork,
        resource_uow: FakeResourceUnitOfWork,
    ):
        cmd_handler = CreateResourceHandler(resource_uow, entry_repo_repo_uow)
        cmd = factories.CreateResourceFactory()
        with pytest.raises(errors.EntryRepoNotFound):
            cmd_handler(cmd)

    def test_create_resource(
        self,
        entry_repo_repo_uow: FakeEntryUowRepositoryUnitOfWork,
        resource_uow: FakeResourceUnitOfWork,
    ):
        cmd_handler = CreateResourceHandler(resource_uow, entry_repo_repo_uow)
        cmd = factories.CreateResourceFactory()

        cmd_handler(cmd)

        assert len(resource_uow.resources) == 1

        resource = resource_uow.resources.by_id(id_)
        assert resource.id == id_
        assert resource.resource_id == resource_id

        assert resource.name == resource_name

        expected_config = {
            "entry_repository_type": "fake_entries",
            "entry_repository_settings": None,
        }
        expected_config.update(conf)
        assert resource.config == expected_config
        assert resource.last_modified_by == "kristoff@example.com"

        assert resource_uow.was_committed

        # assert bus.ctx.index_uow.repo.indicies[resource_id].created
        # assert bus.ctx.index_uow.was_committed

    def test_create_resource_with_same_resource_id_raises(
        self,
        entry_uow_factory: FakeEntryUowFactory,
        entry_uows: repositories.EntriesUnitOfWork,
        resource_uow: FakeResourceUnitOfWork,
    ):
        # uow = FakeUnitOfWork(FakeResourceRepository())
        bus = bootstrap_test_app(
            entry_uow_factory=entry_uow_factory,
            entry_uows=entry_uows,
            resource_uow=resource_uow
        )
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
        assert resource_uow.was_rolled_back
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
    def test_update_resource(
        self,
        entry_uow_factory: FakeEntryUowFactory,
        entry_uows: repositories.EntriesUnitOfWork,
        resource_uow: FakeResourceUnitOfWork,
    ):
        # uow = FakeUnitOfWork(FakeResourceRepository())
        bus = bootstrap_test_app(
            entry_uow_factory=entry_uow_factory,
            entry_uows=entry_uows,
            resource_uow=resource_uow
        )
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

        resource = resource_uow.resources.by_id(id_)
        assert resource is not None
        assert resource.config["a"] == "changed"
        assert resource.config["b"] == "added"
        assert resource.version == 2
        assert resource_uow.was_committed


class TestPublishResource:
    def test_publish_resource(
        self,
        entry_uow_factory: FakeEntryUowFactory,
        entry_uows: repositories.EntriesUnitOfWork,
        resource_uow: FakeResourceUnitOfWork,
    ):
        # uow = FakeUnitOfWork(FakeResourceRepository())
        bus = bootstrap_test_app(
            entry_uow_factory=entry_uow_factory,
            entry_uows=entry_uows,
            resource_uow=resource_uow
        )
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

        bus.handle(
            commands.CreateResource(
                id=id_,
                resource_id=resource_id,
                name=resource_name,
                config=conf,
                message=message,
                created_by="kristoff@example.com",
            )
        )

        bus.handle(
            commands.PublishResource(
                resource_id=resource_id,
                message=message,
                user="kristoff@example.com",
            )
        )

        resource = resource_uow.resources.by_id(id_)
        assert resource.is_published
        assert resource.version == 2
        assert resource_uow.was_committed
        # assert index_uow.repo.indicies[resource_id].published
        # assert index_uow.was_committed
