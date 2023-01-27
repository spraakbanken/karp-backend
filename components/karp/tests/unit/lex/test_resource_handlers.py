import copy

import pytest

from karp.lex.domain import errors

from karp.lex.application import repositories
from karp.lex.application.repositories import ResourceUnitOfWork
from karp.lex.domain import commands

from . import adapters, factories

# type: ignore [arg-type]


class TestCreateResource:
    def test_create_resource_w_no_entry_repo_raises(
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd = factories.CreateResourceFactory()
        with pytest.raises(errors.NoSuchEntryRepository):
            lex_ctx.command_bus.dispatch(cmd)

    def test_create_resource(
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd)

        cmd = factories.CreateResourceFactory(entry_repo_id=cmd.entity_id)
        lex_ctx.command_bus.dispatch(cmd)

        resource_uow = lex_ctx.container.get(ResourceUnitOfWork)  # type: ignore [misc]
        assert resource_uow.was_committed  # type: ignore [attr-defined]
        assert resource_uow.resources.num_entities() == 1

        resource = resource_uow.resources.by_id(cmd.entity_id)
        assert resource.entity_id == cmd.entity_id
        assert resource.resource_id == cmd.resource_id
        # assert len(resource.domain_events) == 1

    def test_create_resource_with_same_resource_id_raises(
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)
        cmd2 = factories.CreateResourceFactory(entry_repo_id=cmd1.entity_id)
        lex_ctx.command_bus.dispatch(cmd2)

        with pytest.raises(errors.IntegrityError):
            lex_ctx.command_bus.dispatch(
                factories.CreateResourceFactory(
                    resource_id=cmd2.resource_id, entry_repo_id=cmd1.entity_id
                )
            )

        resource_uow = lex_ctx.container.get(repositories.ResourceUnitOfWork)  # type: ignore [misc]

        assert resource_uow.was_rolled_back  # type: ignore [attr-defined]

    def test_bad_resource_id_raises(
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd)
        with pytest.raises(errors.InvalidResourceId):
            lex_ctx.command_bus.dispatch(
                factories.CreateResourceFactory(
                    entry_repo_id=cmd.entity_id,
                    resource_id="with space",
                )
            )


class TestUpdateResource:
    def test_update_resource(
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)
        cmd2 = factories.CreateResourceFactory(entry_repo_id=cmd1.entity_id)
        lex_ctx.command_bus.dispatch(cmd2)

        changed_config = copy.deepcopy(cmd2.config)
        changed_config["fields"]["b"] = {"type": "integer"}
        lex_ctx.command_bus.dispatch(
            factories.UpdateResourceFactory(
                resource_id=cmd2.resource_id,
                version=1,
                name="R1",
                config=changed_config,
                message="changed",
                user="bob",
            ),
        )

        resource_uow = lex_ctx.container.get(ResourceUnitOfWork)  # type: ignore [misc]
        assert resource_uow.was_committed  # type: ignore

        resource = resource_uow.resources.by_resource_id(cmd2.resource_id)
        assert resource is not None
        assert resource.config == changed_config
        assert resource.version == 2

        resource = resource_uow.resources.get_by_id(cmd2.entity_id)
        assert resource is not None
        assert resource.config == changed_config
        assert resource.version == 2


class TestPublishResource:
    def test_publish_resource(
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]
        cmd2 = factories.CreateResourceFactory(entry_repo_id=cmd1.entity_id)
        lex_ctx.command_bus.dispatch(cmd2)  # type: ignore [arg-type]

        lex_ctx.command_bus.dispatch(
            commands.PublishResource(
                resource_id=cmd2.resource_id,
                message="publish",
                user="kristoff@example.com",
                version=1,
            )
        )

        resource_uow = lex_ctx.container.get(ResourceUnitOfWork)  # type: ignore [misc]
        assert resource_uow.was_committed  # type: ignore [attr-defined]

        resource = resource_uow.resources.by_id(cmd2.entity_id)  # type: ignore [arg-type]
        assert resource.is_published
        assert resource.version == 2
        # assert index_uow.repo.indicies[resource_id].published
        # assert index_uow.was_committed #type: ignore [attr-defined]
