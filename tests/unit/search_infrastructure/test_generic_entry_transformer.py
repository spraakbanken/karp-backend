from typing import Any  # noqa: I001

import pytest
from karp.lex_core.value_objects.unique_id import make_unique_id

from karp.lex.application.queries import EntryDto
from karp.search_infrastructure import GenericEntryTransformer

from tests.unit.lex import factories as lex_factories


class TestGenericEntryTransformer:
    @pytest.mark.parametrize(
        "field_name, field_config, field_value",
        [
            ("single", {"type": "boolean"}, True),
        ],
    )
    def test_transform_to_index_entry(  # noqa: ANN201
        self,
        field_name: str,
        field_config: dict,
        field_value: Any,  # noqa: ANN401
        search_unit_ctx,
    ):
        resource_id = "transform_res"
        create_entry_repo = lex_factories.CreateEntryRepositoryFactory()
        search_unit_ctx.command_bus.dispatch(create_entry_repo)
        create_resource = lex_factories.CreateResourceFactory(
            entryRepoId=create_entry_repo.id,
            resourceId=resource_id,
            config={
                "fields": {
                    "id": {"type": "string"},
                    field_name: field_config,
                },
                "id": "id",
            },
        )
        search_unit_ctx.command_bus.dispatch(create_resource)
        transformer = search_unit_ctx.container.get(GenericEntryTransformer)  # type: ignore [misc]
        entry_id = "entry..1"
        src_entry = EntryDto(
            id=make_unique_id(),
            resource=resource_id,
            version=1,
            entry={"id": entry_id, field_name: field_value},
            lastModified=1234567,
            lastModifiedBy="alice@example.com",
        )
        index_entry = transformer.transform(resource_id, src_entry)
        assert index_entry.id == str(src_entry.id)
        assert index_entry.entry["_entry_version"] == 1
        assert index_entry.entry["id"] == entry_id
        assert index_entry.entry[field_name] == field_value

    @pytest.mark.parametrize(
        "field_name, field_config, field_value",
        [
            ("single", {"type": "boolean"}, True),
            ("single", {"type": "string"}, "plain string"),
            ("single", {"type": "number"}, 3.14),
            ("single", {"type": "integer"}, 3),
            ("single", {"type": "long_string"}, "very long string"),
            (
                "single",
                {
                    "type": "object",
                    "fields": {
                        "sub": {"type": "string"},
                    },
                },
                {"sub": "test"},
            ),
        ],
    )
    def test_transform_to_index_entry_collection(  # noqa: ANN201
        self,
        field_name: str,
        field_config: dict,
        field_value: Any,  # noqa: ANN401
        search_unit_ctx,
    ):
        resource_id = "transform_res"
        create_entry_repo = lex_factories.CreateEntryRepositoryFactory()
        search_unit_ctx.command_bus.dispatch(create_entry_repo)
        field_config["collection"] = True
        create_resource = lex_factories.CreateResourceFactory(
            entryRepoId=create_entry_repo.id,
            resourceId=resource_id,
            config={
                "fields": {
                    "id": {"type": "string"},
                    field_name: field_config,
                },
                "id": "id",
            },
        )
        search_unit_ctx.command_bus.dispatch(create_resource)
        transformer = search_unit_ctx.container.get(GenericEntryTransformer)  # type: ignore [misc]
        entry_id = "entry..1"
        src_entry = EntryDto(
            id=make_unique_id(),
            resource=resource_id,
            version=1,
            entry={
                "id": entry_id,
                field_name: [field_value],
            },
            lastModified=1234567,
            lastModifiedBy="alice@example.com",
        )
        index_entry = transformer.transform(resource_id, src_entry)
        assert index_entry.id == str(src_entry.id)
        assert index_entry.entry["_entry_version"] == 1
        assert index_entry.entry["id"] == entry_id
        assert index_entry.entry[field_name][0] == field_value

    @pytest.mark.parametrize(
        "field_name, field_config, field_value",
        [
            ("single", {"type": "boolean"}, True),
            ("single", {"type": "string"}, "plain string"),
            ("single", {"type": "number"}, 3.14),
            ("single", {"type": "integer"}, 3),
            ("single", {"type": "long_string"}, "very long string"),
            (
                "single",
                {"type": "object", "fields": {"sub": {"type": "string"}}},
                {"sub": "test"},
            ),
        ],
    )
    def test_transform_to_index_entry_object(  # noqa: ANN201
        self,
        field_name: str,
        field_config: dict,
        field_value: Any,  # noqa: ANN401
        search_unit_ctx,
    ):
        resource_id = "transform_res"
        create_entry_repo = lex_factories.CreateEntryRepositoryFactory()
        search_unit_ctx.command_bus.dispatch(create_entry_repo)
        create_resource = lex_factories.CreateResourceFactory(
            entryRepoId=create_entry_repo.id,
            resourceId=resource_id,
            config={
                "fields": {
                    "id": {"type": "string"},
                    "obj": {
                        "type": "object",
                        "fields": {
                            field_name: field_config,
                        },
                    },
                },
                "id": "id",
            },
        )
        search_unit_ctx.command_bus.dispatch(create_resource)
        transformer = search_unit_ctx.container.get(GenericEntryTransformer)  # type: ignore [misc]
        entry_id = "entry..1"
        src_entry = EntryDto(
            id=make_unique_id(),
            resource=resource_id,
            version=1,
            entry={
                "id": entry_id,
                "obj": {
                    field_name: field_value,
                },
            },
            lastModified=1234567,
            lastModifiedBy="alice@example.com",
        )
        index_entry = transformer.transform(resource_id, src_entry)
        assert index_entry.id == str(src_entry.id)
        assert index_entry.entry["_entry_version"] == 1
        assert index_entry.entry["id"] == entry_id
        assert index_entry.entry["obj"][field_name] == field_value
