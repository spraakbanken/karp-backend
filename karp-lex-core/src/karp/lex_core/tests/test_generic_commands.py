import pydantic
from karp.lex_core.commands import (
    AddEntry,
    CreateResource,
    GenericAddEntry,
    GenericCreateResource,
    GenericUpdateEntry,
    GenericUpdateResource,
    LexCommand,
    UpdateEntry,
    UpdateResource,
)


class Ex(pydantic.BaseModel):
    baseform: str


class TestAddEntry:
    def test_generic_cmd_exported_is_imported_as_nongeneric(self):  # noqa: ANN201
        cmd = GenericAddEntry[Ex](
            entry={"baseform": "ord"},
            message="add",
            user="user1",
            resourceId="abc",
        )
        cmd_dict = cmd.serialize()

        assert isinstance(LexCommand(command=cmd_dict).command, AddEntry)


class TestUpdateEntry:
    def test_generic_cmd_exported_is_imported_as_nongeneric(self):  # noqa: ANN201
        cmd = GenericUpdateEntry[Ex](
            entityId="01GSAHD0K063FBMFE19BFDM4E9",
            entry={"baseform": "ord"},
            version=3,
            message="add",
            user="user1",
            resourceId="abc",
        )
        cmd_dict = cmd.serialize()

        assert isinstance(LexCommand(command=cmd_dict).command, UpdateEntry)


class ExResource(pydantic.BaseModel):
    fields: dict


class TestCreateResource:
    def test_generic_cmd_exported_is_imported_as_nongeneric(self):  # noqa: ANN201
        cmd = GenericCreateResource[ExResource](
            config={"fields": {"baseform": {"type": "string"}}},
            entryRepoId="01GSAHD0K063FBMFE19BFDM4E9",
            message="add",
            user="user1",
            resourceId="abc",
            name="ABC",
        )
        cmd_dict = cmd.serialize()

        assert isinstance(LexCommand(command=cmd_dict).command, CreateResource)


class TestUpdateResource:
    def test_generic_cmd_exported_is_imported_as_nongeneric(self):  # noqa: ANN201
        cmd = GenericUpdateResource[ExResource](
            entityId="01GSAHD0K063FBMFE19BFDM4E9",
            config={"fields": {"baseform": {"type": "string"}}},
            version=3,
            message="add",
            user="user1",
            name="abc",
        )
        cmd_dict = cmd.serialize()

        assert isinstance(LexCommand(command=cmd_dict).command, UpdateResource)
