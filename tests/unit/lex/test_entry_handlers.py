import pytest
from karp.lex.application.repositories import (
    EntryUowRepositoryUnitOfWork,
)
from karp.lex.domain import errors
from karp.lex_core.value_objects.unique_id import make_unique_id

from . import adapters, factories


class TestAddEntry:
    def test_cannot_add_entry_to_nonexistent_resource(
        self,
        lex_ctx: adapters.UnitTestContext,
    ) -> None:
        with pytest.raises(errors.ResourceNotFound):
            lex_ctx.command_bus.dispatch(
                factories.AddEntryFactory.build(
                    resourceId="non_existent",
                )
            )

    def test_invalid_entry_raises(
        self,
        lex_ctx: adapters.UnitTestContext,
    ) -> None:
        cmd1 = factories.CreateEntryRepositoryFactory.build()
        lex_ctx.command_bus.dispatch(cmd1)

        cmd2 = factories.CreateResourceFactory.build(
            entryRepoId=cmd1.id,
            config={
                "sort": ["baseform"],
                "fields": {"baseform": {"type": "string", "required": True}},
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)

        with pytest.raises(errors.InvalidEntry):
            lex_ctx.command_bus.dispatch(
                factories.AddEntryFactory.build(
                    resourceId=cmd2.resource_id,
                    entry={"waveform": "tsunami"},
                )
            )

    def test_cant_add_entry_to_discarded_resource(
        self,
        lex_ctx: adapters.UnitTestContext,
    ) -> None:
        cmd1 = factories.CreateEntryRepositoryFactory.build()
        lex_ctx.command_bus.dispatch(cmd1)

        cmd2 = factories.CreateResourceFactory.build(
            entryRepoId=cmd1.id,
        )
        lex_ctx.command_bus.dispatch(cmd2)
        lex_ctx.command_bus.dispatch(
            factories.DeleteResourceFactory.build(
                resourceId=cmd2.resource_id,
                #  version=1,
            )
        )

        with pytest.raises(errors.DiscardedEntityError):
            lex_ctx.command_bus.dispatch(
                factories.AddEntryFactory.build(
                    resourceId=cmd2.resource_id,
                    entry={"waveform": "tsunami"},
                )
            )

    def test_add_entry(
        self,
        lex_ctx: adapters.UnitTestContext,
    ) -> None:
        cmd1 = factories.CreateEntryRepositoryFactory.build()
        lex_ctx.command_bus.dispatch(cmd1)

        cmd2 = factories.CreateResourceFactory.build(
            entryRepoId=cmd1.id,
            config={
                "sort": ["baseform"],
                "fields": {"baseform": {"type": "string", "required": True}},
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)

        entry_id = "beta"
        cmd3 = factories.AddEntryFactory.build(
            resourceId=cmd2.resource_id,
            entry={"baseform": entry_id},
        )

        lex_ctx.command_bus.dispatch(cmd3)

        entry_uow_repo_uow = lex_ctx.container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [type-abstract]
        uow = entry_uow_repo_uow.repo.get_by_id(cmd2.entry_repo_id)
        entry = uow.repo.by_id(cmd3.id)
        assert entry is not None
        assert entry.id == cmd3.id

        assert entry.body == {"baseform": entry_id}
        assert entry.last_modified_by == cmd3.user

        assert uow.was_committed  # type: ignore [attr-defined]


class TestUpdateEntry:
    def test_cannot_update_entry_in_nonexistent_resource(
        self,
        lex_ctx: adapters.UnitTestContext,
    ) -> None:
        with pytest.raises(errors.ResourceNotFound):
            lex_ctx.command_bus.dispatch(
                factories.UpdateEntryFactory.build(
                    id=make_unique_id(),
                    resourceId="non_existent",
                    version=1,
                )
            )

    def test_invalid_entry_raises(
        self,
        lex_ctx: adapters.UnitTestContext,
    ) -> None:
        cmd1 = factories.CreateEntryRepositoryFactory.build()
        lex_ctx.command_bus.dispatch(cmd1)

        cmd2 = factories.CreateResourceFactory.build(
            entryRepoId=cmd1.id,
            config={
                "sort": ["baseform"],
                "fields": {"baseform": {"type": "string", "required": True}},
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)
        cmd3 = factories.AddEntryFactory.build(
            resourceId=cmd2.resource_id,
            entry={"baseform": "tsunami"},
        )
        lex_ctx.command_bus.dispatch(cmd3)

        with pytest.raises(errors.InvalidEntry):
            lex_ctx.command_bus.dispatch(
                factories.UpdateEntryFactory.build(
                    id=cmd3.id,
                    resourceId=cmd2.resource_id,
                    entry={"waveform": "tsunami"},
                    version=1,
                )
            )

    def test_cant_update_entry_in_discarded_resource(
        self,
        lex_ctx: adapters.UnitTestContext,
    ) -> None:
        cmd1 = factories.CreateEntryRepositoryFactory.build()
        lex_ctx.command_bus.dispatch(cmd1)

        cmd2 = factories.CreateResourceFactory.build(
            entryRepoId=cmd1.id,
        )
        lex_ctx.command_bus.dispatch(cmd2)
        cmd3 = factories.AddEntryFactory.build(
            resourceId=cmd2.resource_id,
            entry={"baseform": "tsunami"},
        )
        lex_ctx.command_bus.dispatch(cmd3)

        lex_ctx.command_bus.dispatch(
            factories.DeleteResourceFactory.build(
                resourceId=cmd2.resource_id,
                #     version=1,
            )
        )
        with pytest.raises(errors.DiscardedEntityError):
            lex_ctx.command_bus.dispatch(
                factories.UpdateEntryFactory.build(
                    id=cmd3.id,
                    resourceId=cmd2.resource_id,
                    entry={"baseform": "tsunami2"},
                    version=1,
                )
            )

    def test_cant_update_nonexistent_entry(
        self,
        lex_ctx: adapters.UnitTestContext,
    ) -> None:
        cmd1 = factories.CreateEntryRepositoryFactory.build()
        lex_ctx.command_bus.dispatch(cmd1)

        cmd2 = factories.CreateResourceFactory.build(
            entryRepoId=cmd1.id,
        )
        lex_ctx.command_bus.dispatch(cmd2)

        with pytest.raises(errors.EntryNotFound):
            lex_ctx.command_bus.dispatch(
                factories.UpdateEntryFactory.build(
                    id=make_unique_id(),
                    resourceId=cmd2.resource_id,
                    entry={"baseform": "small wave"},
                    version=1,
                )
            )

    def test_cant_update_discarded_entry(
        self,
        lex_ctx: adapters.UnitTestContext,
    ) -> None:
        cmd1 = factories.CreateEntryRepositoryFactory.build()
        lex_ctx.command_bus.dispatch(cmd1)

        cmd2 = factories.CreateResourceFactory.build(
            entryRepoId=cmd1.id,
        )
        lex_ctx.command_bus.dispatch(cmd2)
        cmd3 = factories.AddEntryFactory.build(
            resourceId=cmd2.resource_id,
            entry={"baseform": "tsunami"},
        )
        lex_ctx.command_bus.dispatch(cmd3)

        lex_ctx.command_bus.dispatch(
            factories.DeleteEntryFactory.build(
                id=cmd3.id,
                resourceId=cmd2.resource_id,
                version=1,
            )
        )
        with pytest.raises(errors.DiscardedEntityError):
            lex_ctx.command_bus.dispatch(
                factories.UpdateEntryFactory.build(
                    id=cmd3.id,
                    resourceId=cmd2.resource_id,
                    entry={"baseform": "small wave"},
                    version=2,
                )
            )

    def test_update_w_wrong_version_raises(
        self,
        lex_ctx: adapters.UnitTestContext,
    ) -> None:
        cmd1 = factories.CreateEntryRepositoryFactory.build()
        lex_ctx.command_bus.dispatch(cmd1)

        cmd2 = factories.CreateResourceFactory.build(
            entryRepoId=cmd1.id,
        )
        lex_ctx.command_bus.dispatch(cmd2)
        cmd3 = factories.AddEntryFactory.build(
            resourceId=cmd2.resource_id,
            entry={"baseform": "tsunami"},
        )
        lex_ctx.command_bus.dispatch(cmd3)

        with pytest.raises(errors.UpdateConflict):
            lex_ctx.command_bus.dispatch(
                factories.UpdateEntryFactory.build(
                    id=cmd3.id,
                    resourceId=cmd2.resource_id,
                    entry={"baseform": "small wave"},
                    version=2,
                )
            )

    def test_update_entry(
        self,
        lex_ctx: adapters.UnitTestContext,
    ) -> None:
        cmd1 = factories.CreateEntryRepositoryFactory.build()
        lex_ctx.command_bus.dispatch(cmd1)

        cmd2 = factories.CreateResourceFactory.build(
            entryRepoId=cmd1.id,
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
        lex_ctx.command_bus.dispatch(cmd2)

        entry_id = "beta"
        cmd3 = factories.AddEntryFactory.build(
            resourceId=cmd2.resource_id,
            entry={"baseform": entry_id, "a": "orig"},
        )

        lex_ctx.command_bus.dispatch(cmd3)

        lex_ctx.command_bus.dispatch(
            factories.UpdateEntryFactory.build(
                id=cmd3.id,
                version=1,
                resourceId=cmd3.resource_id,
                entry={"baseform": entry_id, "a": "changed", "b": "added"},
            ),
        )

        entry_uow_repo_uow = lex_ctx.container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [type-abstract]
        uow = entry_uow_repo_uow.repo.get_by_id(cmd2.entry_repo_id)
        assert uow.was_committed  # type: ignore [attr-defined]

        entry = uow.repo.by_id(cmd3.id)
        assert entry is not None
        assert entry.body["a"] == "changed"
        assert entry.body["b"] == "added"
        assert entry.version == 2

    def test_update_of_entry_id_changes_entry_id(
        self,
        lex_ctx: adapters.UnitTestContext,
    ) -> None:
        cmd1 = factories.CreateEntryRepositoryFactory.build()
        lex_ctx.command_bus.dispatch(cmd1)

        cmd2 = factories.CreateResourceFactory.build(
            entryRepoId=cmd1.id,
            config={
                "sort": ["baseform"],
                "fields": {
                    "baseform": {"type": "string", "required": True},
                },
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)

        entry_id = "beta"
        cmd3 = factories.AddEntryFactory.build(
            resourceId=cmd2.resource_id,
            entry={"baseform": entry_id},
        )

        lex_ctx.command_bus.dispatch(cmd3)

        new_entry_id = "gamma"
        lex_ctx.command_bus.dispatch(
            factories.UpdateEntryFactory.build(
                id=cmd3.id,  # type: ignore [attr-defined]
                version=1,
                resourceId=cmd3.resource_id,
                entry={"baseform": new_entry_id},
            ),
        )

        entry_uow_repo_uow = lex_ctx.container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [type-abstract]
        uow = entry_uow_repo_uow.repo.get_by_id(cmd2.entry_repo_id)
        assert uow.was_committed  # type: ignore [attr-defined]

        entry = uow.repo.by_id(cmd3.id)
        assert entry.version == 2


class TestDeleteEntry:
    def test_cannot_delete_entry_in_nonexistent_resource(
        self,
        lex_ctx: adapters.UnitTestContext,
    ) -> None:
        with pytest.raises(errors.ResourceNotFound):
            lex_ctx.command_bus.dispatch(
                factories.DeleteEntryFactory.build(
                    id=make_unique_id(),
                    resourceId="non_existent",
                    version=1,
                )
            )

    def test_cant_delete_entry_in_discarded_resource(
        self,
        lex_ctx: adapters.UnitTestContext,
    ) -> None:
        cmd1 = factories.CreateEntryRepositoryFactory.build()
        lex_ctx.command_bus.dispatch(cmd1)

        cmd2 = factories.CreateResourceFactory.build(
            entryRepoId=cmd1.id,
        )
        lex_ctx.command_bus.dispatch(cmd2)
        cmd3 = factories.AddEntryFactory.build(
            resourceId=cmd2.resource_id,
            entry={"baseform": "tsunami"},
        )
        lex_ctx.command_bus.dispatch(cmd3)

        lex_ctx.command_bus.dispatch(
            factories.DeleteResourceFactory.build(
                resourceId=cmd2.resource_id,
                #     version=1,
            )
        )
        with pytest.raises(errors.DiscardedEntityError):
            lex_ctx.command_bus.dispatch(
                factories.DeleteEntryFactory.build(
                    id=cmd3.id,
                    resourceId=cmd2.resource_id,
                    version=1,
                )
            )

    def test_cant_delete_nonexistent_entry(
        self,
        lex_ctx: adapters.UnitTestContext,
    ) -> None:
        cmd1 = factories.CreateEntryRepositoryFactory.build()
        lex_ctx.command_bus.dispatch(cmd1)

        cmd2 = factories.CreateResourceFactory.build(
            entryRepoId=cmd1.id,
        )
        lex_ctx.command_bus.dispatch(cmd2)

        with pytest.raises(errors.EntryNotFound):
            lex_ctx.command_bus.dispatch(
                factories.DeleteEntryFactory.build(
                    id=make_unique_id(),
                    resourceId=cmd2.resource_id,
                    version=1,
                )
            )

    def test_delete_w_wrong_version_raises(
        self,
        lex_ctx: adapters.UnitTestContext,
    ) -> None:
        cmd1 = factories.CreateEntryRepositoryFactory.build()
        lex_ctx.command_bus.dispatch(cmd1)

        cmd2 = factories.CreateResourceFactory.build(
            entryRepoId=cmd1.id,
        )
        lex_ctx.command_bus.dispatch(cmd2)
        cmd3 = factories.AddEntryFactory.build(
            resourceId=cmd2.resource_id,
            entry={"baseform": "tsunami"},
        )
        lex_ctx.command_bus.dispatch(cmd3)

        with pytest.raises(errors.UpdateConflict):
            lex_ctx.command_bus.dispatch(
                factories.DeleteEntryFactory.build(
                    id=cmd3.id,
                    resourceId=cmd2.resource_id,
                    version=2,
                )
            )

    def test_can_delete_entry(
        self,
        lex_ctx: adapters.UnitTestContext,
    ) -> None:
        cmd1 = factories.CreateEntryRepositoryFactory.build()
        lex_ctx.command_bus.dispatch(cmd1)

        cmd2 = factories.CreateResourceFactory.build(
            entryRepoId=cmd1.id,
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
        lex_ctx.command_bus.dispatch(cmd2)

        entry_id = "beta"
        cmd3 = factories.AddEntryFactory.build(
            resourceId=cmd2.resource_id,
            entry={"baseform": entry_id, "a": "orig"},
        )

        lex_ctx.command_bus.dispatch(cmd3)

        lex_ctx.command_bus.dispatch(
            factories.DeleteEntryFactory.build(
                id=cmd3.id,
                version=1,
                resourceId=cmd3.resource_id,
            ),
        )

        entry_uow_repo_uow = lex_ctx.container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [type-abstract]
        uow = entry_uow_repo_uow.repo.get_by_id(cmd2.entry_repo_id)
        assert uow.was_committed  # type: ignore [attr-defined]

        entry = uow.repo.by_id(cmd3.id)
        assert entry.version == 2
        assert entry.discarded

    def test_deleting_discarded_entry_does_not_raise_version(
        self,
        lex_ctx: adapters.UnitTestContext,
    ) -> None:
        cmd1 = factories.CreateEntryRepositoryFactory.build()
        lex_ctx.command_bus.dispatch(cmd1)

        cmd2 = factories.CreateResourceFactory.build(
            entryRepoId=cmd1.id,
            config={
                "sort": ["baseform"],
                "fields": {
                    "baseform": {"type": "string", "required": True},
                },
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)

        entry_id = "beta"
        cmd3 = factories.AddEntryFactory.build(
            resourceId=cmd2.resource_id,
            entry={"baseform": entry_id, "a": "orig"},
        )

        lex_ctx.command_bus.dispatch(cmd3)

        lex_ctx.command_bus.dispatch(
            factories.DeleteEntryFactory.build(
                id=cmd3.id,
                version=1,
                resourceId=cmd3.resource_id,
            ),
        )

        entry_uow_repo_uow = lex_ctx.container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [type-abstract]
        uow = entry_uow_repo_uow.repo.get_by_id(cmd2.entry_repo_id)
        assert uow.was_committed  # type: ignore [attr-defined]

        entry = uow.repo.by_id(cmd3.id)
        previous_version = entry.version

        lex_ctx.command_bus.dispatch(
            factories.DeleteEntryFactory.build(
                id=cmd3.id,
                version=1,
                resourceId=cmd3.resource_id,
            ),
        )

        entry = uow.repo.by_id(cmd3.id)
        assert previous_version == entry.version


class TestAddEntries:
    def test_cannot_add_entries_to_nonexistent_resource(  # noqa: ANN201
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        with pytest.raises(errors.ResourceNotFound):
            lex_ctx.command_bus.dispatch(
                factories.AddEntriesFactory.build(
                    resourceId="non_existent",  # type: ignore [arg-type]
                )
            )

    def test_add_entry(  # noqa: ANN201
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory.build()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory.build(
            entryRepoId=cmd1.id,  # type: ignore [attr-defined]
            config={
                "sort": ["baseform"],
                "fields": {"baseform": {"type": "string", "required": True}},
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)  # type: ignore [arg-type]

        entry_id = "beta"
        cmd3 = factories.AddEntriesFactory.build(
            resourceId=cmd2.resource_id,  # type: ignore [attr-defined]
            entries=[{"baseform": entry_id}],
        )

        lex_ctx.command_bus.dispatch(cmd3)  # type: ignore [arg-type]

        entry_uow_repo_uow = lex_ctx.container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [type-abstract]
        uow = entry_uow_repo_uow.repo.get_by_id(cmd2.entry_repo_id)  # type: ignore [attr-defined]
        # entry = uow.repo.by_id(cmd3.id)
        # assert entry is not None
        # assert entry.repo_id == cmd3.resource_id

        # assert entry.body == {"baseform": entry_id}
        # assert entry.last_modified_by == cmd3.user

        assert uow.was_committed  # type: ignore [attr-defined]


class TestAddEntriesInChunks:
    def test_cannot_add_entries_to_nonexistent_resource(  # noqa: ANN201
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        with pytest.raises(errors.ResourceNotFound):
            lex_ctx.command_bus.dispatch(
                factories.AddEntriesInChunksFactory.build(  # type: ignore [arg-type]
                    resourceId="non_existent",
                )
            )

    def test_add_entry(  # noqa: ANN201
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory.build()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory.build(
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
        cmd3 = factories.AddEntriesInChunksFactory.build(
            resourceId=cmd2.resource_id,  # type: ignore [attr-defined]
            entries=[{"baseform": entry_id}],
        )

        lex_ctx.command_bus.dispatch(cmd3)  # type: ignore [arg-type]

        entry_uow_repo_uow = lex_ctx.container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [type-abstract]
        uow = entry_uow_repo_uow.repo.get_by_id(cmd2.entry_repo_id)  # type: ignore [attr-defined]
        # entry = uow.repo.by_id(entry_id)
        # assert entry is not None
        # assert entry.entry_id == entry_id
        # # assert entry.repo_id == cmd3.resource_id

        # assert entry.body == {"baseform": entry_id}
        # assert entry.last_modified_by == cmd3.user

        assert uow.was_committed  # type: ignore [attr-defined]


class TestImportEntries:
    def test_cannot_import_entries_to_nonexistent_resource(  # noqa: ANN201
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        with pytest.raises(errors.ResourceNotFound):
            lex_ctx.command_bus.dispatch(
                factories.ImportEntriesFactory.build(  # type: ignore [arg-type]
                    resourceId="non_existent",
                )
            )

    def test_import_entries(  # noqa: ANN201
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory.build()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory.build(
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
        cmd3 = factories.ImportEntriesFactory.build(
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

        entry_uow_repo_uow = lex_ctx.container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [type-abstract]
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
        cmd1 = factories.CreateEntryRepositoryFactory.build()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory.build(
            entryRepoId=cmd1.id,  # type: ignore [attr-defined]
            config={
                "sort": ["baseform"],
                "fields": {"baseform": {"type": "string", "required": True}},
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)  # type: ignore [arg-type]

        entry_id = "beta"
        cmd3 = factories.ImportEntriesFactory.build(
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
                factories.ImportEntriesFactory.build(  # type: ignore [arg-type]
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
                factories.ImportEntriesInChunksFactory.build(  # type: ignore [arg-type]
                    resourceId="non_existent",
                )
            )

    def test_import_entries(  # noqa: ANN201
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory.build()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory.build(
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
        cmd3 = factories.ImportEntriesInChunksFactory.build(
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

        entry_uow_repo_uow = lex_ctx.container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [type-abstract]
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
        cmd1 = factories.CreateEntryRepositoryFactory.build()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory.build(
            entryRepoId=cmd1.id,  # type: ignore [attr-defined]
            config={
                "sort": ["baseform"],
                "fields": {"baseform": {"type": "string", "required": True}},
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)  # type: ignore [arg-type]

        entry_id = "beta"
        cmd3 = factories.ImportEntriesInChunksFactory.build(
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
                factories.ImportEntriesInChunksFactory.build(  # type: ignore [arg-type]
                    resourceId=cmd3.resource_id,  # type: ignore [attr-defined]
                    entries=[{"entry": {"baseform": entry_id}}],
                ),
            )
