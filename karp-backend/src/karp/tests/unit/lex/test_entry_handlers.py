import pytest
from karp.lex import commands
from karp.lex.application.repositories import (
    EntryUowRepositoryUnitOfWork,
)
from karp.lex.domain import errors
from karp.lex_core.value_objects.unique_id import make_unique_id

from . import adapters, factories


class TestAddEntry:
    def test_cannot_add_entry_to_nonexistent_resource(  # noqa: ANN201
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        with pytest.raises(errors.ResourceNotFound):
            lex_ctx.command_bus.dispatch(
                factories.AddEntryFactory(  # type: ignore [arg-type]
                    resourceId="non_existent",
                )
            )

    def test_add_entry(  # noqa: ANN201
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory(
            entryRepoId=cmd1.id,  # type: ignore [attr-defined]
            config={
                "sort": ["baseform"],
                "fields": {"baseform": {"type": "string", "required": True}},
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)  # type: ignore [arg-type]

        entry_id = "beta"
        cmd3 = factories.AddEntryFactory(
            resourceId=cmd2.resource_id,  # type: ignore [attr-defined]
            entry={"baseform": entry_id},
        )

        lex_ctx.command_bus.dispatch(cmd3)  # type: ignore [arg-type]

        entry_uow_repo_uow = lex_ctx.container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [misc]
        uow = entry_uow_repo_uow.repo.get_by_id(cmd2.entry_repo_id)  # type: ignore [attr-defined]
        entry = uow.repo.by_id(cmd3.id)  # type: ignore [attr-defined]
        assert entry is not None
        assert entry.id == cmd3.id  # type: ignore [attr-defined]
        # assert entry.entry_id == entry_id
        # assert entry.repo_id == cmd3.resource_id

        assert entry.body == {"baseform": entry_id}
        assert entry.last_modified_by == cmd3.user

        assert uow.was_committed  # type: ignore [attr-defined]

        # assert (
        #     bus.ctx.index_uow.repo.indicies[resource_id].entries[entry_id].id
        #     == entry_id
        # )
        # assert bus.ctx.index_uow.was_committed #type: ignore [attr-defined]

    @pytest.mark.skip(reason="we don't use entry_id anymore")
    def test_create_entry_with_same_entry_id_raises(  # noqa: ANN201
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory(
            entryRepoId=cmd1.id,  # type: ignore [attr-defined]
            config={
                "sort": ["baseform"],
                "fields": {"baseform": {"type": "string", "required": True}},
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)  # type: ignore [arg-type]

        entry_id = "beta"
        cmd3 = factories.AddEntryFactory(
            resourceId=cmd2.resource_id,  # type: ignore [attr-defined]
            entry={"baseform": entry_id},
        )

        lex_ctx.command_bus.dispatch(cmd3)  # type: ignore [arg-type]

        with pytest.raises(errors.IntegrityError):
            lex_ctx.command_bus.dispatch(
                factories.AddEntryFactory(  # type: ignore [arg-type]
                    resourceId=cmd3.resource_id,  # type: ignore [attr-defined]
                    entry={"baseform": entry_id},
                ),
            )


class TestUpdateEntry:
    def test_update_entry(  # noqa: ANN201
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory(
            entryRepoId=cmd1.id,  # type: ignore [attr-defined]
            config={
                "sort": ["baseform"],
                "fields": {
                    "baseform": {"type": "string", "required": True},
                    "a": {
                        "type": "string",
                    },
                },
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)  # type: ignore [arg-type]

        entry_id = "beta"
        cmd3 = factories.AddEntryFactory(
            resourceId=cmd2.resource_id,  # type: ignore [attr-defined]
            entry={"baseform": entry_id, "a": "orig"},
        )

        lex_ctx.command_bus.dispatch(cmd3)  # type: ignore [arg-type]

        lex_ctx.command_bus.dispatch(
            factories.UpdateEntryFactory(  # type: ignore [arg-type]
                id=cmd3.id,  # type: ignore [attr-defined]
                version=1,
                resourceId=cmd3.resource_id,  # type: ignore [attr-defined]
                entry={"baseform": entry_id, "a": "changed", "b": "added"},
            ),
        )

        entry_uow_repo_uow = lex_ctx.container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [misc]
        uow = entry_uow_repo_uow.repo.get_by_id(cmd2.entry_repo_id)  # type: ignore [attr-defined]
        assert uow.was_committed  # type: ignore [attr-defined]

        entry = uow.repo.by_id(cmd3.id)  # type: ignore [attr-defined]
        assert entry is not None
        assert entry.body["a"] == "changed"
        assert entry.body["b"] == "added"
        assert entry.version == 2
        # assert (
        #     bus.ctx.index_uow.repo.indicies[resource_id]
        #     .entries[entry.entry_id]
        #     .entry["_entry_version"]
        #     == entry.version
        # )
        # assert bus.ctx.index_uow.was_committed #type: ignore [attr-defined]

    def test_cannot_update_entry_in_nonexistent_resource(  # noqa: ANN201
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        with pytest.raises(errors.ResourceNotFound):
            lex_ctx.command_bus.dispatch(
                commands.UpdateEntry(
                    id=make_unique_id(),
                    resourceId="non_existent",
                    version=3,
                    entry={},
                    user="kristoff@example.com",
                    message="update",
                )
            )

    def test_update_of_entry_id_changes_entry_id(  # noqa: ANN201
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory(
            entryRepoId=cmd1.id,  # type: ignore [attr-defined]
            config={
                "sort": ["baseform"],
                "fields": {
                    "baseform": {"type": "string", "required": True},
                },
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)  # type: ignore [arg-type]

        entry_id = "beta"
        cmd3 = factories.AddEntryFactory(
            resourceId=cmd2.resource_id,  # type: ignore [attr-defined]
            entry={"baseform": entry_id},
        )

        lex_ctx.command_bus.dispatch(cmd3)  # type: ignore [arg-type]

        new_entry_id = "gamma"
        lex_ctx.command_bus.dispatch(
            factories.UpdateEntryFactory(  # type: ignore [arg-type]
                id=cmd3.id,  # type: ignore [attr-defined]
                version=1,
                resourceId=cmd3.resource_id,  # type: ignore [attr-defined]
                entry={"baseform": new_entry_id},
            ),
        )

        entry_uow_repo_uow = lex_ctx.container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [misc]
        uow = entry_uow_repo_uow.repo.get_by_id(cmd2.entry_repo_id)  # type: ignore [attr-defined]
        assert uow.was_committed  # type: ignore [attr-defined]

        entry = uow.repo.by_id(cmd3.id)  # type: ignore [attr-defined]
        # assert entry.entry_id == new_entry_id
        assert entry.version == 2

        # entry = uow.repo.by_entry_id(new_entry_id)
        # assert entry.id == cmd3.id

        # with pytest.raises(errors.EntryNotFound):
        #     uow.repo.by_entry_id(entry_id)


class TestDeleteEntry:
    def test_can_delete_entry(  # noqa: ANN201
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory(
            entryRepoId=cmd1.id,  # type: ignore [attr-defined]
            config={
                "sort": ["baseform"],
                "fields": {
                    "baseform": {"type": "string", "required": True},
                    "a": {
                        "type": "string",
                    },
                },
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)  # type: ignore [arg-type]

        entry_id = "beta"
        cmd3 = factories.AddEntryFactory(
            resourceId=cmd2.resource_id,  # type: ignore [attr-defined]
            entry={"baseform": entry_id, "a": "orig"},
        )

        lex_ctx.command_bus.dispatch(cmd3)  # type: ignore [arg-type]

        lex_ctx.command_bus.dispatch(
            commands.DeleteEntry(
                id=cmd3.id,  # type: ignore [attr-defined]
                version=1,
                resourceId=cmd3.resource_id,  # type: ignore [attr-defined]
                message="deleted",
                user="bob",
            ),
        )

        entry_uow_repo_uow = lex_ctx.container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [misc]
        uow = entry_uow_repo_uow.repo.get_by_id(cmd2.entry_repo_id)  # type: ignore [attr-defined]
        assert uow.was_committed  # type: ignore [attr-defined]

        entry = uow.repo.by_id(cmd3.id)  # type: ignore [attr-defined]
        assert entry.version == 2
        assert entry.discarded

        # entry = uow.repo._by_entry_id(entry_id)
        # assert entry.version == 2
        # assert entry.discarded
        # assert (
        #     entry.entry_id not in bus.ctx.index_uow.repo.indicies[resource_id].entries
        # )
        # assert bus.ctx.index_uow.was_committed # type: ignore [attr-defined]


class TestAddEntries:
    def test_cannot_add_entries_to_nonexistent_resource(  # noqa: ANN201
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        with pytest.raises(errors.ResourceNotFound):
            lex_ctx.command_bus.dispatch(
                factories.AddEntriesFactory(
                    resourceId="non_existent",  # type: ignore [arg-type]
                )
            )

    def test_add_entry(  # noqa: ANN201
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory(
            entryRepoId=cmd1.id,  # type: ignore [attr-defined]
            config={
                "sort": ["baseform"],
                "fields": {"baseform": {"type": "string", "required": True}},
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)  # type: ignore [arg-type]

        entry_id = "beta"
        cmd3 = factories.AddEntriesFactory(
            resourceId=cmd2.resource_id,  # type: ignore [attr-defined]
            entries=[{"baseform": entry_id}],
        )

        lex_ctx.command_bus.dispatch(cmd3)  # type: ignore [arg-type]

        entry_uow_repo_uow = lex_ctx.container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [misc]
        uow = entry_uow_repo_uow.repo.get_by_id(cmd2.entry_repo_id)  # type: ignore [attr-defined]
        # entry = uow.repo.by_id(cmd3.id)
        # assert entry is not None
        # assert entry.entry_id == entry_id
        # # assert entry.repo_id == cmd3.resource_id

        # assert entry.body == {"baseform": entry_id}
        # assert entry.last_modified_by == cmd3.user

        assert uow.was_committed  # type: ignore [attr-defined]

        # assert (
        #     bus.ctx.index_uow.repo.indicies[resource_id].entries[entry_id].id
        #     == entry_id
        # )
        # assert bus.ctx.index_uow.was_committed #type: ignore [attr-defined]

    @pytest.mark.skip(reason="we don't use entry_id")
    def test_add_entry_with_same_entry_id_raises(  # noqa: ANN201
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory(
            entryRepoId=cmd1.id,  # type: ignore [attr-defined]
            config={
                "sort": ["baseform"],
                "fields": {"baseform": {"type": "string", "required": True}},
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)  # type: ignore [arg-type]

        entry_id = "beta"
        cmd3 = factories.AddEntriesFactory(
            resourceId=cmd2.resource_id,  # type: ignore [attr-defined]
            entries=[{"baseform": entry_id}],
        )

        lex_ctx.command_bus.dispatch(cmd3)  # type: ignore [arg-type]

        with pytest.raises(errors.IntegrityError):
            lex_ctx.command_bus.dispatch(
                factories.AddEntriesFactory(  # type: ignore [arg-type]
                    resourceId=cmd3.resource_id,  # type: ignore [attr-defined]
                    entries=[{"baseform": entry_id}],
                ),
            )


class TestAddEntriesInChunks:
    def test_cannot_add_entries_to_nonexistent_resource(  # noqa: ANN201
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        with pytest.raises(errors.ResourceNotFound):
            lex_ctx.command_bus.dispatch(
                factories.AddEntriesInChunksFactory(  # type: ignore [arg-type]
                    resourceId="non_existent",
                )
            )

    def test_add_entry(  # noqa: ANN201
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory(
            entryRepoId=cmd1.id,  # type: ignore [attr-defined]
            config={
                "sort": ["baseform"],
                "fields": {"baseform": {"type": "string", "required": True}},
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)  # type: ignore [arg-type]

        entry_id = "beta"
        entity_id = make_unique_id()  # noqa: F841
        cmd3 = factories.AddEntriesInChunksFactory(
            resourceId=cmd2.resource_id,  # type: ignore [attr-defined]
            entries=[{"baseform": entry_id}],
        )

        lex_ctx.command_bus.dispatch(cmd3)  # type: ignore [arg-type]

        entry_uow_repo_uow = lex_ctx.container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [misc]
        uow = entry_uow_repo_uow.repo.get_by_id(cmd2.entry_repo_id)  # type: ignore [attr-defined]
        # entry = uow.repo.by_id(entry_id)
        # assert entry is not None
        # assert entry.entry_id == entry_id
        # # assert entry.repo_id == cmd3.resource_id

        # assert entry.body == {"baseform": entry_id}
        # assert entry.last_modified_by == cmd3.user

        assert uow.was_committed  # type: ignore [attr-defined]

        # assert (
        #     bus.ctx.index_uow.repo.indicies[resource_id].entries[entry_id].id
        #     == entry_id
        # )
        # assert bus.ctx.index_uow.was_committed #type: ignore [attr-defined]

    @pytest.mark.skip(reason="we don't use entry_id")
    def test_add_entry_with_same_entry_id_raises(  # noqa: ANN201
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory(
            entryRepoId=cmd1.id,  # type: ignore [attr-defined]
            config={
                "sort": ["baseform"],
                "fields": {"baseform": {"type": "string", "required": True}},
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)  # type: ignore [arg-type]

        entry_id = "beta"
        cmd3 = factories.AddEntriesInChunksFactory(
            resourceId=cmd2.resource_id,  # type: ignore [attr-defined]
            entries=[{"baseform": entry_id}],
        )

        lex_ctx.command_bus.dispatch(cmd3)  # type: ignore [arg-type]

        with pytest.raises(errors.IntegrityError):
            lex_ctx.command_bus.dispatch(
                factories.AddEntriesInChunksFactory(  # type: ignore [arg-type]
                    resourceId=cmd3.resource_id,  # type: ignore [attr-defined]
                    entries=[{"baseform": entry_id}],
                ),
            )


class TestImportEntries:
    def test_cannot_import_entries_to_nonexistent_resource(  # noqa: ANN201
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        with pytest.raises(errors.ResourceNotFound):
            lex_ctx.command_bus.dispatch(
                factories.ImportEntriesFactory(  # type: ignore [arg-type]
                    resourceId="non_existent",
                )
            )

    def test_import_entries(  # noqa: ANN201
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory(
            entryRepoId=cmd1.id,  # type: ignore [attr-defined]
            config={
                "sort": ["baseform"],
                "fields": {"baseform": {"type": "string", "required": True}},
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)  # type: ignore [arg-type]

        entry_id = "beta"
        entity_id = make_unique_id()
        cmd3 = factories.ImportEntriesFactory(
            resourceId=cmd2.resource_id,  # type: ignore [attr-defined]
            entries=[
                {
                    "id": entity_id,
                    "entry": {"baseform": entry_id},
                    "user": "user1",
                }
            ],
        )

        lex_ctx.command_bus.dispatch(cmd3)  # type: ignore [arg-type]

        entry_uow_repo_uow = lex_ctx.container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [misc]
        uow = entry_uow_repo_uow.repo.get_by_id(cmd2.entry_repo_id)  # type: ignore [attr-defined]
        entry = uow.repo.by_id(entity_id)
        assert entry is not None
        # assert entry.entry_id == entry_id
        # assert entry.repo_id == cmd3.resource_id

        assert entry.body == {"baseform": entry_id}
        assert entry.last_modified_by == "user1"

        assert uow.was_committed  # type: ignore [attr-defined]

        # assert (
        #     bus.ctx.index_uow.repo.indicies[resource_id].entries[entry_id].id
        #     == entry_id
        # )
        # assert bus.ctx.index_uow.was_committed #type: ignore [attr-defined]

    @pytest.mark.skip(reason="we don't use entry_id")
    def test_import_entries_with_same_entry_id_raises(  # noqa: ANN201
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory(
            entryRepoId=cmd1.id,  # type: ignore [attr-defined]
            config={
                "sort": ["baseform"],
                "fields": {"baseform": {"type": "string", "required": True}},
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)  # type: ignore [arg-type]

        entry_id = "beta"
        cmd3 = factories.ImportEntriesFactory(
            resourceId=cmd2.resource_id,  # type: ignore [attr-defined]
            entries=[
                {
                    "entry": {"baseform": entry_id},
                }
            ],
        )

        lex_ctx.command_bus.dispatch(cmd3)  # type: ignore [arg-type]

        with pytest.raises(errors.IntegrityError):
            lex_ctx.command_bus.dispatch(
                factories.ImportEntriesFactory(  # type: ignore [arg-type]
                    resourceId=cmd3.resource_id,  # type: ignore [attr-defined]
                    entries=[{"entry": {"baseform": entry_id}}],
                ),
            )


class TestImportEntriesInChunks:
    def test_cannot_import_entries_to_nonexistent_resource(  # noqa: ANN201
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        with pytest.raises(errors.ResourceNotFound):
            lex_ctx.command_bus.dispatch(  # type: ignore [arg-type]
                factories.ImportEntriesInChunksFactory(  # type: ignore [arg-type]
                    resourceId="non_existent",
                )
            )

    def test_import_entries(  # noqa: ANN201
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory(
            entryRepoId=cmd1.id,  # type: ignore [attr-defined]
            config={
                "sort": ["baseform"],
                "fields": {"baseform": {"type": "string", "required": True}},
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)  # type: ignore [arg-type]

        entry_id = "beta"
        entity_id = make_unique_id()
        cmd3 = factories.ImportEntriesInChunksFactory(
            resourceId=cmd2.resource_id,  # type: ignore [attr-defined]
            entries=[
                {
                    "id": entity_id,
                    "entry": {"baseform": entry_id},
                    "user": "user1",
                }
            ],
        )

        lex_ctx.command_bus.dispatch(cmd3)  # type: ignore [arg-type]

        entry_uow_repo_uow = lex_ctx.container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [misc]
        uow = entry_uow_repo_uow.repo.get_by_id(cmd2.entry_repo_id)  # type: ignore [attr-defined]
        entry = uow.repo.by_id(entity_id)  # type: ignore [attr.defined]
        assert entry is not None
        # assert entry.entry_id == entry_id
        # assert entry.repo_id == cmd3.resource_id

        assert entry.body == {"baseform": entry_id}
        assert entry.last_modified_by == "user1"

        assert uow.was_committed  # type: ignore [attr-defined]

        # assert (
        #     bus.ctx.index_uow.repo.indicies[resource_id].entries[entry_id].id
        #     == entry_id
        # )
        # assert bus.ctx.index_uow.was_committed #type: ignore [attr-defined]

    @pytest.mark.skip(reason="we don't use entry_id")
    def test_import_entries_with_same_entry_id_raises(  # noqa: ANN201
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory(
            entryRepoId=cmd1.id,  # type: ignore [attr-defined]
            config={
                "sort": ["baseform"],
                "fields": {"baseform": {"type": "string", "required": True}},
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)  # type: ignore [arg-type]

        entry_id = "beta"
        cmd3 = factories.ImportEntriesInChunksFactory(
            resourceId=cmd2.resource_id,  # type: ignore [attr-defined]
            entries=[
                {
                    "entry": {"baseform": entry_id},
                }
            ],
        )

        lex_ctx.command_bus.dispatch(cmd3)  # type: ignore [arg-type]

        with pytest.raises(errors.IntegrityError):
            lex_ctx.command_bus.dispatch(
                factories.ImportEntriesInChunksFactory(  # type: ignore [arg-type]
                    resourceId=cmd3.resource_id,  # type: ignore [attr-defined]
                    entries=[{"entry": {"baseform": entry_id}}],
                ),
            )
