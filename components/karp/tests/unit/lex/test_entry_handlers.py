from typing import Dict, Optional

import pytest
from karp.foundation.value_objects.unique_id import make_unique_id

from karp.lex.domain import errors

from karp.lex.application import repositories
from karp.lex.application.repositories import (
    ResourceUnitOfWork,
    EntryUowRepositoryUnitOfWork,
)
from karp.lex.domain import commands

from . import adapters, factories

# from karp.domain import errors, events
# from karp.domain.value_objects.unique_id import make_unique_id
# from karp.lex.domain import commands
# from karp.services import unit_of_work

# from karp.tests.unit.adapters import (InMemoryEntryUowFactory, InMemoryResourceUnitOfWork,
#                                       bootstrap_test_app)


class TestAddEntry:
    def test_cannot_add_entry_to_nonexistent_resource(
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        with pytest.raises(errors.ResourceNotFound):
            lex_ctx.command_bus.dispatch(
                factories.AddEntryFactory(  # type: ignore [arg-type]
                    resource_id="non_existent",
                )
            )

    def test_add_entry(
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory(
            entry_repo_id=cmd1.entity_id,
            config={
                "sort": ["baseform"],
                "fields": {"baseform": {"type": "string", "required": True}},
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)  # type: ignore [arg-type]

        entry_id = "beta"
        cmd3 = factories.AddEntryFactory(
            resource_id=cmd2.resource_id,
            entry={"baseform": entry_id},
        )

        lex_ctx.command_bus.dispatch(cmd3)  # type: ignore [arg-type]

        entry_uow_repo_uow = lex_ctx.container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [misc]
        uow = entry_uow_repo_uow.repo.get_by_id(cmd2.entry_repo_id)  # type: ignore [arg-type]
        entry = uow.repo.by_id(cmd3.entity_id)  # type: ignore [arg-type]
        assert entry is not None
        assert entry.id == cmd3.entity_id
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
    def test_create_entry_with_same_entry_id_raises(
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory(
            entry_repo_id=cmd1.entity_id,
            config={
                "sort": ["baseform"],
                "fields": {"baseform": {"type": "string", "required": True}},
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)  # type: ignore [arg-type]

        entry_id = "beta"
        cmd3 = factories.AddEntryFactory(
            resource_id=cmd2.resource_id,
            entry={"baseform": entry_id},
        )

        lex_ctx.command_bus.dispatch(cmd3)  # type: ignore [arg-type]

        with pytest.raises(errors.IntegrityError):
            lex_ctx.command_bus.dispatch(
                factories.AddEntryFactory(  # type: ignore [arg-type]
                    resource_id=cmd3.resource_id,
                    entry={"baseform": entry_id},
                ),
            )


class TestUpdateEntry:
    def test_update_entry(
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory(
            entry_repo_id=cmd1.entity_id,
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
            resource_id=cmd2.resource_id,
            entry={"baseform": entry_id, "a": "orig"},
        )

        lex_ctx.command_bus.dispatch(cmd3)  # type: ignore [arg-type]

        lex_ctx.command_bus.dispatch(
            factories.UpdateEntryFactory(  # type: ignore [arg-type]
                entity_id=cmd3.entity_id,
                # entry_id=entry_id,
                version=1,
                resource_id=cmd3.resource_id,
                entry={"baseform": entry_id, "a": "changed", "b": "added"},
            ),
        )

        entry_uow_repo_uow = lex_ctx.container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [misc]
        uow = entry_uow_repo_uow.repo.get_by_id(cmd2.entry_repo_id)  # type: ignore [arg-type]
        assert uow.was_committed  # type: ignore [attr-defined]

        entry = uow.repo.by_id(cmd3.entity_id)  # type: ignore [arg-type]
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

    def test_cannot_update_entry_in_nonexistent_resource(
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        with pytest.raises(errors.ResourceNotFound):
            lex_ctx.command_bus.dispatch(
                commands.UpdateEntry(
                    entity_id=make_unique_id(),
                    resource_id="non_existent",
                    # entry_id="a",
                    version=3,
                    entry={},
                    user="kristoff@example.com",
                    message="update",
                )
            )

    def test_update_of_entry_id_changes_entry_id(
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory(
            entry_repo_id=cmd1.entity_id,
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
            resource_id=cmd2.resource_id,
            entry={"baseform": entry_id},
        )

        lex_ctx.command_bus.dispatch(cmd3)  # type: ignore [arg-type]

        new_entry_id = "gamma"
        lex_ctx.command_bus.dispatch(
            factories.UpdateEntryFactory(  # type: ignore [arg-type]
                entity_id=cmd3.entity_id,
                # entry_id=entry_id,
                version=1,
                resource_id=cmd3.resource_id,
                entry={"baseform": new_entry_id},
            ),
        )

        entry_uow_repo_uow = lex_ctx.container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [misc]
        uow = entry_uow_repo_uow.repo.get_by_id(cmd2.entry_repo_id)  # type: ignore [arg-type]
        assert uow.was_committed  # type: ignore [attr-defined]

        entry = uow.repo.by_id(cmd3.entity_id)  # type: ignore [arg-type]
        # assert entry.entry_id == new_entry_id
        assert entry.version == 2

        # entry = uow.repo.by_entry_id(new_entry_id)
        # assert entry.id == cmd3.entity_id

        # with pytest.raises(errors.EntryNotFound):
        #     uow.repo.by_entry_id(entry_id)


class TestDeleteEntry:
    def test_can_delete_entry(
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory(
            entry_repo_id=cmd1.entity_id,
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
            resource_id=cmd2.resource_id,
            entry={"baseform": entry_id, "a": "orig"},
        )

        lex_ctx.command_bus.dispatch(cmd3)  # type: ignore [arg-type]

        lex_ctx.command_bus.dispatch(
            commands.DeleteEntry(
                entity_id=cmd3.entity_id,
                # TODO: should we give version to delete entry for sync
                # version=1,
                resource_id=cmd3.resource_id,
                message="deleted",
                user="bob",
            ),
        )

        entry_uow_repo_uow = lex_ctx.container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [misc]
        uow = entry_uow_repo_uow.repo.get_by_id(cmd2.entry_repo_id)  # type: ignore [arg-type]
        assert uow.was_committed  # type: ignore [attr-defined]

        entry = uow.repo.by_id(cmd3.entity_id)  # type: ignore [arg-type]
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
    def test_cannot_add_entries_to_nonexistent_resource(
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        with pytest.raises(errors.ResourceNotFound):
            lex_ctx.command_bus.dispatch(
                factories.AddEntriesFactory(
                    resource_id="non_existent",  # type: ignore [arg-type]
                )
            )

    def test_add_entry(
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory(
            entry_repo_id=cmd1.entity_id,
            config={
                "sort": ["baseform"],
                "fields": {"baseform": {"type": "string", "required": True}},
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)  # type: ignore [arg-type]

        entry_id = "beta"
        cmd3 = factories.AddEntriesFactory(
            resource_id=cmd2.resource_id,
            entries=[{"baseform": entry_id}],
        )

        lex_ctx.command_bus.dispatch(cmd3)  # type: ignore [arg-type]

        entry_uow_repo_uow = lex_ctx.container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [misc]
        uow = entry_uow_repo_uow.repo.get_by_id(cmd2.entry_repo_id)  # type: ignore [arg-type]
        # entry = uow.repo.by_id(cmd3.entity_id)
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
    def test_add_entry_with_same_entry_id_raises(
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory(
            entry_repo_id=cmd1.entity_id,
            config={
                "sort": ["baseform"],
                "fields": {"baseform": {"type": "string", "required": True}},
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)  # type: ignore [arg-type]

        entry_id = "beta"
        cmd3 = factories.AddEntriesFactory(
            resource_id=cmd2.resource_id,
            entries=[{"baseform": entry_id}],
        )

        lex_ctx.command_bus.dispatch(cmd3)  # type: ignore [arg-type]

        with pytest.raises(errors.IntegrityError):
            lex_ctx.command_bus.dispatch(
                factories.AddEntriesFactory(  # type: ignore [arg-type]
                    resource_id=cmd3.resource_id,
                    entries=[{"baseform": entry_id}],
                ),
            )


class TestAddEntriesInChunks:
    def test_cannot_add_entries_to_nonexistent_resource(
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        with pytest.raises(errors.ResourceNotFound):
            lex_ctx.command_bus.dispatch(
                factories.AddEntriesInChunksFactory(  # type: ignore [arg-type]
                    resource_id="non_existent",
                )
            )

    def test_add_entry(
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory(
            entry_repo_id=cmd1.entity_id,
            config={
                "sort": ["baseform"],
                "fields": {"baseform": {"type": "string", "required": True}},
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)  # type: ignore [arg-type]

        entry_id = "beta"
        entity_id = make_unique_id()
        cmd3 = factories.AddEntriesInChunksFactory(
            resource_id=cmd2.resource_id,
            entries=[{"baseform": entry_id}],
        )

        lex_ctx.command_bus.dispatch(cmd3)  # type: ignore [arg-type]

        entry_uow_repo_uow = lex_ctx.container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [misc]
        uow = entry_uow_repo_uow.repo.get_by_id(cmd2.entry_repo_id)  # type: ignore [arg-type]
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
    def test_add_entry_with_same_entry_id_raises(
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory(
            entry_repo_id=cmd1.entity_id,
            config={
                "sort": ["baseform"],
                "fields": {"baseform": {"type": "string", "required": True}},
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)  # type: ignore [arg-type]

        entry_id = "beta"
        cmd3 = factories.AddEntriesInChunksFactory(
            resource_id=cmd2.resource_id,
            entries=[{"baseform": entry_id}],
        )

        lex_ctx.command_bus.dispatch(cmd3)  # type: ignore [arg-type]

        with pytest.raises(errors.IntegrityError):
            lex_ctx.command_bus.dispatch(
                factories.AddEntriesInChunksFactory(  # type: ignore [arg-type]
                    resource_id=cmd3.resource_id,
                    entries=[{"baseform": entry_id}],
                ),
            )


class TestImportEntries:
    def test_cannot_import_entries_to_nonexistent_resource(
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        with pytest.raises(errors.ResourceNotFound):
            lex_ctx.command_bus.dispatch(
                factories.ImportEntriesFactory(  # type: ignore [arg-type]
                    resource_id="non_existent",
                )
            )

    def test_import_entries(
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory(
            entry_repo_id=cmd1.entity_id,
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
            resource_id=cmd2.resource_id,
            entries=[
                {
                    "entity_id": entity_id,
                    "entry": {"baseform": entry_id},
                    "user": "user1",
                }
            ],
        )

        lex_ctx.command_bus.dispatch(cmd3)  # type: ignore [arg-type]

        entry_uow_repo_uow = lex_ctx.container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [misc]
        uow = entry_uow_repo_uow.repo.get_by_id(cmd2.entry_repo_id)  # type: ignore [arg-type]
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
    def test_import_entries_with_same_entry_id_raises(
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory(
            entry_repo_id=cmd1.entity_id,
            config={
                "sort": ["baseform"],
                "fields": {"baseform": {"type": "string", "required": True}},
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)  # type: ignore [arg-type]

        entry_id = "beta"
        cmd3 = factories.ImportEntriesFactory(
            resource_id=cmd2.resource_id,
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
                    resource_id=cmd3.resource_id,
                    entries=[{"entry": {"baseform": entry_id}}],
                ),
            )


class TestImportEntriesInChunks:
    def test_cannot_import_entries_to_nonexistent_resource(
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        with pytest.raises(errors.ResourceNotFound):
            lex_ctx.command_bus.dispatch(  # type: ignore [arg-type]
                factories.ImportEntriesInChunksFactory(  # type: ignore [arg-type]
                    resource_id="non_existent",
                )
            )

    def test_import_entries(
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory(
            entry_repo_id=cmd1.entity_id,
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
            resource_id=cmd2.resource_id,
            entries=[
                {
                    "entity_id": entity_id,
                    "entry": {"baseform": entry_id},
                    "user": "user1",
                }
            ],
        )

        lex_ctx.command_bus.dispatch(cmd3)  # type: ignore [arg-type]

        entry_uow_repo_uow = lex_ctx.container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [misc]
        uow = entry_uow_repo_uow.repo.get_by_id(cmd2.entry_repo_id)  # type: ignore [arg-type]
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
    def test_import_entries_with_same_entry_id_raises(
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd1 = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd1)  # type: ignore [arg-type]

        cmd2 = factories.CreateResourceFactory(
            entry_repo_id=cmd1.entity_id,
            config={
                "sort": ["baseform"],
                "fields": {"baseform": {"type": "string", "required": True}},
                "id": "baseform",
            },
        )
        lex_ctx.command_bus.dispatch(cmd2)  # type: ignore [arg-type]

        entry_id = "beta"
        cmd3 = factories.ImportEntriesInChunksFactory(
            resource_id=cmd2.resource_id,
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
                    resource_id=cmd3.resource_id,
                    entries=[{"entry": {"baseform": entry_id}}],
                ),
            )
